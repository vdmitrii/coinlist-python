# coinlist-python
This is an unofficial python wrapper for the Coinlist exchange

# Official documentation
  https://python-binance.readthedocs.io/en/latest/


# Features
--------

- Implementation of all General, Market Data and Account endpoints.
- Simple handling of authentication


Quick Start
-----------

`Generate an API Key <https://www.coinlist.pro>`_ and assign relevant permissions.


.. code:: bash

    pip install python-binance


.. code:: python

    from coinlist import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
    client = Client(api_key, api_secret)

    # get market depth
    depth = client.get_order_book(symbol='BNBBTC')

    # place a test market buy order, to place an actual order use the create_order function
    order = client.create_test_order(
        symbol='BNBBTC',
        side=Client.SIDE_BUY,
        type=Client.ORDER_TYPE_MARKET,
        quantity=100)

    # get all symbol prices
    prices = client.get_all_tickers()

    # withdraw 100 ETH
    # check docs for assumptions around withdrawals
    from binance.exceptions import BinanceAPIException
    try:
        result = client.withdraw(
            asset='ETH',
            address='<eth_address>',
            amount=100)
    except BinanceAPIException as e:
        print(e)
    else:
        print("Success")