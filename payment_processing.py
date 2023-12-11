import requests
import xml.etree.ElementTree as ET
import hashlib
from random import randint
import time
from dotenv import load_dotenv
import os
import asyncio

load_dotenv('data/.env.prod')

api_key = os.environ['api_key']

async def create_a_bill(price):
    url = "https://api.intellectmoney.ru/p2p/getFormUrl/"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
    }

    order_id = randint(1,9999999)
    
    data = {
        "orderId": order_id,
        "amount": price,
        "formId": 700673,
        'cardGuid': 'test_guid',
        'comment':'Тестовый коммент',
        'backUrl': 'https://discord.gg/cursedshop',
        "language": "RU"
    }

    hash = f"{data['orderId']}::{data['amount']}::{data['formId']}::{data['cardGuid']}::{data['comment']}::{data['backUrl']}::{data['language']}::{api_key}"
    
    sha1_hash = hashlib.sha1()
    sha1_hash.update(hash.encode('utf-8'))
    hashed_string = sha1_hash.hexdigest()
    
    data.update({'hash': hashed_string})
    
    response = requests.post(url, headers=headers, data=data).text
    root = ET.fromstring(response)
    
    print(response)
    
    user_token_response = root.find(".//Desc")
    user_token_url = root.find(".//Url")
    user_token_response = user_token_response.text
    user_token_url = user_token_url.text
    
    return (user_token_url, order_id)


async def if_payment_is_done(order_id):
    url = "https://api.intellectmoney.ru/p2p/CheckPay"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
    }
    
    data = {
        'orderId': order_id,
        'formId': 700673
    }

    hash = f"{data['orderId']}::{data['formId']}::{api_key}"
    
    sha1_hash = hashlib.sha1()
    sha1_hash.update(hash.encode('utf-8'))
    hashed_string = sha1_hash.hexdigest()
    
    data.update({'hash': hashed_string})

    response = requests.post(url, headers=headers, data=data).text
    root = ET.fromstring(response)
    bill_response = root.find(".//PaymentState")
    
    return bill_response.text
