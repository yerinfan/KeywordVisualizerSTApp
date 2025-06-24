# mylib/metacritic_title_crawler.py

import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

def create_driver(driver_path: str) -> webdriver.Chrome:
    """
    ChromeDriver를 헤드리스 모드(백그라운드)로 실행하도록 설정합니다.
    """
    options = webdriver.ChromeOptions()
    # 헤드리스 모드로 실행 (로컬 디버깅 시는 주석 처리 가능)
    #options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=en-US")

    # 임의 User-Agent
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_argument(f"user-agent={ua}")

    # 봇 탐지 회피 옵션
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver


def crawl_game_titles(
    base_url_template: str,
    start_page: int = 1,
    end_page: int = 36,
    driver_path: str = "./chromedriver.exe",
    delay_range: tuple = (1.0, 2.0)
) -> (pd.DataFrame, dict):
    """
    Selenium을 이용해 Metacritic Browse 페이지의
    start_page부터 end_page까지 순회하며 모든 게임 제목과 상세 URL을 수집합니다.

    - base_url_template: 
      ex) "https://www.metacritic.com/browse/game/ps5/all/all-time/"
          "metascore?releaseYearMin=1958&releaseYearMax=2025&platform=ps5&page={}"
      { } 자리에 페이지 번호를 넣어서 호출합니다.

    - start_page: 포함할 시작 페이지 번호 (예: 1)
    - end_page:   포함할 마지막 페이지 번호 (예: 36)
    - driver_path: 크롬드라이버 실행 파일 경로
    - delay_range: 페이지 로드 후 대기할 랜덤 딜레이 범위 (단위: 초)

    반환값:
      - DataFrame(columns=["title", "url"])
      - per_page_counts: {페이지번호: 해당 페이지에서 수집된 제목 개수, …}
    """
    driver = create_driver(driver_path)
    titles = []
    urls = []
    per_page_counts = {}

    for page_num in range(start_page, end_page + 1):
        url = base_url_template.format(page_num)
        driver.get(url)

        # (선택) 쿠키 동의 팝업 등이 뜨면 클릭하여 닫기
        try:
            btn = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            btn.click()
            time.sleep(0.3)
        except:
            pass

        # 페이지 로드 후 랜덤 딜레이
        time.sleep(random.uniform(*delay_range))

        # ——————————————————————————————————————————————————————————————————
        # 1) PS5/구 레이아웃 (테이블형) 시도: <td class="clamp-summary-wrap"> …
        # ——————————————————————————————————————————————————————————————————
        game_cells = driver.find_elements(By.CSS_SELECTOR, "td.clamp-summary-wrap")
        count_this_page = 0

        if game_cells:
            # PS5/구 레이아웃에서 제목 + URL 추출
            for cell in game_cells:
                try:
                    a_tag = cell.find_element(By.CSS_SELECTOR, "a.title")
                    title_text = a_tag.find_element(By.CSS_SELECTOR, "h3").text.strip()
                    href = a_tag.get_attribute("href").strip()
                except:
                    continue

                titles.append(title_text)
                urls.append(href)
                count_this_page += 1

        else:
            # ——————————————————————————————————————————————————————————————————
            # 2) PC/신 레이아웃 (카드형) 시도: 
            #    <div class="c-productListings"> → 여러 개의 <div> 카드 블록
            #    각 카드 블록 내부에 <div class="c-finderProductCard_info"> 가 있고,
            #    제목은 그 안의 h3 > span:nth-child(2)에 들어 있습니다.
            # ——————————————————————————————————————————————————————————————————
            # 2-1) 모든 'info' 블록을 찾는다
            info_blocks = driver.find_elements(By.CSS_SELECTOR, "div.c-finderProductCard_info")

            for info in info_blocks:
                try:
                    # 제목: info 안에서 "div.c-finderProductCard_title > h3 > span:nth-child(2)"
                    title_span = info.find_element(
                        By.CSS_SELECTOR,
                        "div.c-finderProductCard_title > h3 > span:nth-child(2)"
                    )
                    title_text = title_span.text.strip()
                    # URL: info 의 부모(parent::a) 태그의 href
                    a_tag = info.find_element(By.XPATH, "./parent::a")
                    href = a_tag.get_attribute("href").strip()
                except:
                    continue

                titles.append(title_text)
                urls.append(href)
                count_this_page += 1

        # 페이지별 수집 개수 기록
        per_page_counts[page_num] = count_this_page

    driver.quit()

    df = pd.DataFrame({
        "title": titles,
        "url":   urls
    })
    return df, per_page_counts
