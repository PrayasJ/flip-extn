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

def bulkRTD(user, passw):
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
    #status='shipments_to_handover' for final 'shipments_to_pack' for first and 'shipments_to_dispatch' for label
    data = {"status":"shipments_to_dispatch","payload":{"pagination":{"page_num":1,"page_size":2000},"params":{}}}
    response = requests.post(
        f'https://seller.flipkart.com/napi/my-orders/fetch?sellerId={seller_id}', headers=headers, data=json.dumps(data))
    
    result = json.loads(response.text)
    items = result['items']
    
    totalCount = len(items)
    n = 160
    
    pdf_merger = PyPDF2.PdfFileMerger()
    
    items = [d['id'] for d in items]
    
    download_chunks = [items[i:i+n] for i in range(0, len(items), n)]
    for chunk in download_chunks:
        items_string = '%2C'.join(chunk)
        request_url = f'https://seller.flipkart.com/napi/my-orders/reprint_labels?shipmentIds={items_string}'
        response = requests.get(request_url, headers=headers)

        if response.status_code == 200:
            pdf_bytes = BytesIO(response.content)
            pdf_merger.append(PyPDF2.PdfFileReader(pdf_bytes))
            print(f'downloaded {len(chunk)} labels!')
        else:
            print(response.text)
            print("Error: Could not download file")
    
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    filename = f"{date_string}_merged.pdf"
    filepath = os.path.join(downloads_path, filename)

    with open(filepath, 'wb') as f:
        pdf_merger.write(f)

    print(f"Files merged and saved as '{filename}' in Downloads folder")
    while totalCount > 0:
        print(f'{totalCount} left')
        item_chunks = [items[i:i+n] for i in range(0, len(items), n)]
        items = []
        for data in item_chunks:
            response = requests.post(f'https://seller.flipkart.com/napi/shipments/rtsV2?sellerId={seller_id}', headers=headers, data=json.dumps(data))
            response = json.loads(response.text)
            print(response)
            tempItems = []
            for i in range(len(response)):
                if response[i]['succeeded'] is False:
                    if 'shipmentId' in response[i]:
                        tempItems.append(data[i])
                    elif response[i]['errorReponse']['code'] == 'TOO_MANY_REQUESTS':
                        tempItems.append(data[i])
                    else:
                        print(response[i])
                        print('Couldnt resolve')
                
            items =  items + tempItems
            time.sleep(1)
        totalCount = len(items)


bulkRTD(sys.argv[1], sys.argv[2])
