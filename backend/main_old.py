from flipkartScraper import fetchFlipkartData
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import requests
import time
import re
import os
import json
import sys
from flask import Flask, request, render_template
import xlrd
import tqdm
import multiprocessing
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from flask_cors import CORS, cross_origin

if __name__ == '__main__':
    ChromeDriverManager().install()

fixedData = {
    'Listing Status': 'Active',
    'Fullfilment by': 'Seller',
    'Procurement type': 'Express',
    'Procurement SLA': '1',
    'Stock': '1000',
    'Local delivery charge': '0',
    'Zonal delivery charge': '0',
    'National delivery charge': '0',
    'Package Weight': '0.6',
    'Package Length': '12',
    'Package Breadth': '12',
    'Package Height': '12',
    'HSN': '8708',
    'Tax Code': 'GST_28',
    'Country of Origin': 'India',
    'Manufacturer Details': 'Pax Automobile',
    'Packer Details': 'Pax Automobile',
    'Shipping provider': 'Flipkart'
}

url = 'https://www.flipkart.com/paxauto-exterior-fancy-accessories-hybrid-kit-maruti-eeco-2018-onwards-chrome-front-garnish/p/itmfb1ce4ae4a003?pid=CGAGMC5QURQSVEPN'

# fog_lamp_unit =
# car_garnish
detailFetch = 'https://flipkart.dvishal485.workers.dev/product/dl/'

isLoggedIn = False
index = 0
opt = webdriver.ChromeOptions()
opt.add_experimental_option('excludeSwitches', ['enable-logging'])
opt.add_argument("--start-maximized")
opt.add_argument("user-data-dir=.\\browserData")
opt.add_experimental_option("detach", True)

driver = None

def fetchProductData(url):
    global fixedData
    uid = url.split('flipkart.')
    uid = uid[1].split('/')
    uid = '/'.join(uid[1:])
    data = requests.get(f'{detailFetch}{uid}')
    extData = fetchFlipkartData(url)
    data = data.json()
    for key in extData:
        data['specs'][0]['details'].append({
            "property": key,
            "value": extData[key]
        })
    for key in fixedData:
        data['specs'][0]['details'].append({
            "property": key,
            "value": fixedData[key]
        })
    return data


