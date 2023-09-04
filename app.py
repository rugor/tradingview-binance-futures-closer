# load dependencies (requirements.txt)
from dotenv import load_dotenv
import os, requests, json, time
from flask import Flask, request
from binance.client import Client
from binance.enums import *

# take environment variables from .env
load_dotenv()

# tradingview ip whitelist, if needed for binance api security
# https://www.tradingview.com/support/solutions/43000529348-about-webhooks/
# 52.89.214.238
# 34.212.75.30
# 54.218.53.128
# 52.32.178.7

# queue up your environment variables
WEBHOOK_PASSPHRASE = os.getenv("WEBHHOOK_PASSPHRASE")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# FIXIE proxy; you need a fixed IP address for Binance API security whitelist
# This is so only requests from a specific consistent IP are allowed to trigger API requests
os.environ['http_proxy'] = os.environ.get('FIXIE_URL', '')
os.environ['https_proxy'] = os.environ.get('FIXIE_URL', '')

# define app and client
app = Flask(__name__)
client = Client(API_KEY, API_SECRET)

# these are the functions we will use later on

# 1. strip the "USDT.P" suffix from the tradingview ticker symbol and replace with "USDT" for binance API
def get_futures_ticker(ticker):
    sub = "USDT.P"
    if sub in ticker:
        usdt = "USDT"
        new_ticker = ticker[:ticker.index(sub)]
        new_ticker += usdt
        return new_ticker
    else:
        print("Not USDT.P")
        return {
          "code": "error",
          "message": "ticker not USDT.P"
        }

# 2. figure out if the position is short or long; "side"
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

# 3. place a new market order to close the short or long position
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
    
    data = json.loads(request.data)
    alert_passphrase = data['passphrase']
    alert_ticker = data['ticker']
    alert_time = data['time']
    ticker_trunc = get_futures_ticker(alert_ticker)

    # check that the passphrase in the TradingView alert message matches the passphrase from the .env file
    if alert_passphrase != WEBHOOK_PASSPHRASE:
      print("order failed")
      return {
        "code": "error",
        "message": "order failed"
      }
    else: 
      # ticker_trunc = a truncated ticker symbol format for making an order through the binance futures API
      # pull all account open position info from binance futures API
      position_data = client.futures_position_information()

      if position_data:
          # for all open positions
          for position in position_data:
            if float(position['positionAmt']) != 0:         
                
                # check the truncated symbol received from tradingview against open positions
                if position['symbol'] == ticker_trunc:       

                    # define the side for the market order (this function is defined above)
                    side = "BUY" if determine_short_or_long(position)=="SHORT" else "SELL"
                    # remove negative sign from existing positionAmt (in the case of short positions)
                    quantity = position['positionAmt'].replace("-", "")
                    # market close the position
                    order_response = futures_order(side, quantity, ticker_trunc)      
                    # this stuff is optional... send a telegram message when the order has completed  
                    # compose text message
                    message = f"Closer sent order of:\n{side}\n{quantity} {ticker_trunc} \n{alert_time}"
                    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"               
                    # send the message
                    requests.get(url).json()
                else: 
                    print('nope')

      else:
          print('no position data found')

    return {
        "code": "success",
        "message": data
    }

# paste this in the "message" of the TradingView Alert   
# {
#   "passphrase": "some_passphrase_defined_in_the_.env_file",
#   "time": "{{timenow}}",
#   "ticker": "{{ticker}}"
# }