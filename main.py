from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
    driver = setup_driver()
    driver.get("https://www.saramin.co.kr/zf_user/jobs/list/job-category")
    jobs = ["사람인 예시 공고 1", "사람인 예시 공고 2"]
    driver.quit()
    return jobs

def crawl_jobkorea():
    driver = setup_driver()
    driver.get("https://www.jobkorea.co.kr/recruit/joblist")
    jobs = ["잡코리아 예시 공고 1", "잡코리아 예시 공고 2"]
    driver.quit()
    return jobs

def crawl_wanted():
    driver = setup_driver()
    driver.get("https://www.wanted.co.kr/jobsfeed")
    jobs = ["원티드 예시 공고 1", "원티드 예시 공고 2"]
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
    all_jobs = crawl_saramin() + crawl_jobkorea() + crawl_wanted()
    previous_jobs = load_previous_jobs()
    new_jobs = list(set(all_jobs) - set(previous_jobs))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if new_jobs:
        subject = f"[{now}] 새로운 공고 {len(new_jobs)}건 발견!"
        body = "\n".join(new_jobs)
        save_jobs(all_jobs)
    else:
        subject = f"[{now}] 새로운 공고 없음"
        body = "새로운 채용 공고가 없습니다."

    send_email(subject, body)

if __name__ == "__main__":
    main()
