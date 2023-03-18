import os
import re
import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

from flipkartScraper import fetchFlipkartData
chromedriver_autoinstaller.install()

url = 'https://www.flipkart.com/paxauto-exterior-fancy-accessories-hybrid-kit-maruti-eeco-2018-onwards-chrome-front-garnish/p/itmfb1ce4ae4a003?pid=CGAGMC5QURQSVEPN'
listingUrl = 'https://seller.flipkart.com/index.html#dashboard/addListings/single?brand=paxauto&vertical=car_garnish'

detailFetch = 'https://flipkart.dvishal485.workers.dev/product/dl/'
tempData = {
    "name": "paxauto Exterior Fancy Accessories Hybrid Kit For MARUTI EECO 2018 ONWARDS Chrome Maruti Eeco Front Garnishpaxauto Exterior Fancy Accessories Hybrid Kit For MARUTI EECO 2018 ONWARDS Chrome Maruti Eeco Front Garnish",
    "current_price": 3520,
    "original_price": 5080,
    "discounted": True,
    "discount_percent": 30,
    "rating": None,
    "in_stock": True,
    "f_assured": False,
    "share_url": "https://dl.flipkart.com/dl/paxauto-exterior-fancy-accessories-hybrid-kit-maruti-eeco-2018-onwards-chrome-front-garnish/p/itmfb1ce4ae4a003",
    "seller": {
        "seller_name": "paxauto",
        "seller_rating": None
    },
    "thumbnails": [],
    "highlights": [
        "Type: Front",
        "Material: Fiber",
        "Finish: Chrome",
        "Color: Black"
    ],
    "product_id": "CGAGMC5QURQSVEPN",
    "offers": [],
    "specs": [
        {
            "title": "In The Box",
            "details": [
                {
                    "property": "Sales Package",
                    "value": "EECO 2018 ONWARDS Hybrid black finish combo kit"
                },
                {
                    "property": "Description",
                    "value": "Tata Punch 2022 Hybrid black finish combo kit\n\nGet this 5 Pes Hybrid Black Kit designed exclusively for your Tata Punch 2022. \nautomotive and will give your car a fresh look. This EECO 2018 ONWARDS Black Kit model contains items like Tail Light, Finger\nGuard, Headlight Cover, Mirror Cover, Door Catch Cover, Ete. The product has a 100 percent fitment"
                },
                {
                    "property": "Images",
                    "value": [
                        "https://rukminim1.flixcart.com/image/xif0q/car-garnish/w/g/b/exterior-fancy-accessories-hybrid-kit-for-maruti-eeco-2018-original-imagmc5qxcgqcksy.jpeg?q=70",
                        "https://rukminim1.flixcart.com/image/xif0q/car-garnish/w/g/b/exterior-fancy-accessories-hybrid-kit-for-maruti-eeco-2018-original-imagmc5qxcgqcksy.jpeg?q=70"
                    ]
                }
            ]
        },
        {
            "title": "General",
            "details": [
                {
                    "property": "Brand",
                    "value": "paxauto"
                },
                {
                    "property": "Model Number",
                    "value": "Exterior Fancy Accessories Hybrid Kit For MARUTI EECO 2018 ONWARDS"
                },
                {
                    "property": "Type",
                    "value": "Front"
                },
                {
                    "property": "Material",
                    "value": "Fiber"
                },
                {
                    "property": "Finish",
                    "value": "Chrome"
                },
                {
                    "property": "Vehicle Brand",
                    "value": "Maruti"
                },
                {
                    "property": "Vehicle Model Name",
                    "value": "Eeco"
                },
                {
                    "property": "Vehicle Model Year",
                    "value": "2018"
                },
                {
                    "property": "Color",
                    "value": "Black"
                },
                {
                    "property": "Installation Type",
                    "value": "Easy to Install"
                }
            ]
        },
        {
            "title": "Additional Features",
            "details": [
                {
                    "property": "Other Features",
                    "value": "Compatibility- EECO 2018 ONWARDS Models, Quantity- Hybrid Black Combo kit of 5 Pes., Position: Tail Light, Finger Guard, Headlight Cover, Mirror Cover, Door Catch Cover, Petrol tank cover"
                }
            ]
        }
    ]
}
def fetchProductData(url):
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
    return data

isLoggedIn = False
index = 0

opt = webdriver.ChromeOptions()
opt.add_argument("--start-maximized")
#opt.add_argument("user-data-dir=.\\browserData")
opt.add_experimental_option("detach", True)

driver = None

def openAndFill(data, user, passw):
    global isLoggedIn
    global driver
    global index
    
    if isLoggedIn:
        driver.execute_script(f"window.open('{listingUrl}')")
        print(driver.window_handles)
        driver.switch_to.window(driver.window_handles[index])
    else:
        driver = webdriver.Chrome(options=opt)
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
        editFields = driver.find_elements(By.XPATH, ".//*[contains(@class, 'styles__Card')]")
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
            fname = field.find_element(By.XPATH, ".//*[contains(@class, 'styles__Title')]").text
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
                    inp = field.find_element(By.XPATH, ".//input[@id='upload-image']")
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
                btn = field.find_element(By.XPATH, ".//*[contains(@class, 'styles__RotatingBorder')]")
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
                inputs = field.find_elements(By.XPATH, ".//*[contains(@class, 'styles__FocusWrapper')]")
                for inp in inputs:
                    try:
                        label = inp.find_element(By.XPATH, ".//*[contains(@class, 'styles__AttributeItemLabelName')]")
                        prop = [detailMap[key] for key in detailMap if label.text.replace('*', '').strip() == key]
                        if len(prop) == 1:
                            print(label.text, prop[0])
                            try:
                                ff = inp.find_element(By.XPATH, ".//input[contains(@class, 'styles__StyledInput')]")
                                ff.send_keys(prop[0])
                            except:
                                try:
                                    ff = inp.find_element(By.XPATH, ".//select[contains(@class, 'styles__StyledSelect')]")
                                    ff.send_keys(prop[0])
                                except:
                                    ff = inp.find_element(By.TAG_NAME, "textarea")
                                    ff.send_keys(prop[0])
                    except:
                        pass
                WebDriverWait(field, 10).until(
                    EC.element_to_be_clickable((By.XPATH, ".//*[contains(@class, 'styles__RotatingBorder')]")))
                btn = field.find_element(By.XPATH, ".//*[contains(@class, 'styles__RotatingBorder')]")
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

#productData = fetchProductData(url)
#print(json.dumps(productData, indent=4))
openAndFill(tempData, '8920846489', 'pokemon@66')