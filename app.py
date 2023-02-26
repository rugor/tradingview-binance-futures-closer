import json
import os
from flask import Flask, request
from binance.client import Client
from binance.enums import *

WEBHOOK_PASSPHRASE = os.getenv("WEBHOOK_PASSPHRASE")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

app = Flask(__name__)

client = Client(API_KEY, API_SECRET, tld='us')

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print(f"sending order {order_type} - {side} {quantity} {symbol}")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        # print(order)
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
    side = data['strategy']['order_action'].upper()
    quantity = data['strategy']['order_contract']
    ticker = data['ticker']
    bar = data['bar']

    print (side)
    print (quantity)
    print (ticker)
    print (bar)

    # order_response = order(side, quantity, "DOGEUSD")
    # print(order_response)

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
    return {
        "code": "success",
        "message": data
    }