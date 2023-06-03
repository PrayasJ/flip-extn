import sys
import time
import xlrd
import tqdm
import multiprocessing
import chromedriver_autoinstaller
from selenium import webdriver
import requests
import json

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

class LocalStorage:

    def __init__(self, driver) :
        self.driver = driver

    def __len__(self):
        return self.driver.execute_script("return window.localStorage.length;")

    def items(self) :
        return self.driver.execute_script( \
            "var ls = window.localStorage, items = {}; " \
            "for (var i = 0, k; i < ls.length; ++i) " \
            "  items[k = ls.key(i)] = ls.getItem(k); " \
            "return items; ")

    def keys(self) :
        return self.driver.execute_script( \
            "var ls = window.localStorage, keys = []; " \
            "for (var i = 0; i < ls.length; ++i) " \
            "  keys[i] = ls.key(i); " \
            "return keys; ")

    def get(self, key):
        return self.driver.execute_script("return window.localStorage.getItem(arguments[0]);", key)

    def set(self, key, value):
        self.driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def has(self, key):
        return key in self.keys()

    def remove(self, key):
        self.driver.execute_script("window.localStorage.removeItem(arguments[0]);", key)

    def clear(self):
        self.driver.execute_script("window.localStorage.clear();")

    def __getitem__(self, key) :
        value = self.get(key)
        if value is None :
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
    'Product Title', 'MRP' ,'Your Selling Price', 'Procurement SLA',
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

