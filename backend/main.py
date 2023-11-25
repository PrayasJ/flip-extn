# import time
# import os
import json
# import sys
import multiprocessing
import requests
from flask import Flask, request, render_template
import xlrd
import tqdm
import bs4
from bs4 import BeautifulSoup as bs

from flask_cors import CORS

def flipkart_post(url, data, headers):
    """
    Send an HTTP POST request to the specified URL with the provided data and headers.

    Args:
        url (str): The URL to send the POST request to.
        data (dict): The data to include in the POST request, which will be converted to JSON.
        headers (dict): Headers to include in the request.

    Returns:
        tuple: A tuple containing two elements:
            1. dict: The JSON response received from the server.
            2. dict: A dictionary of cookies received in the response.

    Raises:
        requests.exceptions.RequestException: If the request fails or times out.
    """
    response = requests.post(url, data=json.dumps(data), headers=headers, timeout=999)
    return json.loads(response.text)

def display_title_price(url):
    done = False
    tries = 10
    while not done and tries > 0:
        r = requests.post(url, timeout=999)
        soup = bs(r.content, 'html.parser')
        price, title = -1, ''
        price_soup = soup.find('div', attrs={"class": "_16Jk6d"})
        if price_soup is not None:
            price = price_soup.text
            price_without_rs = price[1:]
            price_without_comma = price_without_rs.replace(",", "")
            price = int(price_without_comma)
        
        title_soup = soup.find('span', attrs={"class": "B_NuCI"})
        if title_soup is not None:
            title = title_soup.text.strip()
        
        if price_soup and title:
            done = True
        
        tries -= 1
    
    return title, price

def get_seller_from_response(response):
    keys = ['RESPONSE','data','product_seller_detail_1','data']
    sellers = []
    for key in keys:
        response = response[key] if key in response else None
        if not response:
            break
    
    if response:
        sellers = response
    return sellers
        
def process_url(pid):
    done = False
    tries = 10
    d = {}
    while not done and tries > 0:
        seller_url = "https://1.rome.api.flipkart.com/api/3/page/dynamic/product-sellers"
        data = {"requestContext":{"productId":pid},"locationContext":{}}
        header = {'X-User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 FKUA/website/42/website/Desktop'}
        response = flipkart_post(seller_url, data, header)
        url = response['RESPONSE']['data']['product_summary_1']['data'][0]['action']['url']
        url = 'https://www.flipkart.com' + url
        title, selling_price = display_title_price(url)
        d = {
            'product_name': title,
            'pid': pid,
            'url': url,
            "price": selling_price,
            'other_prices': [],
            'pax_value': None,
            'sara_value': None,
        }
        sellers = []
        sellers = get_seller_from_response(response)
        if len(sellers) == 0:
            tries -= 1
            continue
        for seller in sellers:
            seller = seller['value']
            seller_name = seller['sellerInfo']['value']['name']
            price = seller['pricing']['value']['finalPrice']['value']
            d['other_prices'].append({seller_name: int(price)})

        flat_prices = {key: value for d in d['other_prices'] for key, value in d.items()}

        d['pax_value'] = flat_prices.get('paxauto', None)
        d['sara_value'] = flat_prices.get('CARJUNCTION', None)

        sorted_keys = sorted(flat_prices, key=flat_prices.get)

        d['min_seller'] = sorted_keys[0]
        d['min_price'] = flat_prices[d['min_seller']]

        if len(sorted_keys) > 1:
            d['min_seller2'] = sorted_keys[1]
            d['min_price2'] = flat_prices[d['min_seller2']]

        if d['price'] == -1:
            d['price'] = d['min_price']
        
        done = True
            
    return d

def get_listing_price():
    workbook = xlrd.open_workbook('data.xls')
    worksheet = workbook.sheet_by_index(0)
    header_row = worksheet.row_values(0)

    col_name = 'Flipkart Serial Number'
    col_index = header_row.index(col_name)
    seller_sku = 'Seller SKU Id'
    col_index2 = header_row.index(seller_sku)
    pids = []
    sku_ids = {}
    for i in range(2, worksheet.nrows):
        row = worksheet.row_values(i)
        pids.append(row[col_index])
        sku_ids[row[col_index]] = row[col_index2]
    
    pool = multiprocessing.Pool()
    #pids = pids[:10]
    data = list(tqdm.tqdm(pool.imap(process_url, pids), total=len(pids)))
    for i in range(len(data)):
        if 'pid' in data[i]:
            data[i]['sku'] = sku_ids[data[i]['pid']]
        else:
            print(f'pid missing in ', data[i])
    return data

if __name__ == '__main__':
    app = Flask(__name__)
    CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'

    @app.route('/listings', methods=['GET'])
    def listings():
        data = get_listing_price()
        #data = testData
        # data = [d for d in data if bool(d) and d['pax_value'] != None]
        
        with open("old_dump.json", "w") as outfile:
            json.dump(data, outfile)
        
        data_check = [d for d in data if 'pax_value' in d and d['pax_value'] is not None]
        data_highest = filter(lambda x: x['pax_value'] > x['min_price'], data_check)
        data_lowest = filter(lambda x: x['pax_value'] == x['min_price'], data_check)
        
        print("Total Items: ", len(data_check))
        
        return render_template(
            'listings.html',
            data=list(data_highest),
            data_lowest=data_lowest
        )
        
    @app.route('/listings_sara', methods=['GET'])
    def listings_sara():
        data = get_listing_price()
        #data = testData
        # data = [d for d in data if bool(d) and d['pax_value'] != None]
        
        with open("old_dump.json", "w") as outfile:
            json.dump(data, outfile)
        
        data_check = [d for d in data if 'sara_value' in d and d['sara_value'] is not None]
        data_highest = filter(lambda x: x['sara_value'] > x['min_price'], data_check)
        data_lowest = filter(lambda x: x['sara_value'] == x['min_price'], data_check)
        
        print("Total Items: ", len(data_check))
        
        return render_template(
            'listings_sara.html',
            data=list(data_highest),
            data_lowest=data_lowest
        )

    @app.route('/listings_old', methods=['GET'])
    def listings_old():
        f = open('old_dump.json')
        data = json.load(f)
        data_check = [d for d in data if 'pax_value' in d and d['pax_value'] is not None]
        data_highest = filter(lambda x: x['pax_value'] > x['min_price'], data_check)
        data_lowest = filter(lambda x: x['pax_value'] == x['min_price'], data_check)
        
        print("Total Items: ", len(data_check))
        
        return render_template(
            'listings.html',
            data=list(data_highest),
            data_lowest=data_lowest
        )
    
    @app.route('/listings_sara_old', methods=['GET'])
    def listings_sara_old():
        f = open('old_dump.json')
        data = json.load(f)
        data_check = [d for d in data if 'sara_value' in d and d['sara_value'] is not None]
        data_highest = filter(lambda x: x['sara_value'] > x['min_price'], data_check)
        data_lowest = filter(lambda x: x['sara_value'] == x['min_price'], data_check)
        
        print("Total Items: ", len(data_check))
        
        return render_template(
            'listings.html',
            data=list(data_highest),
            data_lowest=data_lowest
        )
    
    app.run(debug=True, port=8000)
    