def openAndFill(data, vertical, user, passw):
    global isLoggedIn
    global driver
    global index
    listingUrl = f'https://seller.flipkart.com/index.html#dashboard/addListings/single?brand=paxauto&vertical={vertical}'
    if isLoggedIn:
        driver.execute_script(f"window.open('{listingUrl}')")
        print(driver.window_handles)
        driver.switch_to.window(driver.window_handles[index])
    else:
        driver = webdriver.Chrome(options=opt, service=ChromeService(ChromeDriverManager().install()))
        # driver = webdriver.Chrome(options=opt, executable_path='./chromedriver/chromedriver')
        driver.get(listingUrl)
    index += 1
    detailMap = {}
    for __ in data["specs"]:
        for _ in __['details']:
            if _['property'] == 'Brand':
                continue
            detailMap[_['property']] = _['value']
    detailMap['MRP'] = data['original_price']
    detailMap['Your selling price'] = data['current_price']
    if not isLoggedIn:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, 'username')))
            element.send_keys(user)
            modal = driver.find_element(By.CLASS_NAME, 'modal-body-section')
            btn = modal.find_element(By.TAG_NAME, 'button')
            btn.click()
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, 'password')))

            element.send_keys(passw)
            modal = driver.find_element(By.CLASS_NAME, 'modal-body-section')
            btn = modal.find_element(By.TAG_NAME, 'button')
            btn.click()
        except Exception as e:
            print(e)
        finally:
            print('logged in')
            isLoggedIn = True
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
    finally:
        btn = driver.find_element(By.XPATH, "//*[text()='Create New Listing']")
        btn.click()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, ".//*[contains(@class, 'styles__Card')]")))
        editFields = driver.find_elements(
            By.XPATH, ".//*[contains(@class, 'styles__Card')]")
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'styles__ProductCreationFixedSection')]")))
            driver.execute_script("""
                var element = arguments[0];
                element.parentNode.removeChild(element);
                """, element)
        except:
            pass
        for field in editFields:
            fname = field.find_element(
                By.XPATH, ".//*[contains(@class, 'styles__Title')]").text
            if 'Product Photos' in fname:
                print('In ', fname)
                WebDriverWait(field, 10).until(
                    EC.element_to_be_clickable((By.XPATH, ".//button[text()='EDIT']")))
                btn = field.find_element(By.XPATH, ".//button[text()='EDIT']")
                print(btn.text)
                btn.click()
                for i in range(len(detailMap['Images'])):
                    img_url = detailMap['Images'][i]
                    WebDriverWait(field, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f".//*[@id='thumbnail_{i}']"))).click()
                    WebDriverWait(field, 10).until(
                        EC.element_to_be_clickable((By.XPATH, ".//span[text()='Upload Photo']")))
                    inp = field.find_element(
                        By.XPATH, ".//input[@id='upload-image']")
                    picture_req = requests.get(img_url)
                    if picture_req.status_code == 200:
                        print(picture_req.headers)
                        d = picture_req.headers['Content-Type'].split('/')
                        fname = time.strftime("%Y%m%d-%H%M%S") + '.' + d[-1]
                        print(fname)
                        with open(f"./temp/{fname}", 'wb') as f:
                            f.write(picture_req.content)
                        inp.send_keys(f"{os.getcwd()}/temp/{fname}")
                        time.sleep(1)
                WebDriverWait(field, 10).until(
                    EC.element_to_be_clickable((By.XPATH, ".//*[contains(@class, 'styles__RotatingBorder')]")))
                btn = field.find_element(
                    By.XPATH, ".//*[contains(@class, 'styles__RotatingBorder')]")
                print(btn.text)
                btn.click()
                try:
                    elem = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'styles__ProductErrorSidebar')]")))
                    driver.execute_script("""
                    var element = arguments[0];
                    element.parentNode.removeChild(element);
                    """, elem)
                except:
                    pass
            if 'Product Description' in fname or 'Additional Description' in fname or 'Price, Stock and Shipping Information' in fname:
                print('In ', fname)
                WebDriverWait(field, 10).until(
                    EC.element_to_be_clickable((By.XPATH, ".//button[text()='EDIT']")))
                btn = field.find_element(By.XPATH, ".//button[text()='EDIT']")
                print(btn.text)
                btn.click()
                WebDriverWait(field, 10).until(
                    EC.element_to_be_clickable((By.XPATH, ".//*[contains(@class, 'styles__FocusWrapper')]")))
                inputs = field.find_elements(
                    By.XPATH, ".//*[contains(@class, 'styles__FocusWrapper')]")
                for inp in inputs:
                    try:
                        label = inp.find_element(
                            By.XPATH, ".//*[contains(@class, 'styles__AttributeItemLabelName')]")
                        prop = [detailMap[key] for key in detailMap if label.text.replace(
                            '*', '').strip() == key]
                        if len(prop) == 1:
                            print(label.text, prop[0])
                            try:
                                ff = inp.find_element(
                                    By.XPATH, ".//input[contains(@class, 'styles__StyledInput')]")
                                ff.send_keys(prop[0])
                            except:
                                try:
                                    ff = inp.find_element(
                                        By.XPATH, ".//select[contains(@class, 'styles__StyledSelect')]")
                                    ff.send_keys(prop[0])
                                except:
                                    ff = inp.find_element(
                                        By.TAG_NAME, "textarea")
                                    ff.send_keys(prop[0])
                    except:
                        pass
                WebDriverWait(field, 10).until(
                    EC.element_to_be_clickable((By.XPATH, ".//*[contains(@class, 'styles__RotatingBorder')]")))
                btn = field.find_element(
                    By.XPATH, ".//*[contains(@class, 'styles__RotatingBorder')]")
                print(btn.text)
                btn.click()
                try:
                    elem = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'styles__ProductErrorSidebar')]")))
                    driver.execute_script("""
                    var element = arguments[0];
                    element.parentNode.removeChild(element);
                    """, elem)
                except:
                    pass

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('start-maximized')
options.add_argument('disable-infobars')
options.add_argument("--disable-extensions")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver2 = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))
# driver2 = webdriver.Chrome(options=options, executable_path='./chromedriver/chromedriver')

