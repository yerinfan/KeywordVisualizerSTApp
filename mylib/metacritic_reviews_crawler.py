# -------------------------------
# metacritic_reviews_crawler.py
# (오직 derive_review_url 함수만 변경된 버전)
# -------------------------------

import os
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, InvalidArgumentException

def create_driver(driver_path: str = "./chromedriver.exe") -> webdriver.Chrome:
    """
    ChromeDriver를 헤드리스 모드로 실행하도록 설정합니다.
    """
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=en-US")

    # 흔히 쓰이는 User-Agent (크롤링 차단 최소화)
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument(f"user-agent={ua}")

    # 봇 탐지 회피 옵션
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(driver_path)
    driver  = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver

def derive_review_url(game_url: str) -> str:
    """
    Metacritic 게임 상세 URL(예: https://www.metacritic.com/game/elden-ring/)에서
    슬러그를 추출하여 PS5 리뷰 URL로 반환합니다:

      올바른 예:
        game_url = "https://www.metacritic.com/game/elden-ring/"
        → "https://www.metacritic.com/game/elden-ring/user-reviews/?platform=playstation-5"
    """
    if not isinstance(game_url, str) or not game_url.startswith("http"):
        return ""

    stripped = game_url.rstrip("/")  # 맨 끝에 붙은 "/" 제거
    parts = stripped.split("/")      
    # 예: ["https:", "", "www.metacritic.com", "game", "elden-ring"]

    # (A) "/game/<slug>" 구조
    if len(parts) >= 5 and parts[3] == "game":
        game_slug = parts[4]
    else:
        return ""

    # 올바른 리뷰 URL은 아래와 같은 구조입니다.
    return f"https://www.metacritic.com/game/{game_slug}/user-reviews/?platform=pc"


def crawl_game_reviews(game_title: str, review_url: str, driver_path: str = "./chromedriver.exe") -> pd.DataFrame:
    """
    주어진 리뷰 페이지(review_url)에서 모든 유저 리뷰와 평점을 수집하여 DataFrame 반환.
    컬럼: ["game", "review", "score"]
    """
    driver = create_driver(driver_path)

    try:
        driver.get(review_url)
    except InvalidArgumentException:
        driver.quit()
        return pd.DataFrame(columns=["game", "review", "score"])

    time.sleep(random.uniform(1.5, 3.0))

    # 끝까지 스크롤하여 모든 리뷰 로드
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.5, 3.0))
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
        except NoSuchElementException:
            text = ""
        try:
            score = item.find_element(
                By.CSS_SELECTOR,
                "div.c-siteReviewHeader_reviewScore span"
            ).text.strip()
        except NoSuchElementException:
            score = ""
        if text:
            reviews.append(text)
            scores.append(score)

    driver.quit()
    if not reviews:
        return pd.DataFrame(columns=["game", "review", "score"])

    return pd.DataFrame({
        "game":   [game_title] * len(reviews),
        "review": reviews,
        "score":  scores
    })


if __name__ == "__main__":
    # 1) all_ps5_game_titles.csv 로드 (['title','url'] 형식이어야 함)
    titles_csv = "all_pc_game_titles.csv"
    if not os.path.exists(titles_csv):
        print(f"❌ 파일을 찾을 수 없습니다: {titles_csv}")
        exit(1)

    df_titles = pd.read_csv(titles_csv)
    # df_titles.columns → ['title','url']

    # 2) 리뷰 저장 폴더 준비
    output_dir = "reviews"
    os.makedirs(output_dir, exist_ok=True)

    total_games = len(df_titles)
    for idx, row in df_titles.iterrows():
        game_title = row["title"]
        game_url   = row["url"]

        # (1) 리뷰 페이지 URL 생성 (슬러그만 뽑아서 platform=playstation-5 추가)
        review_url = derive_review_url(game_url)
        if not review_url:
            print(f"[{idx+1}/{total_games}] \"{game_title}\" → 리뷰 URL 생성 실패 (game_url: {game_url})")
            continue

        # (2) 파일명 안전하게 변환 (특수문자 제거, 공백→언더바)
        safe_name = "".join(c for c in game_title if c.isalnum() or c.isspace()).rstrip().replace(" ", "_")
        output_path = os.path.join(output_dir, f"{safe_name}_pc_reviews.csv")

        print(f"[{idx+1}/{total_games}] \"{game_title}\" 리뷰 크롤링 → {review_url}")
        df_reviews = crawl_game_reviews(game_title, review_url, driver_path="./chromedriver.exe")

        if df_reviews.empty:
            print(f"  ⚠️ 리뷰가 없거나 크롤링 실패: {game_title}")
        else:
            df_reviews.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"  ✅ 저장 완료: {output_path}")

        # 다음 게임으로 넘어가기 전에 짧은 랜덤 대기
        time.sleep(random.uniform(1.0, 2.0))

    print("\n모든 게임 리뷰 크롤링 완료.")


