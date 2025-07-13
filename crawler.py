from playwright.sync_api import sync_playwright
import json
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
import ssl
import os

FROM_EMAIL = os.environ["FROM_EMAIL"]
TO_EMAIL = os.environ["TO_EMAIL"]
APP_PASSWORD = os.environ["APP_PASSWORD"]

def crawl_saramin(playwright):
    print("\n🟢 Saramin Playwright 크롤링 시작")
    jobs = []
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.saramin.co.kr/zf_user/jobs/list/job-category")
    page.wait_for_selector("div.job-item div.job-info h2.job-title a", timeout=15000)
    elements = page.query_selector_all("div.job-item div.job-info h2.job-title a")
    for e in elements[:10]:
        title = e.inner_text().strip()
        link = e.get_attribute("href")
        if title and link:
            if not link.startswith("http"):
                link = "https://www.saramin.co.kr" + link
            jobs.append({"title": title, "link": link})
    browser.close()
    print(f"🟢 Saramin {len(jobs)}개 수집 완료")
    return jobs

def crawl_jobkorea(playwright):
    print("\n🟢 JobKorea Playwright 크롤링 시작")
    jobs = []
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.jobkorea.co.kr/Search/?stext=정보보안")
    page.wait_for_selector("div.list-default ul.clear li div.post-list-info a.title", timeout=15000)
    elements = page.query_selector_all("div.list-default ul.clear li div.post-list-info a.title")
    for e in elements[:10]:
        title = e.inner_text().strip()
        link = e.get_attribute("href")
        if title and link:
            if not link.startswith("http"):
                link = "https://www.jobkorea.co.kr" + link
            jobs.append({"title": title, "link": link})
    browser.close()
    print(f"🟢 JobKorea {len(jobs)}개 수집 완료")
    return jobs

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

def load_previous_jobs():
    try:
        with open("jobs.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("📂 jobs.json 없음. 새로 생성 예정.")
        return []

def save_jobs(jobs):
    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

def main():
    with sync_playwright() as playwright:
        saramin_jobs = crawl_saramin(playwright)
        jobkorea_jobs = crawl_jobkorea(playwright)

    all_jobs = saramin_jobs + jobkorea_jobs

    print("\n전체 수집된 공고:")
    for job in all_jobs:
        print(job)

    previous_links = set(job["link"] for job in load_previous_jobs())
    print(f"이전 공고 링크 수: {len(previous_links)}")

    new_jobs = [job for job in all_jobs if job["link"] not in previous_links]
    print(f"새로운 공고 수: {len(new_jobs)}")

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
