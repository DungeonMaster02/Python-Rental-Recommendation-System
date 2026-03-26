import scrapper
from bs4 import BeautifulSoup

def get_html():
    option = 0
    while int(option) not in [1,2]:
        option = input("Use static data or scrap new data(type 1 or 2):")
        if int(option) == 1:
            with open("../data/static_rent_data.txt", 'r') as f:
                rent_html = f.read()
        elif int(option) == 2:
            rent_html = scrapper.scrap_html()
        else:
            print("Please type again")
    return rent_html

def get_rent(html: str):
    soup = BeautifulSoup(html, 'html')
    rents = soup.find_all('li',class_ = 'cl-static-search-result')
    result = []
    for rent in rents:
        url = rent.find('a')['href'].strip()
        price = rent.find('div', class_ = 'price').text.strip()
        location = rent.find('div', class_ = 'location').text.strip()
        result.append((url,price,location))
    return result


if __name__ =="__main__":
    html = get_html()
    rent = get_rent(html)
    print(rent)
