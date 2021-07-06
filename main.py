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
    """Class for working with The CoinList Pro API
    """
    def __init__(self, access_key: str = ACCESS_KEY, access_secret: str = ACCESS_SECRET):
        self.access_key = access_key
        self.access_secret = access_secret
        self.endpoint_url = 'https://trade-api.coinlist.co'
        self.wss_url = 'wss://trade-api.coinlist.co'

    def get_traider_id(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        response = self._make_request('GET', '/v1/accounts')
        traider_id = response['accounts'][0]['trader_id']
        return traider_id

    def get_account_summary(self):
        traider_id = self.get_traider_id()
        response = self._make_request('GET', f'/v1/accounts/{traider_id}')
        asset_balances = response.json()['asset_balances']
        asset_holds = response.json()['asset_holds']
        net_liquidation_value_usd = response.json()['net_liquidation_value_usd']
        return asset_balances, asset_holds, net_liquidation_value_usd

    def _sign(self, message: str, secret: str):
        """[summary]

        Args:
            message (str): [description]
            secret (str): [description]

        Returns:
            [type]: [description]
        """
        secret = base64.b64decode(self.access_secret).strip()
        message = message.encode('utf-8')
        h = hmac.new(secret, message, digestmod=hashlib.sha256)
        signature = base64.b64encode(h.digest())
        return signature.decode('utf-8')

    def _make_request(self, method: str, path: str, data: dict={}, params: dict={}):
        """[summary]

        Args:
            method (str): [description]
            path (str): [description]
            data (dict, optional): [description]. Defaults to {}.
            params (dict, optional): [description]. Defaults to {}.

        Returns:
            [type]: [description]
        """
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
        """[summary]

        Args:
            price (float): [description]
            size (int): [description]
            symbol (str, optional): [description]. Defaults to 'ICP-USD'.
            side (str, optional): [description]. Defaults to 'sell'.
            order_type (str, optional): [description]. Defaults to 'limit'.

        Returns:
            [type]: [description]
        """
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
        """[summary]

        Args:
            symbol (str): [description]
        """
        response = self._make_request('POST', '/v1/orders/bulk')
        print(response.status_code)

    def cancel_order(self, order_id: str):
        """[summary]

        Args:
            order_id (str): [description]

        Returns:
            [type]: [description]
        """
        params = {'order_id': str(order_id)}
        res = self._make_request('DELETE', f'/v1/orders/{order_id}', data=params)
        return res

    def cancel_by_symbol(self, symbol: str='ICP-USD'):
        """[summary]

        Args:
            symbol (str, optional): [description]. Defaults to 'ICP-USD'.

        Returns:
            [type]: [description]
        """
        headers = {'accept': 'application/json'}
        data = {'symbol': symbol}
        res = self._make_request('DELETE', '/v1/orders', data=data)
        return res

    def cancel_all(self, uids: list=None):
        """[summary]

        Args:
            uids (list, optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """
        uids = uids or None
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        res = self._make_request('DELETE', '/v1/orders', data=uids)
        return res

    def get_orders(self, order_id: str):
        """[summary]

        Args:
            order_id (str): [description]
        """
        data={}
        response = self._make_request('GET', f'/v1/symbols/{order_id}', data=data)
        print(response.status_code)

    def get_symbol(self, symbol: str):
        """[summary]

        Args:
            symbol (str): [description]
        """
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

    def list_fees(self):
        """List Fees

        Returns:
            dict: An object containing fee schedules by symbol
        """
        response = self._make_request('GET', '/v1/fees')
        return response

    def list_accounts(self):
        """List Accounts

        Returns:
            dict: An object containing an array of trading accounts
        """
        response = self._make_request('GET', '/v1/accounts')
        return response

    def get_account_summary(self):
        """Get Account Summary

        Returns:
            dict: A summary of the current state of this account
        """
        trader_id = self.get_traider_id()
        response = self._make_request('GET', f'/v1/accounts/{trader_id}')
        return response

    def get_account_history(self):
        """Get Account History

        Returns:
            dict: An object containing an array of transactions
        """
        trader_id = self.get_traider_id()
        response = self._make_request('GET', f'/v1/accounts/{trader_id}/ledger')
        return response

    def get_coinlist_wallets(self):
        """Get CoinList Wallets

        Returns:
            dict: An object containing an array of wallet records
        """
        trader_id = self.get_traider_id()
        response = self._make_request('GET', f'/v1/accounts/{trader_id}/wallets')
        return response

    def get_daily_account_summary(self):
        """Get Daily Account Summary

        Returns:
            dict: An object containing an array of daily transaction summaries.
        """
        trader_id = self.get_traider_id()
        response = self._make_request('GET', f'/v1/accounts/{trader_id}/ledger-summary')
        return response

    def get_list_balances(self):
        """List Balances

        Returns:
            dict: An object containing balance details.
        """
        response = self._make_request('GET', f'/v1/balances')
        return response

    def get_list_fills(self):
        """List Fills

        Returns:
            dict: An object containing an array of fills.
        """
        response = self._make_request('GET', f'/v1/fills')
        return response

    def get_list_apikeys(self):
        """List API Keys

        Returns:
            dict: An object containing an array of keys.
        """
        trader_id = self.get_traider_id()
        response = self._make_request('GET', f'/v1/balances')
        return response

    # ORDERS
    def get_list_orders(self):
        """List Orders

        Returns:
            dict: An object containing an array of orders.
        """
        response = self._make_request('GET', f'/v1/orders')
        return response

    def create_order(self, price: float, size: int, symbol: str, side: str='sell', order_type: str='limit'):
        """Create Order

        Args:
            price (float): The price of this order (if the order is of type limit).
            size (float): The quantity to buy or sell.
            symbol (str): The symbol for which the order is placed.
            side (str): Can be buy or sell. Defaults to 'sell'.
            order_type (str): The type of order, which controls how the order will be executed. 
                              One of: market, limit, stop_market, stop_limit, take_market, or take_limit.
                              Defaults to 'limit'.
        Returns:
            202 status: New order request received.
        """
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
        except Exception as e:
                print('Error while creating the order: ', e)
        return returned


if __name__ == '__main__':
    coinlist = CoinlistApi(ACCESS_KEY, ACCESS_SECRET)
    res = coinlist.get_list_orders()
    print(res)
