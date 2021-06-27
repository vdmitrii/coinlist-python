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
        response = self._make_request('GET', '/v1/accounts')
        # traider_id = response['accounts'][0]['trader_id']
        return response

    def get_account_summary(self):
        traider_id = self.get_traider_id()
        response = self._make_request('GET', f'/v1/accounts/{self.traider_id}')
        asset_balances = response.json()['asset_balances']
        asset_holds = response.json()['asset_holds']
        net_liquidation_value_usd = response.json()['net_liquidation_value_usd']
        return asset_balances, asset_holds, net_liquidation_value_usd

    def _sign(self, message: str, secret: str):
        secret = base64.b64decode(self.access_secret).strip()
        message = message.encode('utf-8')
        h = hmac.new(secret, message, digestmod=hashlib.sha256)
        signature = base64.b64encode(h.digest())
        # print(signature.decode('utf-8'))
        return signature.decode('utf-8')

    def _make_request(self, method: str, path: str, data: dict={}, params: dict={}):
        path_with_params = requests.Request(method, self.endpoint_url + path, params=params).prepare().path_url
        timestamp = str(int(time.time()))
        json_body = json.dumps((data), separators=(',', ':')).strip()
        message = timestamp + method + path_with_params + ('' if not data else json_body)
        signature = self._sign(message, self.access_secret)
        headers = {
            'Content-Type': 'application/json',
            'CL-ACCESS-KEY': self.access_key,
            'CL-ACCESS-SIG': signature,
            'CL-ACCESS-TIMESTAMP': timestamp
        }
        url = self.endpoint_url + path_with_params
        r = requests.request(method, url, headers=headers, data=json_body)
        return r.json()

    def show_symbols(self):
        r = self._make_request('GET', '/v1/symbols')
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
        response = self._make_request(method='POST', path='/v1/orders', data=data)
        try:
            returned = response.json()['order']['order_id']
        except Exception:
                print('Ошибка при размещении ордера: ')
        return returned

    def create_orders(self, symbol: str):
        response = self._make_request('POST', '/v1/orders/bulk')
        print(response.status_code)

    def cancel_order(self, order_id: str):
        params = {'order_id': str(order_id)}
        res = self._make_request('DELETE', f'/v1/orders/{order_id}', data=params)
        return res

    def cancel_by_symbol(self, symbol: str='ICP-USD'):
        headers = {'accept': 'application/json'}
        data = {'symbol': symbol}
        res = self._make_request('DELETE', '/v1/orders', data=data)
        return res

    def cancel_all(self, uids: list=None):
        uids = uids or None
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        res = self._make_request('DELETE', '/v1/orders', data=uids)
        return res

    def get_orders(self, order_id: str):
        data={}
        response = self._make_request('GET', f'/v1/symbols/{order_id}', data=data)
        print(response.status_code)

    def get_symbol(self, symbol: str):
        data={}
        response = self._make_request('GET', f'/v1/symbols/{symbol}', data=data)
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
    # print(ACCESS_KEY)
    # print(ACCESS_SECRET)
    print(coinlist.get_traider_id())
