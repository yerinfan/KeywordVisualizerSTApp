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
    Selenium 을 써서 한 URL에서 무한 스크롤을 끝까지 내려가며
    로드된 모든 유저 리뷰를 수집한 뒤 DataFrame 으로 반환합니다.
    """
    # 1) ChromeOptions 설정
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")                # 필요 시 주석 처리
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
        # 스크롤하여 페이지 맨 아래로 이동
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # AJAX 로딩 대기
        time.sleep(random.uniform(*delay_range))
        # 새로 로드된 후 문서 높이 확인
        new_height = driver.execute_script("return document.body.scrollHeight")
        # 높이가 변화 없으면 모두 로드된 것으로 간주하고 종료
        if new_height == last_height:
            break
        last_height = new_height

    # 5) 리뷰 요소 수집
    elems = driver.find_elements(By.CLASS_NAME, "c-siteReview_quote")
    reviews = [e.text.strip() for e in elems if e.text.strip()]

    driver.quit()
    return pd.DataFrame(reviews, columns=["review"])
