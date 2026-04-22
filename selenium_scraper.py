from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
import data_processing as dp
import geopandas as gpd
import json
import re
from selenium.common.exceptions import StaleElementReferenceException

load_dotenv()

def setup():
    url = os.environ.get('Rent_URL')
    driver = webdriver.Chrome()
    driver.get(url)
    return driver

def scrap(pages:int):
    usc = gpd.read_file("../data/usc_campus/usc_campus.shp")
    grid = gpd.read_file("../data/City_Boundary/LA_400m_grid.shp")
    grid = grid.to_crs("EPSG:32611").reset_index(drop=True)
    grid["grid_id"] = grid.index + 1
    grid_score_map = dp.get_grid_score_map()
    # print(usc.crs) #EPSF: 4326
    usc_center = usc.to_crs("EPSG:32611")
    usc_center = usc_center.geometry.union_all().centroid

    driver = setup()
    listings = list()
    unique = set() # make sure the listings are unique
    driver.implicitly_wait(3)

    try:
        for i in range(pages):
            driver.implicitly_wait(3)
            items = driver.find_elements(By.CSS_SELECTOR, "div.cl-search-result")

            pid_snapshot = driver.execute_script("""
                return Array.from(document.querySelectorAll('div.cl-search-result'))
                    .map(el => el.getAttribute('data-pid'))
                    .filter(pid => pid);
            """)

            first_pid = pid_snapshot[0] if pid_snapshot else None
            last_pid = pid_snapshot[-1] if pid_snapshot else None
            print(f"round {i+1}: first_pid={first_pid}, last_pid={last_pid}, collected={len(listings)}")
            script_text = driver.find_element(By.ID, "ld_searchpage_results").get_attribute("innerHTML")
            data = json.loads(script_text)
            item_list = data.get("itemListElement", [])
            for j in range(min(len(items), len(item_list))):
                detail = item_list[j].get('item', {})

                try:
                    item = items[j]
                    pid = item.get_attribute("data-pid")
                except StaleElementReferenceException:
                    items = driver.find_elements(By.CSS_SELECTOR, "div.cl-search-result")
                    if j >= len(items):
                        continue
                    item = items[j]
                    try:
                        pid = item.get_attribute("data-pid")
                    except StaleElementReferenceException:
                        continue
                except:
                    continue

                if pid in unique:
                    continue

                try:
                    href_elements = item.find_elements(By.CSS_SELECTOR, "a.posting-title")
                except StaleElementReferenceException:
                    items = driver.find_elements(By.CSS_SELECTOR, "div.cl-search-result")
                    if j >= len(items):
                        continue
                    item = items[j]
                    try:
                        href_elements = item.find_elements(By.CSS_SELECTOR, "a.posting-title")
                    except StaleElementReferenceException:
                        continue

                if not href_elements:
                    unique.add(pid)
                    print(f"skip pid={pid}: missing href")
                    continue

                href = href_elements[0].get_attribute("href")
                title = detail.get("name", "").strip()

                try:
                    price_elements = item.find_elements(By.CSS_SELECTOR, "span.priceinfo")
                except StaleElementReferenceException:
                    items = driver.find_elements(By.CSS_SELECTOR, "div.cl-search-result")
                    if j >= len(items):
                        continue # this means the item disappeared after we found it, we can just skip this item
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
                location = detail.get("address", {}).get("addressLocality", "").strip()
                latitude = detail.get("latitude", 0)
                longitude = detail.get("longitude", 0)
                distance_score = dp.to_score(dp.get_distance(usc_center, longitude, latitude), "distance")
                listing_point = gpd.GeoSeries(
                    gpd.points_from_xy([longitude], [latitude]),
                    crs="EPSG:4326"
                ).to_crs("EPSG:32611").iloc[0]
                matched_grid = grid.loc[grid.geometry.intersects(listing_point), "grid_id"]
                if matched_grid.empty:
                    convenience_score, safety_score = 0, 0
                else:
                    grid_id = int(matched_grid.iloc[0])
                    convenience_score, safety_score = grid_score_map.get(grid_id, (0, 0)) #default to 0 if grid_id not found
                bedroom = detail.get("numberOfBedrooms", 1)
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
            prev_count = len(items)

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

if __name__ == "__main__":
    pass
    
