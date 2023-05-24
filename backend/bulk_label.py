import sys
import time
import xlrd
import tqdm
import multiprocessing
import chromedriver_autoinstaller
from selenium import webdriver
import requests
import json
from datetime import datetime
import os
import PyPDF2
from io import BytesIO

from datetime import datetime, timedelta
import pytz

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

downloads_path = os.path.expanduser("~/Downloads")

class LocalStorage:

    def __init__(self, driver):
        self.driver = driver

    def __len__(self):
        return self.driver.execute_script("return window.localStorage.length;")

    def items(self):
        return self.driver.execute_script(
            "var ls = window.localStorage, items = {}; "
            "for (var i = 0, k; i < ls.length; ++i) "
            "  items[k = ls.key(i)] = ls.getItem(k); "
            "return items; ")

    def keys(self):
        return self.driver.execute_script(
            "var ls = window.localStorage, keys = []; "
            "for (var i = 0; i < ls.length; ++i) "
            "  keys[i] = ls.key(i); "
            "return keys; ")

    def get(self, key):
        return self.driver.execute_script("return window.localStorage.getItem(arguments[0]);", key)

    def set(self, key, value):
        self.driver.execute_script(
            "window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def has(self, key):
        return key in self.keys()

    def remove(self, key):
        self.driver.execute_script(
            "window.localStorage.removeItem(arguments[0]);", key)

    def clear(self):
        self.driver.execute_script("window.localStorage.clear();")

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        return key in self.keys()

    def __iter__(self):
        return self.items().__iter__()

    def __repr__(self):
        return self.items().__str__()


dataKeys = [
    'Flipkart Serial Number', 'Sub-category', 'Seller SKU Id',
    'Product Title', 'MRP', 'Your Selling Price', 'Procurement SLA',
    'Procurement Type', 'Package Length - Length of the package in cms',
    'Package Breadth - Breadth of the package in cms', 'Package Height - Height of the package in cms',
    'Package Weight - Weight of the package in Kgs', 'Harmonized System Nomenclature - HSN',
    'Tax Code', 'Country of Origin ISO code', 'Listing Status'
]

if __name__ == '__main__':
    chromedriver_autoinstaller.install()

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('start-maximized')
options.add_argument('disable-infobars')
options.add_argument("--disable-extensions")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
# options.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=options)

def bulkLabel(user, passw):
    loginUrl = 'https://seller.flipkart.com/index.html#dashboard'
    driver.get(loginUrl)
    print('Logging in...')
    try:
        print('Filling username...')
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, 'username')))
        element.send_keys(user)
        modal = driver.find_element(By.CLASS_NAME, 'modal-body-section')
        btn = modal.find_element(By.TAG_NAME, 'button')
        btn.click()
        print('Filling password...')
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, 'password')))

        element.send_keys(passw)
        print('Submitting...')
        modal = driver.find_element(By.CLASS_NAME, 'modal-body-section')
        btn = modal.find_element(By.TAG_NAME, 'button')
        btn.click()
    except Exception as e:
        print(e)

    time.sleep(1)
    print('Logged in!')
    storage = LocalStorage(driver)
    app_data = json.loads(storage['__appData'])
    cookies = driver.get_cookies()
    headers = {
        'Cookie': '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies]),
        'Content-Type': 'application/json',
        'fk-csrf-token': app_data['sellerConfig']['csrfToken']
    }

    seller_id = app_data['sellerConfig']['sellerId']
    response = requests.get(
        'https://seller.flipkart.com/napi/get-locations?locationType=pickup&include=state', headers=headers)
    result = json.loads(response.text)
    location_id = result['result']['multiLocationList'][0]['locationId']
    
    current_datetime = datetime.now(pytz.utc)
    timezone_offset = timedelta(hours=5, minutes=30)
    current_datetime_with_offset = current_datetime + timezone_offset

    formatted_datetime = current_datetime_with_offset.strftime("%Y-%m-%dT%H:%M:%S.000%z")
    #status='shipments_to_handover' for final 'shipments_to_pack' for first and 'shipments_to_dispatch' for label
    data = {"status":"shipments_to_pack","payload":{"pagination":{"page_num":1,"page_size":1000},"params":{"dispatch_after_date":{"to":formatted_datetime}}}}
    response = requests.post(
        f'https://seller.flipkart.com/napi/my-orders/fetch?sellerId={seller_id}', headers=headers, data=json.dumps(data))
    
    result = json.loads(response.text)
    items = result['items']
    
    n = 160
    
    data_blocks = []
    
    for item in items:
        if 'order_items' not in item or len(item['order_items']) > 1 or item['order_items'][0]['quantity'] > 1:
            continue
        data_template = {
                "id": item['id'],
                "invoice": {
                    "items": [
                        {
                            "order_item_id": item['order_items'][0]['order_item_id'],
                            "purchase_price": None,
                            "quantity": 1
                        }
                    ]
                },
                "serialized_items": [
                    {
                        "order_item_id": item['order_items'][0]['order_item_id'],
                        "serial_numbers": []
                    }
                ],
                "dimensions": [
                    {
                        "breadth": item['sub_shipments'][0]['packages'][0]['dimensions']['breadth'],
                        "height": item['sub_shipments'][0]['packages'][0]['dimensions']['height'],
                        "length": item['sub_shipments'][0]['packages'][0]['dimensions']['length'],
                        "weight": item['sub_shipments'][0]['packages'][0]['dimensions']['weight'],
                        "external_sub_shipment_id": item['sub_shipments'][0]['external_sub_shipment_id']
                    }
                ]
            }
        data_blocks.append(data_template)
    
    totalCount = len(data_blocks)
    
    item_chunks = [data_blocks[i:i+n] for i in range(0, len(data_blocks), n)]
    count = 0
    for chunk in item_chunks:
        data = {
            "shipments": chunk,
            "sellerId": seller_id
        }
        # print(json.dumps(data))
        response = requests.post(f'https://seller.flipkart.com/napi/shipments/packV2?isCartmanValidationEnabled=true&sellerId={seller_id}', headers=headers, data=json.dumps(data))
        response = json.loads(response.text)
        
        count += len(chunk)
        print(f'processed {count}/{totalCount}')
        time.sleep(1)
    
    notDone = True
    headers['X-LOCATION-ID'] = location_id
    while notDone:
        response = requests.get(f'https://seller.flipkart.com/napi/my-orders/label-generation-status?status=in_process_orders_count&sellerId={seller_id}&serviceProfile=NON_FBF', headers=headers)
        response = json.loads(response.text)
        print(response)
        count = int(response['count'])
        if count == 0:
            notDone = False
        else:
            print(f'{count} left to process')
            response = requests.get(f'https://seller.flipkart.com/napi/orders/downloadLabelsCreatedV2?useNewTemplate=true&locationId={location_id}&sellerId={seller_id}', headers=headers)
            time.sleep(1)


bulkLabel(sys.argv[1], sys.argv[2])
