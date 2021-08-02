import base64
import hashlib
import hmac
import json
import os
import threading
import time
import uuid
from datetime import datetime

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

    def get_traider_id(self):
        """Get traider ID

        Returns:
            String: Traider ID.
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
        """Signing a message

        Returns:
            String: base64-encode the signature (the output of the sha256 HMAC)
        """
        secret = base64.b64decode(self.access_secret).strip()
        message = message.encode('utf-8')
        h = hmac.new(secret, message, digestmod=hashlib.sha256)
        signature = base64.b64encode(h.digest())
        return signature.decode('utf-8')

    def _make_request(self, method: str, path: str, data: dict={}, params: dict={}):
        """Make a request

        Args:
            method (str): The HTTP method should be UPPER CASE.
            path (str): Specific path.
            data (dict, optional): Defaults to {}.
            params (dict, optional): Defaults to {}.

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
        """Create New Order

        Args:
            price (float): A client-specified order id.
            size (int): The quantity to buy or sell.
            symbol (str, optional): The symbol for which the order is placed. Defaults to 'ICP-USD'.
            side (str, optional): Can be buy or sell. Defaults to 'sell'.
            order_type (str, optional): The type of order, which controls how the order will be executed. Defaults to 'limit'.

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
        """Cancel all orders

        Args:
            symbol (str): [description]
        """
        response = self._make_request('POST', '/v1/orders/bulk')
        print(response.status_code)

    def cancel_order(self, order_id: str):
        """Cancel order

        Args:
            order_id (str): Order ID.

        Returns:
            String: [description]
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
        """Get Specific Order (by id)

        Args:
            order_id (str): Order to retrieve.
        """
        data={}
        response = self._make_request('GET', f'/v1/symbols/{order_id}', data=data)
        print(response.status_code)

    def get_symbol(self, symbol: str):
        """[summary]

        Args:
            symbol (str, optional): 
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

    def cancel_orders(self, symbol: str):
        """Cancel All Orders

        Args:
            symbol (str): The symbol for which the order is placed.
        Returns:
            202	Accepted: Request received message.
        """
        response = self._make_request('DELETE', f'/v1/orders', data={'symbols': symbol})
        return response

    def get_order(self, order_id: str):
        """Get Specific Order (by id)

        Args:
            order_id (str): Order to retrieve.
        Returns:
            dict: An object containing an order.
        """
        response = self._make_request('GET', f'/v1/orders/{order_id}')
        return response

    def modify_order(self, order_id: str, price: float, size: int, symbol: str, side: str='sell', order_type: str='limit'):
        """Modify Existing Order

        You may modify the type, size, price, stop_price, and stop_trigger of an order. 
        Your modified order will not retain the time-priority of the original order. 
        Your order will retain the same order id.
        Args:
            order_id (str): Order to retrieve.
            price (float): The price of this order (if the order is of type limit).
            size (float): The quantity to buy or sell.
            symbol (str): The symbol for which the order is placed.
            side (str): Can be buy or sell. Defaults to 'sell'.
            order_type (str): The type of order, which controls how the order will be executed. 
                              One of: market, limit, stop_market, stop_limit, take_market, or take_limit.
                              Defaults to 'limit'.
        Returns:
            dict: An object containing an array of modifed order params.
        """
        data = {
            'symbol': symbol,
            'type': order_type,
            'side': side,
            'size': size,
            'price': price,
            }
        response = self._make_request('PATCH', f'/v1/orders/{order_id}', data=data )
        return response

    ## TO-DO
    def create_orders(self, price: float, size: int, symbol: str, side: str, order_type: str):
        """Create New Orders

        Args:
            body (list of dict): Orders to create
        """
        data = [{
            'symbol': symbol,
            'type': order_type,
            'side': side,
            'size': size,
            'price': price,
            }]
        response = self._make_request('POST', f'/v1/orders/bulk', data=data )
        return response

    # Reports
    def get_reports(self, count: int=200):
        """List Report Requests

        Args:
            count (int, optional): Maximum item count per page (default 200; max 500)

        Returns:
            dict: An object containing an array of report requests
        """
        response = self._make_request('GET', f'/v1/reports', params=str(count))
        return response

    # TO-DO
    def get_fills(self, report_type: str='fills'):
        """Request Report

        Request a new fills or account report (CSV)
        Args:
            count (int, optional): Maximum item count per page (default 200; max 500)

        Returns:
            dict: An object containing an array of report requests
        """

    def get_transfers(self, start_time: str='', end_time: str='', descending: bool=False, count: int=200):
        """List Transfers

        Args:
            start_time (str): Start date-time for results (inclusive; filter on created_at).
            end_time (str): End date-time for results (inclusive; filter on created_at).
            descending (bool): If true, sort newest results first (default false).
            count (int): Maximum item count per page (default 200; max 500).

        Returns:
            dict: An object containing an array of transfers.
        """
        params = {
            start_time: start_time,
            end_time: end_time,
            descending: descending,
            count: count
        }
        response = self._make_request('GET', f'/v1/transfers', params=params)
        return response

    def transfer_to_wallet(self, asset: str='BTC', amont: int=0):
        """Transfer Funds From Pro to Wallet

        Args:
            asset (str): The asset to transfer (e.g. BTC).
            amont (int): The value of the transfer (in quantity).

        Returns:
            string: The transfer id of the new request.
        """
        data = {}
        params = {
            asset: asset,
            amont: str(amont)
        }
        response = self._make_request('POST', f'/v1/transfers/to-wallet', data=data, params=params)
        return response

    def transfer_from_wallet(self, asset: str='BTC', amont: int=0):
        """Transfer Funds From Wallet to Pro

        Args:
            asset (str): The asset to transfer (e.g. BTC).
            amont (int): The value of the transfer (in quantity).

        Returns:
            string: The transfer id of the new request.
        """
        data = {}
        params = {
            asset: asset,
            amont: str(amont)
        }
        response = self._make_request('POST', f'/v1/transfers/from-wallet', data=data, params=params)
        return response

    def transfer_between_wallet(self, asset: str='BTC', amont: int=0):
        """Transfer Funds Between Entities

        Args:
            asset (str): The asset to transfer (e.g. BTC).
            amont (int): The value of the transfer (in quantity).

        Returns:
            string: The transfer id of the new request.
        """
        data = {}
        params = {
            asset: asset,
            amont: str(amont)
        }
        response = self._make_request('POST', f'/v1/transfers/internal-transfer', data=data, params=params)
        return response

    # Market Data API
    ## Auctions
    def get_candles(self, 
                    symbol: str, 
                    field_name: str='price', 
                    start_time: str=str(datetime(2011, 11, 4, 0, 0, 0)),
                    end_time: str=str(datetime.today()), 
                    granularity: str='1m', 
                    format: str='json'):
        """Get historic price data (OHLC) for a symbol.

        Args:
            symbol (str): Required.
            field_name (str): enumerated value(price, fair_price, best_ask, best_bid). Default: "price".
            start_time (str): date-time. Default: datetime(2011, 11, 4, 0, 0, 0)).
            end_time (str): date-time. Default: time at the moment of request.
            granularity (str): enumerated value(1m, 5m, 30m). Default: "1m".
            format (str): enumerated value(json, csv). Default: 'json'.

        Returns:
            dict: Candles are returned in the form [time, open, high, low, close, volume, index_close].
        """
        data = {
            'symbol': symbol,
            'field_name': field_name, 
            'start_time': start_time,
            'end_time': end_time, 
            'granularity': granularity, 
            'format': format
        }
        response = self._make_request('GET', f'/v1/symbols/{symbol}/candles', data=data)
        return response

    def get_auctions(self,
                    symbol: str,
                    min_volume: str='price',
                    start_time: str=str(datetime(2011, 11, 4, 0, 0, 0)),
                    end_time: str=str(datetime.today()),
                    descending: bool=False, 
                    count: int=200):
        """List Auctions

        Args:
            symbol (str): The symbol to list auctions for.
            min_volume (str, optional): Return auctions with greater than or equal to this trade volume. Defaults to 'price'.
            start_time (str, optional): Start date-time for results (inclusive; filter on logical_time).
            end_time (str, optional): End date-time for results (inclusive; filter on logical_time).
            descending (bool, optional): If true, sort newest results first (default false). Defaults to False.
            count (int, optional): Maximum item count per page (default 200; max 500). Defaults to 200.

        Returns:
            List: Returns historical, complete auctions for the given symbol - in descending chronological order. Indicative auctions are not included.
        """
        data = {
            'symbol': symbol,
            'min_volume': min_volume,
            'start_time': start_time,
            'end_time': end_time,
            'descending': descending,
            'count': count
        }
        response = self._make_request('GET', f'/v1/symbols/{symbol}/auctions', data=data)
        return response

    def get_auction_results(self, symbol: str, auction_code: str):
        """Get Auction Results

        Args:
            symbol (str): The symbol to list auctions for.
            auction_code (str): Required True. Code for auction.

        Returns:
            Dict: Get auction results for a specific (historical) auction.
        """
        response = self._make_request('GET', f'/v1/symbols/{symbol}/auctions/{auction_code}', params=auction_code)
        return response

    ## Order Books
    def get_order_book(self, symbol: str):
        """Get Order Book (Level 2)

        Args:
            symbol (str): The symbol.

        Returns:
            Dict: Get the full, price-aggregated order book for a symbol.
        """
        response = self._make_request('GET', f'/v1/symbols/{symbol}/book')
        return response

    def get_quote(self, symbol: str):
        """Get Quote (Level 1)

        Args:
            symbol (str): The symbol.

        Returns:
            Dict: Get the latest quote data including last trade, best bid, and best ask.
        """
        response = self._make_request('GET', f'/v1/symbols/{symbol}/quote')
        return response

    ## Symbols
    def get_symbols(self):
        """List Symbols

        Returns:
            Dict: Get symbols and metadata for all active markets on CoinList Pro.
        """
        response = self._make_request('GET', f'/v1/symbols')
        return response

    def get_symbol_summaries(self, symbol: str):
        """Get Symbol Summaries

        Args:
            symbol (str): The symbol.

        Returns:
            Dict: Get recent performance data for all active markets on CoinList Pro.
        """
        response = self._make_request('GET', f'/v1/symbols/summary')
        return response

    def get_specific_symbol(self, symbol: str):
        """Get Specific Symbol

        Args:
            symbol (str): The symbol.

        Returns:
            Dict: Get symbol metadata.
        """
        response = self._make_request('GET', f'/v1/symbols/summary')
        return response

    def get_market_summary(self, symbol: str):
        """Get Market Summary

        Args:
            symbol (str): The symbol.

        Returns:
            Dict: Get a summary of recent market performance for a given symbol.
        """
        response = self._make_request('GET', f'/v1/symbols/{symbol}')
        return response


if __name__ == '__main__':
    coinlist = CoinlistApi(ACCESS_KEY, ACCESS_SECRET)
    res = coinlist.get_quote(symbol='ICP-USDT')
    print(res)
