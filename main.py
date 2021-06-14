import base64
import hashlib
import hmac
import json
import os
import threading
import time
import uuid

import requests
import websocket
from dotenv import load_dotenv
from requests import Request, Session


load_dotenv()
ACCESS_KEY = os.getenv('ACCESS_KEY')
ACCESS_SECRET = os.getenv('ACCESS_SECRET')

# @dataclass
class CoinlistApi:
    def __init__(self, access_key: str, access_secret: str = ACCESS_SECRET):
        self.access_key = access_key
        self.access_secret = access_secret
        self.endpoint_url = 'https://trade-api.coinlist.co'
        self.wss_url ='wss://trade-api.coinlist.co'
        self.traider_id = ''
        # self.ws_id = 1
        # self._ws = None

        # t = threading.Thread(target=self._start_ws)
        # t.start()


    def get_traider_id(self):
        response = self._make_requests('GET', '/v1/accounts')
        traider_id = response.json()['accounts'][0]['trader_id']
        print(response.status_code)
        return traider_id


    def get_account_summary(self):
        response = self._make_requests('GET', f'/v1/accounts/{self.traider_id}')
        asset_balances = response.json()['asset_balances']
        asset_holds = response.json()['asset_holds']
        net_liquidation_value_usd = response.json()['net_liquidation_value_usd']
        # print(response.status_code)
        return asset_balances, asset_holds, net_liquidation_value_usd


    def _sign(self, message, secret):
        secret = base64.b64decode(self.access_secret).strip()
        message = message.encode('utf-8')
        h = hmac.new(secret, message, digestmod=hashlib.sha256)
        signature = base64.b64encode(h.digest())
        return signature.decode('utf-8')
    

    def _make_requests(self, method='POST', path=None, data=None, timeout=10):
        # path = path or None
        # data = data or None
        url = self.endpoint_url + path
        # body = {}
        timestamp = str(int(time.time()))
        json_body = json.dumps((data), separators=(',', ':')).strip()
        message = timestamp + method + path + ('' or json_body)
        signature = self._sign(message, self.access_secret)
        headers = {
            'Content-Type': 'application/json',
            'CL-ACCESS-KEY': self.access_key,
            'CL-ACCESS-SIG': signature,
            'CL-ACCESS-TIMESTAMP': timestamp
        }
        s = Session()
        req = Request(method=method, url=url, data=json_body, headers=headers)
        prepped = s.prepare_request(req)
        response = s.send(prepped, timeout=timeout)
        return response


    def show_symbols(self):
        r = self._make_requests('GET', '/v1/symbols')
        response = r.json().get('symbols')
        symbols = []
        with open('symbols.txt', 'w') as f:
            for i in response:
                symbols.append(i['symbol'])
                f.write(i['symbol'] + '\n')


    def create_order(self, price, size, symbol='ICP-USD', side='sell', order_type='limit'):
   
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


    def create_orders(self, symbol):
        response = self._make_requests('POST', '/v1/orders/bulk')
        print(response.status_code)


    def cancel_order(self, order_id):
        params = {
            'order_id': str(order_id)
        }
        res = self._make_requests('DELETE', f'/v1/orders/{order_id}', data=params)
        return res


    def cancel_by_symbol(self, symbol='ICP-USD'):
        headers = {
            'accept': 'application/json'
        }
        data = {
            'symbol': symbol
        }
        res = self._make_requests('DELETE', '/v1/orders', data=data)
        return res


    def cancel_all(self, uids: list=None):
        uids = uids or None
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        data = [
            'string1($uuid)',
            'string2($uuid)',
            'string3($uuid)'
        ]
        res = self._make_requests('DELETE', '/v1/orders', data=data)
        return res


    def get_orders(self, order_id):
        data={}
        response = self._make_requests('GET', f'/v1/symbols/{order_id}', data=data)
        print(response.status_code)


    def get_symbol(self, symbol):
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