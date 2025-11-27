from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import csv


START = "https://openedu.ru/course/"
GECKODRIVER_PATH = "./geckodriver.exe"
HEADLESS = True
TIMEOUT = 10
MAX_COUNT = 1189 #check the actual count at https://openedu.ru/course/


def setup_driver():
    options = webdriver.FirefoxOptions()
    options.set_preference("intl.accept_languages", "en-US,en;q=0.8")
    options.set_preference(
        "general.useragent.override", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )

    if HEADLESS:
        options.add_argument("-headless")

    service = Service(GECKODRIVER_PATH)
    driver = webdriver.Firefox(service=service, options=options)
    return driver


def parse_course_li(li):
    href = li.find_element(By.XPATH, "./div/a").get_attribute("href")
    title = li.find_element(By.XPATH, "./div/div/a[1]").text.strip()
    university = li.find_element(By.XPATH, "./div/div/a[2]").text.strip()
    dates_parent = li.find_element(By.XPATH, "./div/div/div/div[2]/div[2]")
    start_date = dates_parent.find_element(By.XPATH, "./span[1]").text[5:].strip()
    end_date = dates_parent.find_element(By.XPATH, "./span[2]").text[3:].strip()

    return {
        "title": title,
        "url": href,
        "university": university,
        "start_date": start_date,
        "end_date": end_date
    }


def load_all_courses(driver):
    ul_xpath = "/html/body/div[2]/div[1]/main/div/div[2]/div/ul"
    button_xpath = "/html/body/div[2]/div[1]/main/div/div[2]/div/button[1]"
    driver.get(START)
    wait = WebDriverWait(driver, TIMEOUT)
    wait.until(EC.presence_of_element_located((By.XPATH, ul_xpath)))
    wait.until(EC.presence_of_element_located((By.XPATH, button_xpath)))
    btn = driver.find_element(By.XPATH, button_xpath)

    count = 0
    while count < MAX_COUNT:
        btn.click()
        lis = driver.find_elements(By.XPATH, ul_xpath + "/li")
        count = len(lis)

    return driver.find_elements(By.XPATH, ul_xpath + "/li")


def save_csv(items, out_file="openedu_courses.csv"):
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "index", "title", "url", "university", 
            "start_date", "end_date"
        ])
        writer.writeheader()
        for it in items:
            writer.writerow(it)


def main():
    driver = setup_driver()
    lis = load_all_courses(driver)

    items = []
    for index, li in enumerate(lis, start=1):
        parsed = parse_course_li(li)
        parsed["index"] = index
        items.append(parsed)

    save_csv(items)

    print("Found:", len(items), "courses")

    driver.quit()


if __name__ == "__main__":
    main()
