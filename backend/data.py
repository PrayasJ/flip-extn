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

def get_transaction(user, passw):
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
    
    get_transaction_history(headers)
    
def get_transaction_history(headers):
    # Parse the JSON data
    data = {"status":"shipments_delivered","payload":{"pagination":{"page_num":1,"page_size":1000},"params":{"seller_id":"5a4bc512639a4a92","approval_date":{"from":"2023-06-17T00:00:00.000+05:30","to":"2023-06-17T23:59:59.000+05:30"}}},"sellerId":"5a4bc512639a4a92"}
    response = requests.post(
        'https://seller.flipkart.com/napi/my-orders/fetch?sellerId=5a4bc512639a4a92', headers=headers, data=json.dumps(data))
    
    json_data = json.loads(response.text)

    # Extract order_item_id from each item
    order_item_ids = []
    for item in json_data["items"]:
        for order_item in item["order_items"]:
            order_item_ids.append(order_item["order_item_id"])
    with open("reward.csv", "w") as file:
        for order in order_item_ids:
            data = {"operationName":"TransactionPage_getOrderTransactionHistory","variables":{"param":order,"service_type":"orderItem"},"query":"query TransactionPage_getOrderTransactionHistory($param: String!, $service_type: String!) {\n  getOrderTransactionHistory(param: $param, service_type: $service_type) {\n    order_item_id\n    settled_settlements {\n      neft_id\n      order_item_value {\n        net_amount\n        sale_amount {\n          item_revenue\n          customer_paid_shipping_revenue\n          net_amount\n          __typename\n        }\n        total_offer {\n          free_shipping_offer\n          non_shipping_offer\n          net_amount\n          __typename\n        }\n        my_share {\n          free_shipping_offer\n          non_shipping_offer\n          net_amount\n          __typename\n        }\n        __typename\n      }\n      offer_adjustments {\n        net_amount\n        discount_base_amount\n        discount_on_mp_fees {\n          net_amount\n          actual_discount\n          item_gst_rate\n          gst_amount\n          __typename\n        }\n        __typename\n      }\n      flipkart_fees {\n        commission_fee\n        shopsy_marketing_fee\n        collection_fee\n        service_cancellation_charge\n        fixed_fee\n        fee_discount\n        cancellation_fee\n        installation_fee\n        uninstallation_fee\n        no_cost_emi_fee\n        franchise_fee\n        uninstallation_packaging_fee\n        tech_visit_fee\n        forward_shipping_fee\n        reverse_shipping_fee\n        pick_and_pack_fee\n        service_cancellation_fee\n        customer_shipping_fee_amount\n        customer_shipping_fee_type\n        net_amount\n        __typename\n      }\n      taxes {\n        net_amount\n        gst {\n          net_amount\n          tax_details {\n            fee_type\n            net_tax_rule_value\n            net_amount\n            tax_group {\n              tax_group\n              base_amount\n              net_amount\n              net_tax_rule_value\n              tax_detail {\n                tax_type\n                tax_value\n                rule_name\n                rule_value\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        tds {\n          tax_group\n          base_amount\n          net_amount\n          net_tax_rule_value\n          tax_detail {\n            tax_type\n            tax_value\n            rule_name\n            rule_value\n            __typename\n          }\n          __typename\n        }\n        tcs {\n          tax_group\n          base_amount\n          net_amount\n          net_tax_rule_value\n          tax_detail {\n            tax_type\n            tax_value\n            rule_name\n            rule_value\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      net_amount\n      input_gst_credits\n      income_tax_credits\n      payment_type\n      adjustment_reasons {\n        reason\n        subreason\n        __typename\n      }\n      settlement_date\n      refund_amount\n      protection_fund\n      reward_amount\n      adjustments\n      customer_shipping_amount\n      customer_shipping_type\n      incentives\n      lockin_type\n      lockin_verbiage\n      cancellation_charge\n      shopsy_net_amount\n      __typename\n    }\n    upcoming_settlement {\n      neft_id\n      order_item_value {\n        net_amount\n        sale_amount {\n          item_revenue\n          customer_paid_shipping_revenue\n          customer_tax_rate\n          net_amount\n          __typename\n        }\n        total_offer {\n          free_shipping_offer\n          non_shipping_offer\n          net_amount\n          __typename\n        }\n        my_share {\n          free_shipping_offer\n          non_shipping_offer\n          net_amount\n          __typename\n        }\n        __typename\n      }\n      offer_adjustments {\n        net_amount\n        discount_base_amount\n        discount_on_mp_fees {\n          net_amount\n          actual_discount\n          item_gst_rate\n          gst_amount\n          __typename\n        }\n        __typename\n      }\n      flipkart_fees {\n        commission_fee\n        shopsy_marketing_fee\n        collection_fee\n        service_cancellation_charge\n        fixed_fee\n        fee_discount\n        cancellation_fee\n        installation_fee\n        uninstallation_fee\n        no_cost_emi_fee\n        franchise_fee\n        uninstallation_packaging_fee\n        tech_visit_fee\n        forward_shipping_fee\n        reverse_shipping_fee\n        pick_and_pack_fee\n        service_cancellation_fee\n        customer_shipping_fee_amount\n        customer_shipping_fee_type\n        net_amount\n        __typename\n      }\n      taxes {\n        net_amount\n        gst {\n          net_amount\n          tax_details {\n            fee_type\n            net_tax_rule_value\n            net_amount\n            tax_group {\n              tax_group\n              base_amount\n              net_amount\n              net_tax_rule_value\n              tax_detail {\n                tax_type\n                tax_value\n                rule_name\n                rule_value\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        tds {\n          tax_group\n          base_amount\n          net_amount\n          net_tax_rule_value\n          tax_detail {\n            tax_type\n            tax_value\n            rule_name\n            rule_value\n            __typename\n          }\n          __typename\n        }\n        tcs {\n          tax_group\n          base_amount\n          net_amount\n          net_tax_rule_value\n          tax_detail {\n            tax_type\n            tax_value\n            rule_name\n            rule_value\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      net_amount\n      input_gst_credits\n      income_tax_credits\n      payment_type\n      adjustment_reasons {\n        reason\n        subreason\n        __typename\n      }\n      settlement_date\n      refund_amount\n      protection_fund\n      reward_amount\n      adjustments\n      customer_shipping_amount\n      customer_shipping_type\n      incentives\n      lockin_type\n      lockin_verbiage\n      cancellation_charge\n      shopsy_net_amount\n      __typename\n    }\n    total_settlement {\n      neft_id\n      order_item_value {\n        net_amount\n        sale_amount {\n          item_revenue\n          customer_paid_shipping_revenue\n          net_amount\n          __typename\n        }\n        total_offer {\n          free_shipping_offer\n          non_shipping_offer\n          net_amount\n          __typename\n        }\n        my_share {\n          free_shipping_offer\n          non_shipping_offer\n          net_amount\n          __typename\n        }\n        __typename\n      }\n      offer_adjustments {\n        net_amount\n        discount_base_amount\n        discount_on_mp_fees {\n          net_amount\n          actual_discount\n          item_gst_rate\n          gst_amount\n          __typename\n        }\n        __typename\n      }\n      flipkart_fees {\n        commission_fee\n        shopsy_marketing_fee\n        collection_fee\n        service_cancellation_charge\n        fixed_fee\n        fee_discount\n        cancellation_fee\n        installation_fee\n        uninstallation_fee\n        no_cost_emi_fee\n        franchise_fee\n        uninstallation_packaging_fee\n        tech_visit_fee\n        forward_shipping_fee\n        reverse_shipping_fee\n        pick_and_pack_fee\n        service_cancellation_fee\n        customer_shipping_fee_amount\n        customer_shipping_fee_type\n        net_amount\n        __typename\n      }\n      taxes {\n        net_amount\n        gst {\n          net_amount\n          tax_details {\n            fee_type\n            net_tax_rule_value\n            net_amount\n            tax_group {\n              tax_group\n              base_amount\n              net_amount\n              net_tax_rule_value\n              tax_detail {\n                tax_type\n                tax_value\n                rule_name\n                rule_value\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        tds {\n          tax_group\n          base_amount\n          net_amount\n          net_tax_rule_value\n          tax_detail {\n            tax_type\n            tax_value\n            rule_name\n            rule_value\n            __typename\n          }\n          __typename\n        }\n        tcs {\n          tax_group\n          base_amount\n          net_amount\n          net_tax_rule_value\n          tax_detail {\n            tax_type\n            tax_value\n            rule_name\n            rule_value\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      net_amount\n      input_gst_credits\n      income_tax_credits\n      payment_type\n      settlement_date\n      refund_amount\n      protection_fund\n      reward_amount\n      adjustments\n      customer_shipping_amount\n      customer_shipping_type\n      incentives\n      lockin_type\n      lockin_verbiage\n      cancellation_charge\n      shopsy_net_amount\n      __typename\n    }\n    __typename\n  }\n}\n"}
            response = requests.post(
            'https://seller.flipkart.com/napi/graphql', headers=headers, data=json.dumps(data))
            json_data = json.loads(response.text)
            reward_amount = json_data["data"]["getOrderTransactionHistory"]["settled_settlements"][0]["reward_amount"]
            net_amount = json_data["data"]["getOrderTransactionHistory"]["settled_settlements"][0]["net_amount"]
            file.write(f"{order},{net_amount},{reward_amount}\n")
    print("Done!")

get_transaction(sys.argv[1], sys.argv[2])