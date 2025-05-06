from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
import json
import os

FROM_EMAIL = os.environ["FROM_EMAIL"]
TO_EMAIL = os.environ["TO_EMAIL"]
APP_PASSWORD = os.environ["APP_PASSWORD"]

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def crawl_saramin():
    print("🟢 Saramin 크롤링 시작")
    jobs = []
    driver = setup_driver()
    try:
        driver.get("https://www.saramin.co.kr/zf_user/jobs/list/job-category")
        # 최신 구조에 맞는 선택자 (2024.06 기준)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.area_job > h2.job_tit > a"))
        )
        elements = driver.find_elements(By.CSS_SELECTOR, "div.area_job > h2.job_tit > a")
        for e in elements[:5]:
            title = e.get_attribute("title").strip()
            link = e.get_attribute("href")
            jobs.append({"title": title, "link": link})
        print(f"🟢 Saramin {len(jobs)}개 수집")
    except Exception as e:
        print(f"❌ Saramin 크롤링 실패: {e}")
        driver.save_screenshot("saramin_error.png")
        print("🖼️ Saramin 에러 화면 캡처 (saramin_error.png)")
    finally:
        driver.quit()
    return jobs

def crawl_jobkorea():
    print("🟢 JobKorea 크롤링 시작")
    jobs = []
    driver = setup_driver()
    try:
        driver.get("https://www.jobkorea.co.kr/recruit/joblist")
        # 최신 구조에 맞는 선택자 (2024.06 기준)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.list-default > ul.clear > li > div.post-list-info > a.title"))
        )
        elements = driver.find_elements(By.CSS_SELECTOR, "div.list-default > ul.clear > li > div.post-list-info > a.title")
        for e in elements[:5]:
            title = e.text.strip()
            link = e.get_attribute("href")
            jobs.append({"title": title, "link": link})
        print(f"🟢 JobKorea {len(jobs)}개 수집")
    except Exception as e:
        print(f"❌ JobKorea 크롤링 실패: {e}")
        driver.save_screenshot("jobkorea_error.png")
        print("🖼️ JobKorea 에러 화면 캡처 (jobkorea_error.png)")
    finally:
        driver.quit()
    return jobs

def crawl_wanted():
    print("🟢 Wanted 크롤링 시작")
    jobs = []
    driver = setup_driver()
    try:
        driver.get("https://www.wanted.co.kr/jobsfeed")
        # 동적 로딩이므로, job-card로 시작하는 div를 기다림 (2024.06 기준)
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.JobCard_container__z4_3g a"))
        )
        elements = driver.find_elements(By.CSS_SELECTOR, "div.JobCard_container__z4_3g a")
        count = 0
        for e in elements:
            link = e.get_attribute("href")
            if link and "/wd/" in link:
                title = e.text.strip()
                jobs.append({"title": title, "link": link})
                count += 1
                if count >= 5:
                    break
        print(f"🟢 Wanted {len(jobs)}개 수집")
    except Exception as e:
        print(f"❌ Wanted 크롤링 실패: {e}")
        driver.save_screenshot("wanted_error.png")
        print("🖼️ Wanted 에러 화면 캡처 (wanted_error.png)")
    finally:
        driver.quit()
    return jobs

def load_previous_jobs():
    if not os.path.exists("jobs.json"):
        return []
    with open("jobs.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_jobs(jobs):
    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(FROM_EMAIL, APP_PASSWORD)
            server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        print("✅ 이메일 전송 완료")
    except Exception as e:
        print(f"❌ 이메일 전송 실패: {e}")

def main():
    saramin_jobs = crawl_saramin()
    jobkorea_jobs = crawl_jobkorea()
    wanted_jobs = crawl_wanted()
    all_jobs = saramin_jobs + jobkorea_jobs + wanted_jobs

    previous_links = set()
    previous_jobs = load_previous_jobs()
    for job in previous_jobs:
        previous_links.add(job["link"])

    new_jobs = [job for job in all_jobs if job["link"] not in previous_links]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if new_jobs:
        subject = f"[{now}] 새로운 공고 {len(new_jobs)}건 발견!"
        body = "\n\n".join([f"📌 {job['title']}\n{job['link']}" for job in new_jobs])
        save_jobs(all_jobs)
    else:
        subject = f"[{now}] 새로운 공고 없음"
        body = "새로운 채용 공고가 없습니다."

    send_email(subject, body)

if __name__ == "__main__":
    main()
