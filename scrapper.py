from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os

load_dotenv()

def scrap_html():
    url = os.environ.get('Rent_URL')
    response = requests.get(url)
    try:
        response.raise_for_status()
        html = response.text
        return html
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")


if __name__ == "__main__":
    html = scrap_html()
    with open('../data/static_rent_data.txt','w') as f:
        f.write(html)