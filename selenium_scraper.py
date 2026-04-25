from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
import geopandas as gpd
import json
import re
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException, TimeoutException
import db_execution as db
from selenium.webdriver.support.ui import WebDriverWait
import time
import random
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

def setup():
    url = os.environ.get('Rent_URL')
    driver = webdriver.Chrome()
    driver.get(url)
    return driver

def scrap(pages:int):
    driver = setup()
    listings = list()
    unique = set()
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.cl-search-result")) > 0
        )

        for i in range(pages):
            current_items = driver.find_elements(By.CSS_SELECTOR, "div.cl-search-result")
            item_count = len(current_items)

            pid_snapshot = driver.execute_script("""
                return Array.from(document.querySelectorAll('div.cl-search-result'))
                    .map(el => el.getAttribute('data-pid'))
                    .filter(pid => pid);
            """)

            first_pid = pid_snapshot[0] if pid_snapshot else None
            last_pid = pid_snapshot[-1] if pid_snapshot else None

            print(
                f"round {i + 1}: first_pid={first_pid}, "
                f"last_pid={last_pid}, visible={item_count}, collected={len(listings)}"
            )

            for j in range(item_count):
                try:
                    items = driver.find_elements(By.CSS_SELECTOR, "div.cl-search-result")

                    if j >= len(items):
                        continue

                    item = items[j]
                    pid = item.get_attribute("data-pid")

                    if not pid:
                        continue

                except StaleElementReferenceException:
                    continue
                except Exception:
                    continue

                if pid in unique:
                    continue

                try:
                    href_elements = item.find_elements(By.CSS_SELECTOR, "a.posting-title")

                    if not href_elements:
                        unique.add(pid)
                        print(f"skip pid={pid}: missing href")
                        continue

                    href = href_elements[0].get_attribute("href")
                    title = href_elements[0].text.strip()

                except StaleElementReferenceException:
                    try:
                        items = driver.find_elements(By.CSS_SELECTOR, "div.cl-search-result")

                        if j >= len(items):
                            continue

                        item = items[j]
                        href_elements = item.find_elements(By.CSS_SELECTOR, "a.posting-title")

                        if not href_elements:
                            unique.add(pid)
                            print(f"skip pid={pid}: missing href")
                            continue

                        href = href_elements[0].get_attribute("href")
                        title = href_elements[0].text.strip()

                    except StaleElementReferenceException:
                        continue

                try:
                    price_elements = item.find_elements(By.CSS_SELECTOR, "span.priceinfo")
                except StaleElementReferenceException:
                    items = driver.find_elements(By.CSS_SELECTOR, "div.cl-search-result")
                    if j >= len(items):
                        continue
                    item = items[j]
                    try:
                        price_elements = item.find_elements(By.CSS_SELECTOR, "span.priceinfo")
                    except StaleElementReferenceException:
                        continue

                if not price_elements:
                    unique.add(pid)
                    print(f"skip pid={pid}: missing price")
                    continue

                price_str = price_elements[0].text.strip()
                price = int(price_str.replace("$", "").replace(",", ""))

                location_elements = item.find_elements(By.CSS_SELECTOR, ".location")
                location = location_elements[0].text.strip() if location_elements else ""

                latitude = 0
                longitude = 0
                distance_score = 0
                convenience_score = 0
                safety_score = 0

                housing_elements = item.find_elements(By.CSS_SELECTOR, ".housing")
                housing_text = housing_elements[0].text.strip() if housing_elements else ""

                bedroom = 1
                bedroom_match = re.search(r"(\d+)\s*br", housing_text, re.IGNORECASE)
                if bedroom_match:
                    bedroom = int(bedroom_match.group(1))

                unique.add(pid)
                listings.append((
                    href,
                    title,
                    price,
                    location,
                    latitude,
                    longitude,
                    distance_score,
                    convenience_score,
                    safety_score,
                    bedroom,
                ))

            prev_count = len(driver.find_elements(By.CSS_SELECTOR, "div.cl-search-result"))

            driver.execute_script("""
                const items = document.querySelectorAll('div.cl-search-result');
                if (items.length > 0) {
                    items[items.length - 1].scrollIntoView({block: 'end'});
                }
                window.scrollBy(0, Math.floor(window.innerHeight * 15));
            """)

            new_count = len(driver.find_elements(By.CSS_SELECTOR, "div.cl-search-result"))
            print(f"round {i+1}: before={prev_count}, after={new_count}, collected={len(listings)}")
    finally:
        driver.quit()

    return listings
def delay(min_seconds=3.5, max_seconds=6.5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def scroll(driver):
    scroll_times = random.randint(1, 3)

    for _ in range(scroll_times):
        driver.execute_script(
            "window.scrollBy(0, arguments[0]);",
            random.randint(250, 800)
        )
        time.sleep(random.uniform(0.5, 1.5))

def scrap_detail():
    driver = webdriver.Chrome()
    driver.set_page_load_timeout(20) 
    listings = db.query('listing', ['href'])
    wait = WebDriverWait(driver, 10)
    count = 0

    try:
        for (url,) in listings:
            count += 1
            delay(2.5, 4.5)
            netcount = 0
            success = 0
            while netcount < 6:
                try:
                    driver.get(url)
                    delay(1.5, 3.5)
                    scroll(driver)
                    success = 1
                    break
                except (WebDriverException, TimeoutException):
                    print(f"Network/page load failed. Waiting 10 seconds and retrying {netcount + 1}/6...")
                    netcount += 1
                    time.sleep(10)
                    if netcount == 6:
                        conti = input("Do you want to continue scraping?")
                        if conti.lower() == 'yes':
                            driver.quit()
                            driver = webdriver.Chrome()
                            driver.set_page_load_timeout(20) 
                            netcount = 0
                            continue
                        else:
                            print(f"Skip: {url}")
                            db.delete('listing', 'href', url)
                            break 
            if not success:
                continue
            try:
                element = wait.until(
                    EC.presence_of_element_located((By.ID, "ld_posting_data"))
                )
            except:
                print("Missing page, deleting from database")
                db.delete('listing', 'href', url)
                continue

            try:
                element = driver.find_element(By.ID, "ld_posting_data")
                json_data = element.get_attribute("innerHTML")
                data = json.loads(json_data)
                latitude = data["latitude"]
                longitude = data["longitude"]
            except:
                print(f"Missing latitude/longitude for {url}")
                db.delete('listing', 'href', url)
                continue
            db.update('listing', {'latitude': latitude, 'longitude': longitude}, 'href', url)
            print(f"Processed {count}/{len(listings)}")
    finally:
        driver.quit()


if __name__ == "__main__":
    pass
    
