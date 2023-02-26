from dotenv import load_dotenv
import os
import json
import requests
from flask import Flask, request
from binance.client import Client
from binance.enums import *

load_dotenv()  # take environment variables from .env.

# tradingview ip whitelist
# https://www.tradingview.com/support/solutions/43000529348-about-webhooks/
# 52.89.214.238
# 34.212.75.30
# 54.218.53.128
# 52.32.178.7

WEBHOOK_PASSPHRASE = os.getenv("WEBHHOOK_PASSPHRASE")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)

# tld us required for US-based server
client = Client(API_KEY, API_SECRET, tld='us')

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
      return {
        "code": "error",
        "message": "order failed"
      }
    else: 
      # SETUP THE VARS
      #  
      # side = BUY OR SELL
      side = data['strategy']['order_action'].upper()
      # quantity = COIN QUANTITY
      quantity = data['strategy']['order_contract']
      # TICKER = MARKET TICKER I.E. BTCUSDTPERP
      ticker = data['ticker']
      # TICKER_TRUNC = TRUNCATED TICKER FOR MAKING AN ORDER ON BINANCE FUTURES API
      ticker_trunc = ticker[ 0 : 7 ]

      # FUTURES MARKET ORDER
      # *uses the coin's default leverage*
      order_response = futures_order(side, quantity, ticker_trunc)
      # print(order_response)

      message = f"Closer sent order of {side} {quantity} {ticker_trunc}"
      url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
      # print(requests.get(url).json()) # this sends the message
      requests.get(url).json()

    return {
        "code": "success",
        "message": data
    }
   