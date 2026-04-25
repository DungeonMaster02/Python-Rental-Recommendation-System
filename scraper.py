from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os
import time

load_dotenv()

def scrap_html_single():
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
    url = os.environ.get('Rent_URL')
    response = requests.get(url,headers=headers)
    page = list()
    try:
        response.raise_for_status()
        html = response.text
        page.append(html)
        return page
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")

def scrap_to_local(number):
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
    base_url = os.environ.get('Rent_URL')
    pages = list()
    for offset in range(0, 120*number, 120):
        time.sleep(1)
        url = f'{base_url}?s={offset}'
        print(f"Fetching: {url}")
        response = requests.get(url,headers=headers)
        try:
            response.raise_for_status()
            html = response.text
            pages.append(html)
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
    pages_str = '\n'.join(pages)
    with open('../data/static_listing_data.txt','w') as f:
        f.write(pages_str)

def scrap_html_multi(page_number): # this function doesn't work now since craigslist only gives a solid static html page for simple scraping, I would try selenium if I have time
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
    base_url = os.environ.get('Rent_URL')
    pages = list()
    for offset in range(0, page_number*120, 120):
        time.sleep(1)
        url = f'{base_url}?s={offset}'
        print(f"Fetching: {url}")
        response = requests.get(url,headers=headers)
        try:
            response.raise_for_status()
            html = response.text
            pages.append(html)
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            pass
    return pages

    
if __name__ == "__main__":
    html = scrap_to_local(5) # set how many pages to scrape