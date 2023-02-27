from dotenv import load_dotenv
import os
import json
import requests
from flask import Flask, request
from binance.client import Client
from binance.enums import *

load_dotenv()  # take environment variables from .env.

# tradingview ip whitelist, if needed
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

# tld us required for US-based server: , tld='us'
client = Client(API_KEY, API_SECRET)

# figure out if existing position is short or long
def determine_short_or_long(position):
      mark_price = float(position['markPrice'])
      entry_price = float(position['entryPrice'])
      if mark_price != entry_price:
          profit = float(position['unRealizedProfit']) >= 0
          if entry_price < mark_price and profit:
              return 'LONG'
          elif entry_price < mark_price and not profit:
              return 'SHORT'
          elif entry_price > mark_price and profit:
              return 'SHORT'
          elif entry_price > mark_price and not profit:
              return 'LONG'
      else:
          return False

# place futures order
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
      # SETUP VARS
      # TICKER = MARKET TICKER I.E. BTCUSDTPERP
      ticker = data['ticker']
      alert_time = data['time']
      # TICKER_TRUNC = TRUNCATED TICKER FOR MAKING AN ORDER ON BINANCE FUTURES API
      ticker_trunc = ticker[ 0 : 7 ]

      # CHECK POSITIONS OF UNDERLYING ASSET
      position_data = client.futures_position_information()

      if position_data:
          for position in position_data:
            if float(position['positionAmt']) != 0:
                
                # check that the requested symbol is correct
                if position['symbol'] == ticker_trunc:
                    
                    print(ticker_trunc, position['symbol'])
                    # do opposite of what the position is
                    side = "BUY" if determine_short_or_long(position)=="SHORT" else "SELL"
                    order_response = futures_order(side, position['positionAmt'], ticker_trunc)
              
                    # compose text message
                    message = f"Closer sent order of {side} {position['positionAmt']} {ticker_trunc}"
                    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
                   
                    # send the message
                    requests.get(url).json()
                else: 
                    print('nope')
                # position['symbol']
                # position['positionAmt']
                # position['entryPrice']
                # position['markPrice']
                # position['unRealizedProfit']
                # position['liquidationPrice']
                # position['leverage']
                # position['maxNotionalValue']
                # position['marginType']
                # position['isolatedMargin']
                # position['isAutoAddMargin']
                # position['positionSide']
                # position['notional']
                # position['isolatedWallet']
                # position['updateTime']

      else:
          print('no position data found')

    return {
        "code": "success",
        "message": data
    }
   