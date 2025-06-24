# metacritic_crawler.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import pandas as pd

def crawl_game_reviews(game_url, driver_path="./chromedriver.exe", num_pages=3):
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--lang=en-US')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    #options.add_argument('--headless')  # 필요 시 사용

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(game_url)
    time.sleep(5)

    for _ in range(num_pages):
        try:
            more_button = driver.find_element(By.CLASS_NAME, "load_more")
            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(2)
        except:
            break

    review_elements = driver.find_elements(By.CLASS_NAME, "c-siteReview_quote")
    reviews = [review.text.strip() for review in review_elements if review.text.strip()]
    driver.quit()

    df = pd.DataFrame(reviews, columns=["review"])
    return df
