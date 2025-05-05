from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os
import time

# ======== 설정 ========
KEYWORDS = ["정보보안", "보안"]
REGIONS = ["서울", "경기"]
EXPERIENCE_KEYWORDS = ["신입", "인턴"]

FROM_EMAIL = "your_email@gmail.com"
TO_EMAIL = "receiver_email@gmail.com"
APP_PASSWORD = "your_app_password"

PREV_JOBS_FILE = "jobs.json"

# ======== 유틸 ========
def load_previous_jobs():
    if os.path.exists(PREV_JOBS_FILE):
        with open(PREV_JOBS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_current_jobs(job_urls):
    with open(PREV_JOBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(job_urls), f, ensure_ascii=False, indent=2)

# ======== 크롤링 (Selenium 기반) ========
def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(ChromeDriverManager().install(), options=options)

def crawl_saramin():
    driver = setup_driver()
    url = "https://www.saramin.co.kr/zf_user/search?searchword=정보보안&loc_mcd=101000&exp_cd=1"
    driver.get(url)
    time.sleep(3)
    results = []
    try:
        items = driver.find_elements(By.CSS_SELECTOR, ".item_recruit")
        for item in items:
            try:
                title_tag = item.find_element(By.CSS_SELECTOR, ".job_tit a")
                title = title_tag.text.strip()
                link = title_tag.get_attribute("href")
                company = item.find_element(By.CSS_SELECTOR, ".corp_name").text.strip()
                location = item.find_element(By.CSS_SELECTOR, ".job_condition span:nth-child(2)").text.strip()

                if any(k in title for k in KEYWORDS) and any(r in location for r in REGIONS):
                    results.append({"title": title, "company": company, "location": location, "link": link})
            except:
                continue
    finally:
        driver.quit()
    return results

def crawl_jobkorea():
    driver = setup_driver()
    url = "https://www.jobkorea.co.kr/Search/?stext=정보보안&careerType=1&local=I000"
    driver.get(url)
    time.sleep(3)
    results = []
    try:
        items = driver.find_elements(By.CSS_SELECTOR, 'div.list-default > ul > li')
        for item in items:
            try:
                title_tag = item.find_element(By.CSS_SELECTOR, ".title a.name")
                title = title_tag.text.strip()
                link = title_tag.get_attribute("href")
                company_tag = item.find_element(By.CSS_SELECTOR, ".corp .name")
                company = company_tag.text.strip()
                location_tag = item.find_element(By.CSS_SELECTOR, ".loc.long")
                location = location_tag.text.strip()

                if any(k in title for k in KEYWORDS) and any(r in location for r in REGIONS):
                    results.append({"title": title, "company": company, "location": location, "link": link})
            except:
                continue
    finally:
        driver.quit()
    return results

def crawl_wanted():
    driver = setup_driver()
    url = "https://www.wanted.co.kr/search?query=정보보안"
    driver.get(url)
    time.sleep(5)
    results = []
    try:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        for item in soup.select(".JobCard_container__FqChn"):
            try:
                title_tag = item.select_one("h2")
                title = title_tag.text.strip() if title_tag else ""
                link_tag = item.select_one("a")
                link = "https://www.wanted.co.kr" + link_tag['href'] if link_tag else ""
                company_tag = item.select_one(".JobCard_companyName__vZMqJ")
                company = company_tag.text.strip() if company_tag else ""
                location_tag = item.select_one(".JobCard_location__2EOr5")
                location = location_tag.text.strip() if location_tag else ""

                if any(k in title for k in KEYWORDS):
                    results.append({"title": title, "company": company, "location": location, "link": link})
            except:
                continue
    finally:
        driver.quit()
    return results

# ======== 이메일 전송 ========
def send_email(new_jobs):
    body = "\n\n".join([f"[{job['title']}]\n{job['company']} - {job['location']}\n{job['link']}" for job in new_jobs])
    msg = MIMEText(body)
    msg['Subject'] = f"[보안 채용 알림] {len(new_jobs)}건의 새로운 공고 ({datetime.now().strftime('%Y-%m-%d')})"
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(FROM_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

# ======== 메인 실행 ========
if __name__ == "__main__":
    try:
        previous_links = load_previous_jobs()
        all_jobs = crawl_saramin() + crawl_jobkorea() + crawl_wanted()
        new_jobs = [job for job in all_jobs if job['link'] not in previous_links]

        if new_jobs:
            send_email(new_jobs)
            save_current_jobs(set(job['link'] for job in all_jobs))
        else:
            print("새로운 공고가 없습니다.")
    except Exception as e:
        print(f"[Fatal Error] {e}")
        error_msg = MIMEText(f"크롤링 중 오류 발생: {e}")
        error_msg['Subject'] = f"[에러] 채용 크롤링 실패 ({datetime.now().strftime('%Y-%m-%d')})"
        error_msg['From'] = FROM_EMAIL
        error_msg['To'] = TO_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(FROM_EMAIL, APP_PASSWORD)
            smtp.send_message(error_msg)
