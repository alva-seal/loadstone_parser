from onepassword import OnePassword
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import pyotp
import csv
import time
import config


# get login credentials
op = OnePassword(password=config.passwd_1pass)
credentials = op.get_item(uuid="dbdxb4ujrrculm4ftiocbs5yk4", fields=["username", "password", "otp"])
totp = pyotp.parse_uri(credentials['otp'])
url = 'https://eu.finalfantasyxiv.com/lodestone/account/login/?back=%2Flodestone%2Fmy%2F'
url_retainer = 'https://eu.finalfantasyxiv.com/lodestone/character/36103000/retainer/'
url_character = 'https://eu.finalfantasyxiv.com/lodestone/character/36103000/'

retainers = {
    'Fur-seal': '7107199c63',
    'Csukepo': 'd65bfd3c44',
    'Grayseal': 'bd4280dd76',
    'Halichoerus': '1ba0d4a5cd',
    'Harbour-seal': 'bc94fadd3c',
    'Norderney ': '2415399d36',
    'Otter': '6c4db7beb1',
    'Sealottere': '073e4e46cb',
    'Seaotter': 'e7d9c967ca',
    'Wmulte': '7036526b72'
}

DRIVER_PATH = '/opt/homebrew/bin/chromedriver'

options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")

driver = webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
driver.get(url)

username = driver.find_element_by_id("sqexid")
password = driver.find_element_by_id("password")
username.send_keys(credentials['username'])
password.send_keys(credentials['password'])
driver.find_element_by_id("view-loginArea").click()
otppw = driver.find_element_by_id("otppw")
otppw.send_keys(totp.now())
driver.find_element_by_id("view-loginArea").click()
time.sleep(1)
driver.find_element_by_class_name("entry").click()
data = driver.page_source
time.sleep(2.4)
driver.get(url_character)
character_data = driver.page_source
retainer_data = {}
for retainer in retainers:
    url_ret = ''.join([url_retainer, retainers[retainer], '/'])
    driver.get(url_ret)
    retainer_data[retainer] = driver.page_source

driver.quit()


with open('sales.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Retainer", "Product", "Price", "Buyer", "Timestamp"])
    for retainer in retainers:
        soup = BeautifulSoup(retainer_data[retainer],  features="html.parser")
        result = soup.find("div", {"name": "tab__market-logs"})
        list2 = result.find("ul", {"class": "item-list--footer"})
        list3 = list2.find_all("li", {"class": "item-list__list"})
        for item in list3:
            if item.text is None:
                break
            product = item.contents[1].contents[1].text.replace('\n', '').replace('\r', '').replace('\t', '')
            price = item.contents[3].text
            buyer = item.contents[5].text
            timestamp = datetime.fromtimestamp(int(item.contents[7].contents[1].attrs['data-epoch']))
            writer.writerow([retainer, product, price, buyer, timestamp])

with open('on_market.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Retainer", "Product", "Price", "Buyer", "Timestamp"])
    for retainer in retainers:
        soup = BeautifulSoup(retainer_data[retainer], features="html.parser")
        result = soup.find("div", {"name": "tab__market-list"})
        list2 = result.find("ul", {"class": "item-list--footer"})
        list3 = list2.find_all("li", {"class": "item-list__list"})
        for item in list3:
            if item.text is None:
                break
            product = item.contents[0].text
            price = item.contents[1].text
            quantity = item.contents[2].text
            total_price = item.contents[3].text
            writer.writerow([retainer, product, price, quantity, total_price])
