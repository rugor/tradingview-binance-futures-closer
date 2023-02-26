from dotenv import load_dotenv
import os
import json
from flask import Flask, request
from binance.client import Client
from binance.enums import *

load_dotenv()  # take environment variables from .env.

WEBHOOK_PASSPHRASE = os.getenv("WEBHHOOK_PASSPHRASE")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

app = Flask(__name__)

client = Client(API_KEY, API_SECRET)

# def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
#     try:
#         print(f"sending order {order_type} - {side} {quantity} {symbol}")
#         order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
#         # print(order)
#     except Exception as e:
#         print("an exception occured - {}".format(e))
#         return False

#     return order

def futures_order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try: 
        print(f"sending order {order_type} - {side} {quantity} {symbol}")
        order = client.futures_create_order(
          symbol=symbol,
          type=order_type,
          side=side,
          quantity=quantity
      )
        
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return order

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/closer", methods=["POST"])
def webhook():
    # print(request.data)
    data = json.loads(request.data)

    if data['passphrase'] != WEBHOOK_PASSPHRASE:
      print("order failed")
      # print(config.WEBHOOK_PASSPHRASE)
      return {
        "code": "error",
        "message": "order failed"
      }
    else:  
      # side = data['strategy']['order_action'].upper()
      # quantity = data['strategy']['order_contract']
      # ticker = data['ticker']
      # bar = data['bar']
      # print (side)
      # print (quantity)
      # print (ticker)
      # print (bar)
      
      # side, quantity, symbol, order_type=ORDER_TYPE_MARKET

      # spot order
      #order_response = order("BUY", 0.0005, "BTCUSDT")

      # futures limit order
      # binance_client.futures_create_order(
      #     symbol='BTCUSDT',
      #     type='LIMIT',
      #     timeInForce='GTC',  # Can be changed - see link to API doc below
      #     price=30000,  # The price at which you wish to buy/sell, float
      #     side='BUY',  # Direction ('BUY' / 'SELL'), string
      #     quantity=0.001  # Number of coins you wish to buy / sell, float
      # )
      
      # futures market order
      # this is using default leverage
      order_response = futures_order("SELL", 0.001, "BTCUSDT")
      
    # print(order_response)

    return {
        "code": "success",
        "message": data
    }

    # if data['passphrase'] != config.WEBHHOOK_PASSPHRASE: 
    #     return {
    #         "code": "error",
    #         "message": "invalid"
    #     }
    
    # if order_response: 
    #     return {
    #         "code": "success",
    #         "message": "order executed"
    #     }
    # else:
    #     print("order failed")
    #     return {
    #         "code": "error",
    #         "message": "order failed"
    #     }
   