import json
import os
from crawler_saramin import crawl_saramin
from crawler_jobkorea import crawl_jobkorea
from email_utils import send_email

def load_previous_jobs(filepath='jobs.json'):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_jobs(jobs, filepath='jobs.json'):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

def compare_jobs(prev_jobs, new_jobs):
    prev_set = {json.dumps(job, sort_keys=True) for job in prev_jobs}
    return [job for job in new_jobs if json.dumps(job, sort_keys=True) not in prev_set]

def format_job_list(jobs):
    if not jobs:
        return "📭 새로운 공고가 없습니다."
    message = "📢 새로운 채용 공고:\n\n"
    for job in jobs:
        message += f"- [{job['title']}]({job['link']}) @ {job['company']}\n"
    return message

def main():
    all_jobs = crawl_saramin() + crawl_jobkorea()
    prev_jobs = load_previous_jobs()
    new_jobs = compare_jobs(prev_jobs, all_jobs)
    save_jobs(all_jobs)
    message = format_job_list(new_jobs)
    send_email("📌 채용 공고 알림", message)

if __name__ == '__main__':
    main()
