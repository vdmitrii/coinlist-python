import base64
import hashlib
import hmac
import json
import os
import threading
import time
import uuid

import requests
# import websocket
from dotenv import load_dotenv
from requests import Request, Session


load_dotenv()
ACCESS_KEY = os.getenv('ACCESS_KEY')
ACCESS_SECRET = os.getenv('ACCESS_SECRET')


class CoinlistApi:
    def __init__(self, access_key: str = ACCESS_KEY, access_secret: str = ACCESS_SECRET):
        self.access_key = access_key
        self.access_secret = access_secret
        self.endpoint_url = 'https://trade-api.coinlist.co'
        self.wss_url = 'wss://trade-api.coinlist.co'
        # self.traider_id = ''

    def get_traider_id(self):
        response = self._make_requests('GET', '/v1/accounts')
        # traider_id = response.json()['accounts'][0]['trader_id']
        # print(response.status_code)
        return response

    def get_account_summary(self):
        traider_id = self.get_traider_id()
        response = self._make_requests('GET', f'/v1/accounts/{self.traider_id}')
        asset_balances = response.json()['asset_balances']
        asset_holds = response.json()['asset_holds']
        net_liquidation_value_usd = response.json()['net_liquidation_value_usd']
        return asset_balances, asset_holds, net_liquidation_value_usd

    def _sign(self, message: str, secret: str):
        secret = base64.b64decode(self.access_secret).strip()
        message = message.encode('utf-8')
        h = hmac.new(secret, message, digestmod=hashlib.sha256)
        signature = base64.b64encode(h.digest())
        return signature.decode('utf-8')

    def _make_requests(self, method: str='POST', path: str='', data: str='', timeout: int=10):
        url = self.endpoint_url + path
        print('url', url)
        timestamp = str(int(time.time()))
        print('timestamp', timestamp)
        json_body = json.dumps((data), separators=(',', ':')).strip()
        print('json_body', json_body)
        message = timestamp + method + path + json_body
        print('message', message)
        signature = self._sign(message, self.access_secret)
        print('signature', signature)
        headers = {
            'Content-Type': 'application/json',
            'CL-ACCESS-KEY': self.access_key,
            'CL-ACCESS-SIG': signature,
            'CL-ACCESS-TIMESTAMP': timestamp
        }
        print(headers)
        s = Session()
        req = Request(method=method, url=url, data=json_body, headers=headers)
        prepped = s.prepare_request(req)
        response = s.send(prepped, timeout=timeout)
        return response.json()

    def show_symbols(self):
        r = self._make_requests('GET', '/v1/symbols')
        response = r.json().get('symbols')
        symbols = []
        with open('symbols.txt', 'w') as f:
            for i in response:
                symbols.append(i['symbol'])
                f.write(i['symbol'] + '\n')

    def create_order(self, price: float, size: int, symbol: str='ICP-USD', side: str='sell', order_type: str='limit'):
        data = {
            'symbol': symbol,
            'type': order_type,
            'side': side,
            'size': size,
            'price': price,
            "origin": "api"
        }
        response = self._make_requests(method='POST', path='/v1/orders', data=data)
        try:
            returned = response.json()['order']['order_id']
        except Exception:
                print('Ошибка при размещении ордера: ')
        return returned

    def create_orders(self, symbol: str):
        response = self._make_requests('POST', '/v1/orders/bulk')
        print(response.status_code)

    def cancel_order(self, order_id: str):
        params = {'order_id': str(order_id)}
        res = self._make_requests('DELETE', f'/v1/orders/{order_id}', data=params)
        return res

    def cancel_by_symbol(self, symbol: str='ICP-USD'):
        headers = {'accept': 'application/json'}
        data = {'symbol': symbol}
        res = self._make_requests('DELETE', '/v1/orders', data=data)
        return res

    def cancel_all(self, uids: list=None):
        uids = uids or None
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        res = self._make_requests('DELETE', '/v1/orders', data=uids)
        return res

    def get_orders(self, order_id: str):
        data={}
        response = self._make_requests('GET', f'/v1/symbols/{order_id}', data=data)
        print(response.status_code)

    def get_symbol(self, symbol: str):
        data={}
        response = self._make_requests('GET', f'/v1/symbols/{symbol}', data=data)
        print(response.status_code)

    def exchange_time(self):
        return None

    def fills(self):
        return None

    def orders_info(self):
        return None

    def order_info(self):
        return None

    def _uuid(self):
        return str(uuid.uuid1())


if __name__ == '__main__':
    coinlist = CoinlistApi(ACCESS_KEY, ACCESS_SECRET)
    print(ACCESS_KEY)
    print(ACCESS_SECRET)
    print(coinlist.get_traider_id())
