# job_crawler_api_version.py
import os
import json
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
import ssl
import requests
import re

FROM_EMAIL = os.environ["FROM_EMAIL"]
TO_EMAIL = os.environ["TO_EMAIL"]
APP_PASSWORD = os.environ["APP_PASSWORD"]

def crawl_saramin():
    print("\n🟢 Saramin API 크롤링 시작")
    jobs = []
    try:
        url = "https://oapi.saramin.co.kr/job-search"
        params = {
            "keywords": "정보보안",
            "count": 10,
            "fields": "posting-date+apply-url+company+position"
        }
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json()
            items = data.get("jobs", [])
            for item in items:
                job_data = item.get("position")
                company = item.get("company", {}).get("name")
                title = job_data.get("title") if job_data else None
                link = item.get("apply_url")
                if title and link:
                    jobs.append({"title": f"{title} - {company}", "link": link})
        print(f"🟢 Saramin {len(jobs)}개 수집 완료")
    except Exception as e:
        print(f"❌ Saramin API 실패: {e}")
    return jobs

def crawl_jobkorea():
    print("\n🟢 JobKorea HTML 파싱 시작")
    jobs = []
    try:
        url = "https://www.jobkorea.co.kr/Search/?stext=정보보안"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            html = res.text
            titles = re.findall(r'data-garecruit-title="(.*?)"', html)
            links = re.findall(r'href="(/Recruit/GIRead/.*?)"', html)
            min_len = min(len(titles), len(links))
            for i in range(min_len):
                jobs.append({"title": titles[i], "link": f"https://www.jobkorea.co.kr{links[i]}"})
        print(f"🟢 JobKorea {len(jobs)}개 수집 완료")
    except Exception as e:
        print(f"❌ JobKorea HTML 파싱 실패: {e}")
    return jobs

def crawl_wanted():
    print("\n🟢 Wanted API 크롤링 시작")
    jobs = []
    try:
        url = "https://www.wanted.co.kr/api/v4/jobs"
        params = {
            "limit": 10,
            "query": "정보보안",
            "job_sort": "job.latest_order"
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, params=params, headers=headers)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("data", []):
                title = item.get("position")
                link = f"https://www.wanted.co.kr/wd/{item.get('id')}"
                company = item.get("company", {}).get("name")
                if title and link:
                    jobs.append({"title": f"{title} - {company}", "link": link})
        print(f"🟢 Wanted {len(jobs)}개 수집 완료")
    except Exception as e:
        print(f"❌ Wanted API 실패: {e}")
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
    saramin_jobs = crawl_saramin()
    jobkorea_jobs = crawl_jobkorea()
    wanted_jobs = crawl_wanted()

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
