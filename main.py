import requests
from bs4 import BeautifulSoup
import os
import re
import sqlite3

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}


def get_list_car():
    # URL = "https://auto.ria.com/uk/search/"
    url = "https://auto.ria.com/uk/search/?indexName=auto,order_auto,newauto_search&categories.main.id=1&brand.id[0]=79&model.id[0]=2104&country.import.usa.not=0&price.currency=1&abroad.not=0&custom.not=1&damage.not=0&page=0&size=10"
    search_params = {'categories.main.id': 1,
                     'brand.id[0]': 79,
                     'model.id[0]': 2104,
                     'damage.not': 0,
                     'indexName': 'auto,order_auto,newauto_search',
                     'country.import.usa.not': 0}
    r = requests.get(url, headers=HEADERS, data=search_params)

    soup = BeautifulSoup(r.content, 'html5lib')
    all_cars = soup.find('section', {'id': 'open'}).find_all('section', {'class': 'ticket-item'})
    list_car = []
    for car in all_cars:
        list_car.append(car.find('a', {'m-link-ticket'}, href=True)['href'])
    list_car.append('https://auto.ria.com/uk/auto_volkswagen_touareg_34712606.html')
    return list_car


def get_car_info(url):
    r = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(r.content, 'html5lib')
    try:
        city = soup.find('div', {'class': 'item_inner'}).text
    except AttributeError:
        city = 'Не знайдено'

    car_info = {'title': soup.find('h1', {'class': 'head'}).text,
                'price': soup.find('div', {'class': 'price_value'}).find('strong').text,
                'mileage': soup.find('div', {'class': 'base-information bold'}).text,
                'city': city,
                'link': url,
                'auction_link': soup.find('script', attrs={'data-bidfax-pathname': True})[
                    'data-bidfax-pathname'].replace('/bidfax', 'https://bidfax.info/'),
                'sold': 1 if soup.find('div', {'class': 'notice notice--icon notice--orange'}) else 0
                }
    vin_code = re.search(r'-(\w{17})\.html$', car_info['auction_link']).group(1) if car_info['auction_link'] \
        else car_info['title']
    car_info['vin'] = vin_code

    os.makedirs(os.path.dirname(f'photos/{vin_code}/'), exist_ok=True)

    photos = soup.findAll('img', {'class': 'outline m-auto'})
    file_names = []
    for i in range(4):
        img_data = requests.get(photos[i]['src']).content
        with open(f'photos/{vin_code}/{car_info["title"]}_{i}.jpg', 'wb') as handler:
            handler.write(img_data)
            file_names.append(f'photos/{vin_code}/{car_info["title"]}_{i}.jpg')

    car_info['images'] = file_names
    return car_info


def write_to_db():
    links = get_list_car()
    conn = sqlite3.connect('cars.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS CAR_INFO
                 ("VIN"            CHAR(30) PRIMARY KEY     NOT NULL,
                 "TITLE"           TEXT    NOT NULL,
                 "PRICE"            TEXT     NOT NULL,
                 "MILEAGE"        CHAR(20)   NOT NULL,
                 "CITY"           TEXT      NOT NULL,
                 "AUCTION_LINK"       CHAR(50),
                 "LINK"       CHAR(50),
                 "IMAGES"         TEXT    NOT NULL,
                 "MESSAGE"       TEXT    DEFAULT 'new'  NOT NULL,
                 "SOLD"         BOOLEAN);''')

    for link in links:
        car = get_car_info(link)
        cur = conn.cursor()
        cur.execute("SELECT VIN, PRICE, SOLD FROM CAR_INFO WHERE VIN = ?", (car['vin'],))
        query = cur.fetchone()
        if not query:
            try:
                conn.execute(
                    "INSERT INTO CAR_INFO (VIN, TITLE, PRICE, MILEAGE, CITY, LINK, AUCTION_LINK, IMAGES, SOLD) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (car['vin'], car['title'], car['price'], car['mileage'], car['city'], car['link'],
                     car['auction_link'], '!'.join(car['images']), car['sold'])
                )
                conn.commit()
                print(f"Inserted car with VIN: {car['vin']}")
            except sqlite3.Error as e:
                print(f"Error inserting car with VIN: {car['vin']}")
                print(e)
        else:
            if query[1] != car['price']:
                conn.execute(f"UPDATE CAR_INFO set PRICE = ? MESSAGE = ? where VIN = ?;",
                             (car['price'], 'changed_price', car['vin'],))
            if query[2] != car['sold']:
                conn.execute(f"UPDATE CAR_INFO set MESSAGE = ? SOLD = ? where VIN = ?;",
                             ('changed_status', 1, car['vin'],))

    conn.close()
