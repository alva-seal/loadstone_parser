# importing the pandas library
import numpy as np
import pandas as pd
import requests
import json
import datetime as dt
global price_history

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
writer.save()
