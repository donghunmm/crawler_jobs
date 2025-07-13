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
    print("🟢 Saramin 크롤링 시작")
    jobs = []
    try:
        page.goto("https://www.saramin.co.kr/zf_user/jobs/list/job-category", timeout=60000)
        page.wait_for_selector("div.area_job > h2.job_tit > a")
        elements = page.query_selector_all("div.area_job > h2.job_tit > a")
        for e in elements[:5]:
            title = e.get_attribute("title").strip()
            link = e.get_attribute("href")
            jobs.append({"title": title, "link": link})
        print(f"🟢 Saramin {len(jobs)}개 수집")
    except Exception as e:
        print(f"❌ Saramin 크롤링 실패: {e}")
    return jobs

def crawl_jobkorea(page):
    print("🟢 JobKorea 크롤링 시작")
    jobs = []
    try:
        page.goto("https://www.jobkorea.co.kr/recruit/joblist", timeout=60000)
        page.wait_for_selector("div.list-default > ul.clear > li > div.post-list-info > a.title")
        elements = page.query_selector_all("div.list-default > ul.clear > li > div.post-list-info > a.title")
        for e in elements[:5]:
            title = e.inner_text().strip()
            link = e.get_attribute("href")
            jobs.append({"title": title, "link": link})
        print(f"🟢 JobKorea {len(jobs)}개 수집")
    except Exception as e:
        print(f"❌ JobKorea 크롤링 실패: {e}")
    return jobs

def crawl_wanted(page):
    print("🟢 Wanted 크롤링 시작")
    jobs = []
    try:
        page.goto("https://www.wanted.co.kr/jobsfeed", timeout=60000)
        page.wait_for_selector("div.JobCard_container__z4_3g a")
        elements = page.query_selector_all("div.JobCard_container__z4_3g a")
        count = 0
        for e in elements:
            link = e.get_attribute("href")
            if link and "/wd/" in link:
                title = e.inner_text().strip()
                jobs.append({"title": title, "link": link})
                count += 1
                if count >= 5:
                    break
        print(f"🟢 Wanted {len(jobs)}개 수집")
    except Exception as e:
        print(f"❌ Wanted 크롤링 실패: {e}")
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        saramin_jobs = crawl_saramin(page)
        jobkorea_jobs = crawl_jobkorea(page)
        wanted_jobs = crawl_wanted(page)
        browser.close()

    all_jobs = saramin_jobs + jobkorea_jobs + wanted_jobs

    print("전체 수집된 공고:")
    for job in all_jobs:
        print(job)
    
    previous_links = set(job["link"] for job in load_previous_jobs())
    print(f"이전 공고 링크 수: {len(previous_links)}")

    new_jobs = [job for job in all_jobs if job["link"] not in previous_links]
    print(f"새로운 공고 수: {len(new_jobs)}")

    previous_links = set(job["link"] for job in load_previous_jobs())
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
