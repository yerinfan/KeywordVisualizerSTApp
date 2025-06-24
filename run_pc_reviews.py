# metacritic_reviews_crawler_resume.py

import os
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, InvalidArgumentException

# ------------------------------------------------------------------
# (1) 이 변수를 마지막 정상 완료된 인덱스 + 1 로 바꿔서 실행하면
#     그 번호부터 자동으로 이어서 크롤링하게 됩니다.
#     예: 만약 125번 게임까지 정상적으로 크롤링했다면 resume_from=126
# ------------------------------------------------------------------
resume_from = 1  # 기본값: 1번부터 시작
# ------------------------------------------------------------------

def create_driver(driver_path: str = "./chromedriver.exe") -> webdriver.Chrome:
    """
    ChromeDriver를 헤드리스 모드로 실행하도록 설정합니다.
    (ChromeDriver 111 이상 버전에서 헤드리스 작동이 원활하도록 몇 가지 플래그를 추가)
    """
    options = webdriver.ChromeOptions()

    # 반드시 '--headless=new' 혹은 '--headless'를 사용하도록 권장합니다.
    # (ChromeDriver 버전에 따라 '--headless=new'가 필요할 수도 있습니다.)
    #options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=en-US")
    # Chrome v111 이후 remote-allow-origins 옵션이 필요할 수 있음
    options.add_argument("--remote-allow-origins=*")

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
    슬러그를 추출하여 PC 리뷰 URL로 반환합니다:

      game_url = "https://www.metacritic.com/game/elden-ring/"
      → "https://www.metacritic.com/game/elden-ring/user-reviews/?platform=pc"
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

    # 페이지 로드 완료까지 잠깐 대기
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
        # 리뷰 하나도 없으면 빈 DataFrame 반환
        return pd.DataFrame(columns=["game", "review", "score"])

    return pd.DataFrame({
        "game":   [game_title] * len(reviews),
        "review": reviews,
        "score":  scores
    })


if __name__ == "__main__":
    # 1) all_pc_game_titles.csv 로드 (['title','url'] 형식이어야 함)
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
    # resume_from 값이 총 게임 수보다 클 경우 조정
    if resume_from < 1:
        resume_from = 1
    if resume_from > total_games:
        resume_from = total_games

    print(f"▶ 전체 게임 개수: {total_games}")
    print(f"▶ {resume_from}번 인덱스부터 시작합니다.\n")

    for idx, row in df_titles.iterrows():
        game_idx = idx + 1  # 사람 눈에 편한 1-based 인덱스

        # resume_from 이전 번호는 건너뜀
        if game_idx < resume_from:
            continue

        game_title = row["title"]
        game_url   = row["url"]

        # (1) 리뷰 페이지 URL 생성
        review_url = derive_review_url(game_url)
        if not review_url:
            print(f"[{game_idx}/{total_games}] \"{game_title}\" → ❌ 리뷰 URL 생성 실패 (game_url: {game_url})")
            continue

        # (2) 파일명 안전하게 변환 (특수문자 제거, 공백→언더바)
        safe_name = "".join(c for c in game_title if c.isalnum() or c.isspace()).rstrip().replace(" ", "_")
        output_path = os.path.join(output_dir, f"{safe_name}_pc_reviews.csv")

        # 이미 파일이 존재하면 스킵
        if os.path.exists(output_path):
            print(f"[{game_idx}/{total_games}] \"{game_title}\" → 이미 크롤링됨, 스킵 ({output_path})")
            continue

        print(f"[{game_idx}/{total_games}] \"{game_title}\" 리뷰 크롤링 → {review_url}")
        df_reviews = crawl_game_reviews(game_title, review_url, driver_path="./chromedriver.exe")

        if df_reviews.empty:
            print(f"  ⚠️ 리뷰 없음 or 크롤링 실패: {game_title}")
        else:
            df_reviews.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"  ✅ 저장 완료: {output_path}")

        # 다음 게임으로 넘어가기 전에 짧은 랜덤 대기
        time.sleep(random.uniform(1.0, 2.0))

    print("\n▶ 모든 게임 리뷰 크롤링 완료.")
