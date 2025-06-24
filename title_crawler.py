# 파일명: streamlit_crawler.py

import streamlit as st
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

def create_driver(driver_path: str = "./chromedriver.exe") -> webdriver.Chrome:
    """ChromeDriver를 설정하여 반환합니다."""
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 필요 시 해제
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=en-US")
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_argument(f"user-agent={ua}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service(driver_path)
    return webdriver.Chrome(service=service, options=options)

def crawl_game_list(
    base_url_template: str,
    start_page: int,
    end_page: int,
    driver_path: str = "./chromedriver.exe",
    delay_range: tuple = (2.0, 4.0),
    progress_bar=None,
    status_text=None
) -> pd.DataFrame:
    """
    Metacritic PS5 Browse 페이지를 start_page부터 end_page까지 순회하며
    각 게임의 제목과 URL을 수집하여 DataFrame으로 반환합니다.
    """
    driver = create_driver(driver_path)
    game_titles = []
    game_urls   = []
    total_pages = end_page - start_page + 1

    for idx, page in enumerate(range(start_page, end_page + 1)):
        if status_text:
            status_text.text(f"게임 목록 페이지 {page} 크롤링 중... ({idx+1}/{total_pages})")
        url = base_url_template.format(page)
        driver.get(url)
        time.sleep(random.uniform(*delay_range))

        # 무한 스크롤 (필요 시)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(*delay_range))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # div.clamp-summary-wrap > a.title > h3 구조에서 제목과 URL 추출
        game_blocks = driver.find_elements(By.CSS_SELECTOR, "div.clamp-summary-wrap")
        for block in game_blocks:
            try:
                a_tag = block.find_element(By.CSS_SELECTOR, "a.title")
                title = a_tag.find_element(By.CSS_SELECTOR, "h3").text.strip()
                href  = a_tag.get_attribute("href").strip()
            except:
                continue
            if title and href:
                game_titles.append(title)
                game_urls.append(href)

        # 진행률 업데이트
        if progress_bar:
            progress_bar.progress((idx + 1) / total_pages)

    driver.quit()
    if status_text:
        status_text.text("✅ 게임 목록 수집 완료!")
    df_games = pd.DataFrame({
        "title": game_titles,
        "url":   game_urls
    })
    return df_games

def crawl_game_reviews(
    game_title: str,
    reviews_url: str,
    driver_path: str = "./chromedriver.exe",
    delay_range: tuple = (2.0, 4.0),
    progress_bar=None,
    status_text=None,
    idx: int = 0,
    total: int = 1
) -> pd.DataFrame:
    """
    한 게임의 User Reviews 페이지에서 리뷰와 평점을 수집하여 DataFrame으로 반환합니다.
    """
    if status_text:
        status_text.text(f"[{idx+1}/{total}] \"{game_title}\" 리뷰 크롤링 중...")
    driver = create_driver(driver_path)
    driver.get(reviews_url)
    time.sleep(random.uniform(*delay_range))

    # 무한 스크롤: 모든 리뷰 로드
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(*delay_range))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    reviews = []
    scores  = []
    items = driver.find_elements(By.CSS_SELECTOR, "div.c-siteReview_main")
    for item in items:
        try:
            text = item.find_element(By.CSS_SELECTOR, ".c-siteReview_quote").text.strip()
        except:
            text = ""
        try:
            score = item.find_element(
                By.CSS_SELECTOR,
                "div.c-siteReviewHeader_reviewScore span"
            ).text.strip()
        except:
            score = ""
        if text:
            reviews.append(text)
            scores.append(score)

    driver.quit()
    if progress_bar:
        progress_bar.progress((idx + 1) / total)
    return pd.DataFrame({
        "game":   [game_title] * len(reviews),
        "review": reviews,
        "score":  scores
    })

# ─────────────────────────────────────────────────────────────────────────────
# Streamlit UI
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Metacritic PS5 크롤러", layout="wide")
st.title("🎮 Metacritic PS5 게임 크롤러 (페이지 0 제외)")

st.markdown(
    """
    **기능**  
    1. PS5 Browse 페이지 중 `?page=1`부터 `?page=35`까지만 순회하여 모든 게임의 제목과 URL을 수집합니다.  
    2. 수집된 각 게임의 User Reviews 페이지를 순회하며 리뷰 텍스트와 평점을 수집합니다.  
    3. 진행 상황을 실시간으로 표시하고, 완료 시 결과 CSV 파일을 다운로드할 수 있습니다.
    """
)

driver_path = st.text_input(
    "ChromeDriver 경로", "./chromedriver.exe",
    help="예: ./chromedriver.exe"
)

if st.button("크롤링 시작"):
    # 1) 게임 목록 크롤링 (page=1~35)
    base_url = (
        "https://www.metacritic.com/browse/game/ps5/all/all-time/"
        "metascore?releaseYearMin=1958&releaseYearMax=2025&platform=ps5&page={}"
    )
    start_page = 1
    end_page   = 35

    st.subheader("1️⃣ 게임 목록 크롤링 (page 1~35)")
    list_status = st.empty()
    list_progress = st.progress(0.0)

    df_games = crawl_game_list(
        base_url_template=base_url,
        start_page=start_page,
        end_page=end_page,
        driver_path=driver_path,
        progress_bar=list_progress,
        status_text=list_status
    )

    st.markdown(f"- 총 수집된 게임 수: **{len(df_games)}**")
    st.dataframe(df_games.head(10))

    # 2) 유저 리뷰 크롤링
    st.subheader("2️⃣ 유저 리뷰 크롤링")
    review_status = st.empty()
    review_progress = st.progress(0.0)

    all_review_dfs = []
    total_games = len(df_games)

    for idx, row in df_games.iterrows():
        game_title = row["title"]
        game_url   = row["url"]
        platform   = game_url.rstrip("/").split("/")[-1]
        reviews_url = f"{game_url}/user-reviews?platform={platform}"

        try:
            df_rev = crawl_game_reviews(
                game_title=game_title,
                reviews_url=reviews_url,
                driver_path=driver_path,
                progress_bar=review_progress,
                status_text=review_status,
                idx=idx,
                total=total_games
            )
            all_review_dfs.append(df_rev)
        except Exception as e:
            review_status.text(f"⚠️ 오류 발생 ({game_title}): {e}")

        time.sleep(random.uniform(1.0, 2.5))

    if all_review_dfs:
        df_all_reviews = pd.concat(all_review_dfs, ignore_index=True)
    else:
        df_all_reviews = pd.DataFrame(columns=["game", "review", "score"])

    review_status.text("✅ 유저 리뷰 수집 완료!")

    # 3) 결과 파일 저장 및 다운로드 버튼
    st.subheader("✅ 크롤링 완료: 결과 파일 다운로드")
    df_games.to_csv("games.csv", index=False, encoding="utf-8-sig")
    df_all_reviews.to_csv("game_reviews.csv", index=False, encoding="utf-8-sig")

    st.download_button(
        label="게임 목록 (games.csv) 다운로드",
        data=open("games.csv", "rb"),
        file_name="games.csv",
        mime="text/csv"
    )
    st.download_button(
        label="유저 리뷰 (game_reviews.csv) 다운로드",
        data=open("game_reviews.csv", "rb"),
        file_name="game_reviews.csv",
        mime="text/csv"
    )

    st.success("모든 작업이 완료되었습니다! 파일을 다운로드해주세요.")