def process_url(pid):
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
        print(d['other_prices'])
        d['pax_value'] = next((x["paxauto"] for x in d['other_prices'] if "paxauto" in x), None)
        d['sara_value'] = next((x["CARJUNCTION"] for x in d['other_prices'] if "CARJUNCTION" in x), None)
        d['min_seller'] = key
        d['min_price'] = value
        if len(d['other_prices']) > 1: 
            second_min_dict = sorted(d['other_prices'], key=lambda x: float(list(x.values())[0].replace(',', '')[1:]))[1]
            key2, value2 = list(second_min_dict.items())[0]
            d['min_seller2'] = key2
            d['min_price2'] = value2
    except Exception as e:
        print(f'Couldnt process {seller_url}')
        d = {}
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
    
    @app.route('/', methods=['POST'])
    def hello_world():
        tab = request.json['tab']
        vertical = request.json['vertical']
        print(f'Tab visited from is {tab}, vertical={vertical}!')
        productData = fetchProductData(tab)
        openAndFill(productData, vertical, sys.argv[1], sys.argv[2])
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

    @app.route('/listings', methods=['GET'])
    def listings():
        data = get_listing_price()
        #data = testData
        data = [d for d in data if bool(d) and d['pax_value'] != None]
        
        with open("old_dump.json", "w") as outfile:
            json.dump(data, outfile)
        print("Total Items: ", len(data))
        
        data_highest = filter(lambda x: int(x['pax_value'][1:].replace(',', '')) > int(x['min_price'][1:].replace(',', '')), data)
        
        data_lowest = filter(lambda x: int(x['pax_value'][1:].replace(',', '')) == int(x['min_price'][1:].replace(',', '')), data)
        
        print("Total Items: ", len(data))
        
        return render_template(
            'listings.html',
            data=list(data_highest),
            data_lowest=data_lowest
        )
        
    @app.route('/listings_sara', methods=['GET'])
    def listings_sara():
        data = get_listing_price()
        #data = testData
        data = [d for d in data if bool(d) and d['sara_value'] != None]
        
        with open("old_dump.json", "w") as outfile:
            json.dump(data, outfile)
        print("Total Items: ", len(data))
        
        data_highest = filter(lambda x: int(x['sara_value'][1:].replace(',', '')) > int(x['min_price'][1:].replace(',', '')), data)
        
        data_lowest = filter(lambda x: int(x['sara_value'][1:].replace(',', '')) == int(x['min_price'][1:].replace(',', '')), data)
        
        print("Total Items: ", len(data))
        
        return render_template(
            'listings_sara.html',
            data=list(data_highest),
            data_lowest=data_lowest
        )

    @app.route('/listings_old', methods=['GET'])
    def listings_old():
        f = open('old_dump.json')
        data = json.load(f)
        data = [d for d in data if bool(d) and d['pax_value'] != None and 'min_price2' in d]
        
        data_highest = filter(lambda x: int(x['pax_value'][1:].replace(',', '')) > int(x['min_price'][1:].replace(',', '')), data)
        
        data_lowest = filter(lambda x: int(x['pax_value'][1:].replace(',', '')) == int(x['min_price'][1:].replace(',', '')), data)
        
        print("Total Items: ", len(data))
        
        return render_template(
            'listings.html',
            data=list(data_highest),
            data_lowest=data_lowest
        )
    
    app.run(debug=True, port=8000)
    