def process_item(data):
    global driver
    #listingUrl = f'https://seller.flipkart.com/index.html#dashboard/addListings/single?brand={data["details"]["brand"]}&vertical={data["Sub-category"]}'
    listingUrl = f'https://seller.flipkart.com/index.html#dashboard/listings/product/na?fsn={data["Flipkart Serial Number".lower()]}'
    driver.get(listingUrl)
    try:
        element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'ReactModal__Overlay')))
        driver.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
            """, element)
        try:
            element = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Last']")))
            element.click()
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)
    try:
        already_selling = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alreadySelling')))
        return False
    except Exception as e:
        print('Creating new mapping!')
    try:
        start_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'startSelling')))
        start_button.click()
        fields = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'entity-container')))
        for field in fields:
            key = field.find_element(By.CLASS_NAME, 'entity-info')
            key = key.text.strip().lower()
            if key == 'length':
                key = 'Package Length - Length of the package in cms'.lower()
            elif key == 'breadth':
                key = 'Package Breadth - Breadth of the package in cms'.lower()
            elif key == 'height':
                key = 'Package Height - Height of the package in cms'.lower()
            elif key == 'weight':
                key = 'Package Weight - Weight of the package in Kgs'.lower()
            elif key == 'hsn':
                key = 'Harmonized System Nomenclature - HSN'.lower()
            if key in data:
                inp = field.find_element(By.CLASS_NAME, 'entity-field')
                try:
                    inp = inp.find_element(By.TAG_NAME, 'input')
                except WebDriverException:
                    try:
                      inp = inp.find_element(By.TAG_NAME, 'textarea')
                    except WebDriverException:
                        try: 
                           inp = inp.find_element(By.TAG_NAME, 'select')
                        except WebDriverException: 
                            print(f'cant find input for {key}') 
                # driver.execute_script("arguments[0].scrollIntoView();", inp)
                # driver.execute_script("arguments[0].click();", inp)
                inp.send_keys(data[key])
                if inp.get_attribute('value') == '':
                    inp.send_keys(data[key])
            else:
                print(f'\'{key}\' not found :(')
        
        confirm_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'confirm-button-text')))
        print(confirm_button)
    except Exception as e:
        print(e)

dataKeys = {
    'Flipkart Serial Number': 'productId', 
    'Sub-category': '', 
    'Seller SKU Id': 'sku_id', 
    'Product Title': '',
    'MRP': 'mrp' ,
    'Your Selling Price': 'flipkart_selling_price',
    'Procurement SLA': 'shipping_days',    
    # 'Procurement Type': 'procurement_type', 
    'Package Length - Length of the package in cms': 'length',
    'Package Breadth - Breadth of the package in cms': 'breadth', 
    'Package Height - Height of the package in cms': 'height',
    'Package Weight - Weight of the package in Kgs': 'weight', 
    'Harmonized System Nomenclature - HSN': 'hsn',
    'Tax Code': 'tax_code', 
    'Country of Origin ISO code': 'country_of_origin', 
    'Listing Status': 'listing_status',
    'seller_brand': 'manufacturer_details',
    'seller_id': 'sellerId',
    'headers': 'headers'
}

data_template = {
    "bulkRequests": [
        {
            "attributeValues": {
                "sku_id": [
                    {
                        "value": "LED Splendor Light",
                        "qualifier": ""
                    }
                ],
                "listing_status": [
                    {
                        "value": "ACTIVE",
                        "qualifier": ""
                    }
                ],
                "mrp": [
                    {
                        "value": "1299",
                        "qualifier": "INR"
                    }
                ],
                "flipkart_selling_price": [
                    {
                        "value": "562",
                        "qualifier": "INR"
                    }
                ],
                "service_profile": [
                    {
                        "value": "NON_FBF",
                        "qualifier": ""
                    }
                ],
                "procurement_type": [
                    {
                        "value": "EXPRESS",
                        "qualifier": ""
                    }
                ],
                "shipping_days": [
                    {
                        "value": "1.0",
                        "qualifier": ""
                    }
                ],
                "stock_size": [
                    {
                        "value": "1000",
                        "qualifier": ""
                    }
                ],
                "shipping_provider": [
                    {
                        "qualifier": "",
                        "value": "FLIPKART"
                    }
                ],
                "local_shipping_fee_from_buyer": [
                    {
                        "value": "0",
                        "qualifier": "INR"
                    }
                ],
                "zonal_shipping_fee_from_buyer": [
                    {
                        "value": "0",
                        "qualifier": "INR"
                    }
                ],
                "national_shipping_fee_from_buyer": [
                    {
                        "value": "0",
                        "qualifier": "INR"
                    }
                ],
                "hsn": [
                    {
                        "value": "8512",
                        "qualifier": ""
                    }
                ],
                "luxury_cess": [
                    {
                        "value": "0",
                        "qualifier": "PERCENTAGE"
                    }
                ],
                "tax_code": [
                    {
                        "value": "GST_18",
                        "qualifier": ""
                    }
                ],
                "country_of_origin": [
                    {
                        "value": "IN",
                        "qualifier": ""
                    }
                ],
                "manufacturer_details": [
                    {
                        "value": "CARJUNCTION",
                        "qualifier": ""
                    }
                ],
                "packer_details": [
                    {
                        "value": "CARJUNCTION",
                        "qualifier": ""
                    }
                ]
            },
            "productId": "HLUGBAGBHX7VDCQZ",
            "skuId": "LED Splendor Light",
            "packages": [
                {
                    "id": {
                        "value": "packages-0"
                    },
                    "length": {
                        "value": "12.0",
                        "qualifier": "CM"
                    },
                    "breadth": {
                        "value": "12.0",
                        "qualifier": "CM"
                    },
                    "height": {
                        "value": "12.0",
                        "qualifier": "CM"
                    },
                    "weight": {
                        "value": "0.4",
                        "qualifier": "KG"
                    },
                    "sku_id": {
                        "value": "LED Splendor Light",
                        "qualifier": ""
                    }
                }
            ]
        }
    ],
    "sellerId": "8074129009f74a0c"
}   

def alreadySelling(item):
    response = requests.get(f'https://seller.flipkart.com/napi/listing/searchProduct?fsnSearch={item["Flipkart Serial Number"]}&sellerId={item["seller_id"]}', headers=item['headers'])
    is_product = json.loads(response.text)
    if len(is_product['result']['productList']) == 0:
        return -1
    return is_product['result']['productList'][0]['alreadySelling']

def process_item2(item):
    global data_template
    data = data_template.copy()
    for key in item:
        key_data = dataKeys[key]
        if key_data in data['bulkRequests'][0]['attributeValues']:
            data['bulkRequests'][0]['attributeValues'][key_data][0]['value'] = str(item[key])
        if key_data in data['bulkRequests'][0]['packages'][0]:
            data['bulkRequests'][0]['packages'][0][key_data]['value'] = str(item[key])
    data['bulkRequests'][0]['productId'] = item['Flipkart Serial Number']
    data['bulkRequests'][0]['skuId'] = item['Seller SKU Id']
    data['sellerId'] = item['seller_id']

    response = requests.post(f'https://seller.flipkart.com/napi/listing/create-update-listings?sellerId={item["seller_id"]}', data=json.dumps(data), headers=item['headers'])
    result = json.loads(response.text)
    if result['result']['status'] != 'success':
        print('failed to update/add')
        print(item) 
    
def bulkMap(user, passw):
    workbook = xlrd.open_workbook('data.xls')
    worksheet = workbook.sheet_by_index(0)
    header_row = worksheet.row_values(0)

    dataKeyMap = {}
    for key in dataKeys:
        try:
            dataKeyMap[key] = header_row.index(key)
        except:
            pass

    rowCount = worksheet.nrows
    
    data = []
    
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
    
    for i in range(2, rowCount):
        row = worksheet.row_values(i)
        item = {key: row[dataKeyMap[key]] for key in dataKeyMap}

        item['Your Selling Price'] = int(int(item['Your Selling Price']) * 1.1)
        item['seller_brand'] = 'CARJUNCTION'
        item['seller_id'] = seller_id
        item['headers'] = headers
        data.append(item)
    count = 0
    notSelling = []
    print(f'Going over {rowCount} products to check how many are being listed...')
    for item in data:
        is_selling = alreadySelling(item)
        if is_selling is False:
            notSelling.append(item)

    rowCount = len(notSelling)
    print(f'Not selling {rowCount} products.')
    for item in notSelling:
        count += 1
        print(f'Processing {count}/{rowCount}')
        process_item2(item)
        time.sleep(1)

bulkMap(sys.argv[1], sys.argv[2])
