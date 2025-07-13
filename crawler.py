# job_crawler_playwright.py
import os
import json
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
import ssl
from playwright.sync_api import sync_playwright

FROM_EMAIL = os.environ["FROM_EMAIL"]
TO_EMAIL = os.environ["TO_EMAIL"]
APP_PASSWORD = os.environ["APP_PASSWORD"]

def crawl_saramin(page):
    print("\n🟢 Saramin 크롤링 시작")
    jobs = []
    try:
        page.goto("https://www.saramin.co.kr/zf_user/jobs/list/job-category", timeout=60000)
        page.wait_for_timeout(3000)
        page.wait_for_selector("div.area_job > h2.job_tit > a", timeout=10000)
        elements = page.query_selector_all("div.area_job > h2.job_tit > a")
        for e in elements[:5]:
            title = e.get_attribute("title") or e.inner_text().strip()
            link = e.get_attribute("href")
            if title and link:
                jobs.append({"title": title.strip(), "link": link})
        print(f"🟢 Saramin {len(jobs)}개 수집 완료")
    except Exception as e:
        print(f"❌ Saramin 크롤링 실패: {e}")
    return jobs

def crawl_jobkorea(page):
    print("\n🟢 JobKorea 크롤링 시작")
    jobs = []
    try:
        page.goto("https://www.jobkorea.co.kr/recruit/joblist", timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("div.list-default > ul.clear > li > div.post-list-info > a.title")
        elements = page.query_selector_all("div.list-default > ul.clear > li > div.post-list-info > a.title")
        for e in elements[:5]:
            title = e.inner_text().strip()
            link = e.get_attribute("href")
            if title and link:
                jobs.append({"title": title, "link": link})
        print(f"🟢 JobKorea {len(jobs)}개 수집 완료")
    except Exception as e:
        print(f"❌ JobKorea 크롤링 실패: {e}")
    return jobs

def crawl_wanted(page):
    print("\n🟢 Wanted 크롤링 시작")
    jobs = []
    try:
        page.goto("https://www.wanted.co.kr/jobsfeed", timeout=60000)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(5000)
        page.wait_for_selector("div.JobCard_container__z4_3g a")
        elements = page.query_selector_all("div.JobCard_container__z4_3g a")
        count = 0
        for e in elements:
            link = e.get_attribute("href")
            if link and "/wd/" in link:
                title = e.inner_text().strip()
                if title:
                    jobs.append({"title": title, "link": link})
                    count += 1
                if count >= 5:
                    break
        print(f"🟢 Wanted {len(jobs)}개 수집 완료")
    except Exception as e:
        print(f"❌ Wanted 크롤링 실패: {e}")
    return jobs

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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36")
        page = context.new_page()

        saramin_jobs = crawl_saramin(page)
        jobkorea_jobs = crawl_jobkorea(page)
        wanted_jobs = crawl_wanted(page)

        browser.close()

    all_jobs = saramin_jobs + jobkorea_jobs + wanted_jobs

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
