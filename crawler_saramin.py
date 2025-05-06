from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def crawl_saramin():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    url = "https://www.saramin.co.kr/zf_user/search?searchword=정보보안&loc_cd=101000%2C102000&panel_type=&search_done=y&panel_count=y&preview=y"
    driver.get(url)
    time.sleep(3)

    jobs = []
    elements = driver.find_elements(By.CSS_SELECTOR, "div.item_recruit")
    for elem in elements[:10]:
        try:
            title_elem = elem.find_element(By.CSS_SELECTOR, "h2.job_tit a")
            company_elem = elem.find_element(By.CSS_SELECTOR, "div.area_corp a.corp_name")

            job = {
                "title": title_elem.text.strip(),
                "link": title_elem.get_attribute("href"),
                "company": company_elem.text.strip()
            }
            jobs.append(job)
        except:
            continue

    driver.quit()
    return jobs
