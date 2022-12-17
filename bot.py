import binance
from binance import Client
import ccxt
import pandas as pd
from API import api_key_bybit, api_secret_bybit
import time
from datetime import datetime
import ta
from ta import trend, momentum, volatility

# -------------- Debut de Session ---------------

now = datetime.now()
heure_actuelle = now.strftime('%d/%m/%Y  %H:%M:%S')
print("------", heure_actuelle, "------")

# ---------------------- Connection au compte ---------------------
exchange = ccxt.bybit({
    'apiKey' : api_key_bybit,
    'secret' : api_secret_bybit,
})

# ----------------------- Check de la balance -------------------
balance = exchange.fetch_balance()
usdt_free = balance['USDT']['free']
usdt_used = balance['USDT']['used']
usdt_total = balance['USDT']['total']
btc_used = balance['BTC']['used']
btc_free = balance['BTC']['free']
btc_total = balance['BTC']['total']


# ------------------------ Informations marché -------------------------
market = exchange.load_markets()
coin = 'BTC/USDT:USDT'

# ------------ Date en millisecondes ----------------------
starting_day = '12/12/2021'
starting_day = time.strptime(starting_day,'%d/%m/%Y')
starting_day = time.mktime(starting_day)
starting_day = starting_day * 1000

# ------------------------ Recupération & Organisation Data historiques ------------------------

client = Client()
data = client.get_historical_klines('BTCUSDT', interval=client.KLINE_INTERVAL_1HOUR)
prix = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av'
    , 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])


prix['open'] = pd.to_numeric(prix['open'])
prix['high'] = pd.to_numeric(prix['high'])
prix['low'] = pd.to_numeric(prix['low'])
prix['close'] = pd.to_numeric(prix['close'])

prix = prix.set_index(prix['timestamp'])
prix.index = pd.to_datetime(prix.index, unit='ms')
del prix['timestamp']
prix.drop(prix.columns.difference(['open', 'high', 'low', 'close']), axis=1, inplace=True)

# ----------------------- Definir les indicateurs ----------------------------
prix['EMA1'] = ta.trend.ema_indicator(prix['close'], window=7)
prix['EMA2'] = ta.trend.ema_indicator(prix['close'], window=30)
prix['EMA3'] = ta.trend.ema_indicator(prix['close'], window=50)
prix['EMA4'] = ta.trend.ema_indicator(prix['close'], window=100)
prix['EMA5'] = ta.trend.ema_indicator(prix['close'], window=121)
prix['EMA6'] = ta.trend.ema_indicator(prix['close'], window=200)
prix['RSI'] = ta.momentum.stochrsi(prix['close'], window=14, smooth1=3, smooth2=3)
prix['ATR'] = ta.volatility.average_true_range(high=prix['high'], low=prix['low'], close=prix['close'], window=14)

prix_copy = prix.copy()

# ------------------ Fonction long -------------------
def open_long(row):
    if row['EMA1'][-1] > row['EMA2'][-1] and row['EMA2'][-1] > row['EMA3'][-1]and row['EMA3'][-1] > row['EMA4'][-1] and row['EMA4'][-1] > row['EMA5'][-1]and row['EMA5'][-1] > row['EMA6'][-1] and row['RSI'][-1] < 0.82:
        return True
    else:
        return False


def close_long(row):
    if row['EMA6'][-1] > row['EMA1'][-1] and row['RSI'][-1] > 0.2:
        return True
    else:
        return False

# ------------------------------- Ordres possibilités -------------------------------------

# ----------------- Montant d'achat ----------------------
bitcoin_price = exchange.fetch_ticker(coin)
actual_price = (bitcoin_price['bid'] + bitcoin_price['ask']) / 2
amount_position = usdt_free / actual_price

# ------------------ Ordre Long ------------------------
def ouvrir(row):
    global btc_total
    global usdt_free
    global amount_position
    buy_price = row['close'][-1]
    stop_loss = buy_price - 2 * row['ATR'][-1]
    take_profit = buy_price + 4 * row['ATR'][-1]
    if open_long(row) == True and usdt_free > 0:
        print("Prise de position long")
        # exchange.create_market_buy_order(symbol=coin, amount= amount_position)
# ---------------- Ordre Take profit ---------------------
    elif row['high'][-1] < take_profit and btc_total > 0:
        print("TP", row['high'][-1], take_profit)
        # exchange.create_market_sell_order(symbol=coin, amount=btc_total)
        print("Take profit")
# ----------------------Ordre Stop Loss -----------------------------
    elif row['low'][-1] < stop_loss and btc_total > 0:
        print("Stop Loss")
        # exchange.create_market_sell_order(symbol=coin, amount=btc_total)
    elif close_long(row) == True and btc_total > 0:
        # exchange.create_market_sell_order(symbol=coin, amount=btc_total)
        print("Fermeture de position long")
    else:
        print("Il ne se passe rien ....")



ouvrir(prix)
""""""""""

def sleep(seconds):
    time.sleep(seconds)

# Mettre en veille le script pendant 1 heure
sleep(3600)

ordres = exchange.fetch_my_trades(coin)
"""""""""""