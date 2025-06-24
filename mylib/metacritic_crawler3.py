# mylib/metacritic_crawler.py

import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

def crawl_game_reviews(
    game_url: str,
    driver_path: str = "./chromedriver.exe",
    delay_range: tuple = (2.0, 4.0)
) -> pd.DataFrame:
    """
    Selenium을 이용해 한 URL에서 모든 유저 리뷰와 평점(유저 스코어)을 
    수집한 뒤 DataFrame으로 반환합니다.
    """
    # 1) ChromeOptions 설정
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 필요 시 주석 해제
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=en-US")
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument(f"user-agent={ua}")
    # 봇 탐지 회피 옵션
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # 2) 드라이버 기동
    service = Service(driver_path)
    driver  = webdriver.Chrome(service=service, options=options)

    # 3) 페이지 열기
    driver.get(game_url)
    time.sleep(random.uniform(*delay_range))

    # 4) 무한 스크롤: 페이지 끝까지 내려가며 새로운 리뷰 로드
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(*delay_range))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # 5) 리뷰 블록 수집
    reviews = []
    scores  = []
    # 각 리뷰 아이템 컨테이너
    items = driver.find_elements(By.CSS_SELECTOR, "div.c-siteReview_main")
    for item in items:
        # 리뷰 텍스트
        try:
            text = item.find_element(By.CSS_SELECTOR, ".c-siteReview_quote").text.strip()
        except:
            text = ""
        # 유저 평점 (CSS 경로에 맞춰 간단화)
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

    # 6) DataFrame으로 변환
    df = pd.DataFrame({
        "review": reviews,
        "score":  scores
    })
    return df

if __name__ == "__main__":
    url = "https://www.metacritic.com/game/elden-ring/user-reviews/?platform=playstation-5"
    df_reviews = crawl_game_reviews(url)
    # CSV로 저장
    df_reviews.to_csv("elden_ring_user_reviews.csv", index=False, encoding="utf-8-sig")
    print("Saved to elden_ring_user_reviews.csv")
