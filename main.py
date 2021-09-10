from onepassword import OnePassword
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import pyotp
import csv
import time
import config
import xivapi
import asyncio
import numpy as np
import pandas as pd
import requests
import json
import datetime as dt
global price_history

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
# retainers = {
#     'Fur-seal': '7107199c63'
# }

# tax ra
DRIVER_PATH = '/opt/homebrew/bin/chromedriver'

options = Options()
#options.headless = True
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


loop = asyncio.get_event_loop()

IDs = []
with open('on_market.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Retainer", "Product", "Price", "Buyer", "Timestamp", "HQ", "ID"])
    for retainer in retainers:
        soup = BeautifulSoup(retainer_data[retainer], features="html.parser")
        result = soup.find("div", {"name": "tab__market-list"})
        list2 = result.find("ul", {"class": "item-list--footer"})
        list3 = list2.find_all("li", {"class": "item-list__list"})
        for item in list3:
            if item.text is None:
                break
            if "\ue03c" in item.find("div", {"class": "item-list__relative"}).find_all("a")[0].text:
                hq = 1
            else:
                hq = 0
            product = item.find("div", {"class": "item-list__relative"}).find_all("a")[0].text.split("\ue03c")[0]
            price = item.contents[1].text
            quantity = item.contents[2].text
            total_price = item.contents[3].text
            result = loop.run_until_complete(xivapi.fetch_example_results(product))
            xivapi_id = result['Results'][0]['ID']
            writer.writerow([retainer, product, price, quantity, total_price, hq, xivapi_id])
            IDs.append(xivapi_id)


global shortterm
global longterm

now = dt.datetime.now()
shortterm = now - dt.timedelta(days=7)
longterm = now - dt.timedelta(days=28)


def get_mean(itemid, price, hq, history):
    # row = history.loc('itemIDs' == ID
    try:
        historic_sales = pd.json_normalize(list(filter(lambda dataset: dataset['itemID'] == itemid, history['items']))[0]['entries'])
    except:
        return 0, 0, 0, 0, 0, 0, -1
    else:
        # last 30 days last 7
        historic_7d = historic_sales[(historic_sales.timestamp > shortterm.timestamp()) & (historic_sales.hq == hq)]
        historic_28d = historic_sales[(historic_sales.timestamp > longterm.timestamp()) & (historic_sales.hq == hq)]
        check = 0
        if price > historic_7d.mean()['pricePerUnit']:
            check = 1
        return historic_7d.mean()['pricePerUnit'], historic_7d.count()['quantity'], historic_7d.mean()['quantity'], historic_28d.mean()['pricePerUnit'], historic_28d.count()['quantity'], historic_28d.mean()['quantity'], check

df = pd.read_csv('on_market.csv', thousands=',')


# get all IDs
IDs = np.unique(df['ID'])
# get prices
price_history = None

for i in np.arange(0, IDs.size, 100):
    universalis_url = ''.join(['https://universalis.app/api/history/Zodiark/', str(IDs[i:i+100].tolist())[1:-1]])
    if price_history is not None:
        new_data = json.loads(requests.get(universalis_url).text)
        price_history['itemIDs'] = price_history['itemIDs'] + new_data['itemIDs']
        price_history['items'] = price_history['items'] + new_data['items']
    else:
        price_history = json.loads(requests.get(universalis_url).text)

# add collumns
df[['m7d', 'c7d', 's7d', 'm28d', 'c28d', 's28d', 'check']] = df.apply(lambda row: get_mean(row.ID, row.Price, row.HQ, price_history), axis=1, result_type="expand")


# tax rates

tax_url = 'https://universalis.app/api/tax-rates?world=42'
results = requests.get(tax_url)
taxrates = pd.json_normalize(results.text)


df.to_csv('sellout.csv')

writer = pd.ExcelWriter('MB_to_do.xlsx', engine='xlsxwriter')
df.to_excel(writer, sheet_name="Market Board")
df2 = df[df.check == 1]
workbook = writer.book
worksheet = writer.sheets['Market Board']
format_ok = workbook.add_format({'bg_color': '#00ff00'})
format_todo = workbook.add_format({'bg_color': '#ff0000'})
format_error = workbook.add_format({'bg_color': '#ff00ff'})
worksheet.conditional_format('O2:O201', {'type':  'cell',
                                   'criteria': '==',
                                   'value': 0,
                                   'format': format_ok})
worksheet.conditional_format('O2:O201', {'type':  'cell',
                                   'criteria': '==',
                                   'value': -1,
                                   'format': format_error})
worksheet.conditional_format('O2:O201', {'type':  'cell',
                                   'criteria': '==',
                                   'value': 1,
                                   'format': format_todo})
df2.to_excel(writer, sheet_name="TODO")
worksheet = writer.sheets['TODO']
worksheet.conditional_format('O2:O201', {'type':  'cell',
                                   'criteria': '==',
                                   'value': 1,
                                   'format': format_todo})
taxrates.to_excel(writer, sheet_name="Tax rates")
writer.save()
