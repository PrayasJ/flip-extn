import json
import sys
from flask import Flask, request
from flask_cors import CORS
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
import os
import re
import time
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

import tqdm
import multiprocessing

chromedriver_autoinstaller.install()

import xlrd

# def get_listing_price():
#     base_url = 'https://www.flipkart.com/search?q=paxauto&page='
#     product_urls = []
#     page = 1
#     while True:
#         url = base_url + str(page)
#         response = requests.get(url)
#         soup = BeautifulSoup(response.content, 'html.parser')
#         if not soup.find_all('a', {'class': '_2rpwqI'}):
#             break
#         for link in soup.find_all('a', {'class': '_2rpwqI'}):
#             product_urls.append('https://www.flipkart.com' + link.get('href'))
#         page += 1
#     data = []
#     options = Options()
#     options.headless = True
#     driver2 = webdriver.Chrome(options=options)
#     count = 0
#     total = len(product_urls)
#     for url in product_urls:
#         print(f"Processed {count} out of {total}")
#         count += 1
#         try:
#             response = requests.get(url)
#             soup = BeautifulSoup(response.content, 'html.parser')
#             product_name_element = soup.find('span', {'class': 'B_NuCI'})
#             product_name = product_name_element.text.strip()
#             selling_price_element = soup.find(
#                 'div', {'class': ['_30jeq3', '_16Jk6d']})
#             selling_price = selling_price_element.text.strip()
#             parsed_url = urlparse(url)
#             params = parse_qs(parsed_url.query)
#             pid = params['pid'][0]
#             seller_url = "https://www.flipkart.com/sellers?pid=" + pid
#             driver2.get(seller_url)
#             wait = WebDriverWait(driver2, 60)
#             wait.until(EC.visibility_of_element_located(
#                 (By.CLASS_NAME, '_2Y3EWJ')))
#             html = driver2.page_source
#             soup = BeautifulSoup(html, 'html.parser')

#             prices = soup.find_all('div', {'class': '_2Y3EWJ'})
#             d = {
#                 'product_name': product_name,
#                 'pid': pid,
#                 'url': url,
#                 "price": selling_price,
#                 'other_prices': []
#             }
#             for price in prices:
#                 seller = price.find('div', {'class': '_3enH42'}).text.strip()
#                 amount = price.find('div', {'class': '_30jeq3'}).text.strip()
#                 d['other_prices'].append({seller: amount})
#             min_dict = min(d['other_prices'], key=lambda x: int(x[next(iter(x))].replace('₹', '').replace(',', '')))
#             key, value = list(min_dict.items())[0]
#             d['pax_value'] = next((x["paxauto"] for x in d['other_prices'] if "paxauto" in x), None)
#             d['min_seller'] = key
#             d['min_price'] = value
#             data.append(d)
#         except Exception as e:
#             print(f'Couldn\'t Process {url}')
#     driver2.quit()
#     return data

def process_url(pid):
    options = Options()
    options.headless = True
    driver2 = webdriver.Chrome(options=options)
    seller_url = "https://www.flipkart.com/sellers?pid=" + pid
    d = {}
    try:
        driver2.get(seller_url)
        wait = WebDriverWait(driver2, 60)
        wait.until(EC.visibility_of_element_located(
            (By.CLASS_NAME, '_2Y3EWJ')))
        html = driver2.page_source
        soup = BeautifulSoup(html, 'html.parser')
        prices = soup.find_all('div', {'class': '_2Y3EWJ'})

        product_page_url = 'https://www.flipkart.com' + soup.find('div', {'class': '_52cNDb'}).find('a').get('href')
        response = requests.get(product_page_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        product_name_element = soup.find('span', {'class': 'B_NuCI'})
        product_name = product_name_element.text.strip()
        selling_price_element = soup.find(
            'div', {'class': ['_30jeq3', '_16Jk6d']})
        selling_price = selling_price_element.text.strip()        
        d = {
            'product_name': product_name,
            'pid': pid,
            'url': product_page_url,
            "price": selling_price,
            'other_prices': []
        }
        for price in prices:
            seller = price.find('div', {'class': '_3enH42'}).text.strip()
            amount = price.find('div', {'class': '_30jeq3'}).text.strip()
            d['other_prices'].append({seller: amount})
        min_dict = min(d['other_prices'], key=lambda x: int(x[next(iter(x))].replace('₹', '').replace(',', '')))
        key, value = list(min_dict.items())[0]
        d['pax_value'] = next((x["paxauto"] for x in d['other_prices'] if "paxauto" in x), None)
        d['min_seller'] = key
        d['min_price'] = value
    except Exception as e:
        print(f'Couldnt process {seller_url}')
    return d
def get_listing_price_2():
    workbook = xlrd.open_workbook('data.xls')
    worksheet = workbook.sheet_by_index(0)
    header_row = worksheet.row_values(0)

    col_name = 'Flipkart Serial Number'
    col_index = header_row.index(col_name)

    pids = []
    for i in range(2, worksheet.nrows):
        row = worksheet.row_values(i)
        pids.append(row[col_index])
    
    pool = multiprocessing.Pool()
    data = list(tqdm.tqdm(pool.imap(process_url, pids), total=len(pids)))

    return data

if __name__ == '__main__':
    get_listing_price_2()

# @app.route('/', methods = ['POST'])
# # ‘/’ URL is bound with hello_world() function.
# def hello_world():
#     tab = request.json['tab']
#     vertical = request.json['vertical']
#     print(f'Tab visited from is {tab}, vertical={vertical}!')
#     productData = fetchProductData(tab)
#     openAndFill(productData, vertical, sys.argv[1], sys.argv[2])
#     return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
 
# # main driver function
# if __name__ == '__main__':
 
#     # run() method of Flask class runs the application
#     # on the local development server.
#     app.run(debug=True)
