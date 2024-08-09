import requests
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from datetime import datetime 
import numpy as np
import ta

pd.options.mode.chained_assignment = None

def get_okx_ohlcv(symbol, interval, limit):
    url = f'https://www.okx.com/api/v5/market/candles'
    params = {
        'instId': symbol,
        'bar': interval,
        'limit': 300
    }
    data = []
    response = requests.get(url, params=params)
    response = response.json()['data']
    data.extend(response)
    print ('DOWNLOAD')
    url = f'https://www.okx.com/api/v5/market/history-candles'
    while len(data) < limit:
        print (str(round(len(data) / limit*100))+'%')
        params = {
            'instId': symbol,
            'bar': interval,
            'limit': 100,
            'after': data[-1][0]
        }
        response = requests.get(url, params=params)
        try:
            response = response.json()['data']
            data.extend(response)
        except requests.exceptions.RequestException as err:
            print(f"Error: {err}")
            break
    return data

def macd_strategy(df):
    # Перевернуть DataFrame
    df_reversed = df[::-1]
    
    # Рассчитать MACD на перевернутом DataFrame
    macd = ta.trend.MACD(df_reversed['close'])
    df_reversed['macd'] = macd.macd()
    df_reversed['macd_signal'] = macd.macd_signal()

    # Перевернуть DataFrame обратно
    df = df_reversed[::-1]

    transactions = []
    profit_factor = 1.5
    profit_percent = 3
    open_price = 0
    open_time = 0
    type = 1 # 1 - long, -1 - short
    current_balance = 100
    balance = [[],[]]
    balance[0].append(current_balance)
    balance[1].append(df.index[-1])
    position_size = 1
    trade_open = False 

    for i in range(len(df) - 1, 0, -1):
        if trade_open:
            if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                close_price = tp
                close_time = df.index[i]
                result = 1
                trade_open = False
                transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                current_balance = current_balance+current_balance*position_size*0.01*profit_percent
                balance[0].append(current_balance)
                balance[1].append(df.index[i])
            elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                close_price = sl
                close_time = df.index[i]
                result = 0
                trade_open = False
                transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                current_balance = current_balance-current_balance*position_size*0.01*profit_percent/profit_factor
                balance[0].append(current_balance)
                balance[1].append(df.index[i])
            else:
                balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type)
                balance[1].append(df.index[i])  

        if not trade_open:
            if df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] < df['macd_signal'].iloc[i]:
                open_price = df['close'].iloc[i]
                open_time = df.index[i]
                tp = open_price * (1+0.01*profit_percent)
                sl = open_price * (1-0.01*profit_percent/profit_factor)
                type = 1
                trade_open = True
                balance[0].append(current_balance)
                balance[1].append(df.index[i]) 
            if df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                open_price = df['close'].iloc[i]
                open_time = df.index[i]
                tp = open_price * (1-0.01*profit_percent)
                sl = open_price * (1+0.01*profit_percent/profit_factor)
                type = -1
                trade_open = True
                balance[0].append(current_balance)
                balance[1].append(df.index[i])
    return transactions, balance

def macd_v2_strategy(df):
    # Перевернуть DataFrame
    df_reversed = df[::-1]
    
    # Рассчитать MACD на перевернутом DataFrame
    macd = ta.trend.MACD(df_reversed['close'])
    df_reversed['macd'] = macd.macd()
    df_reversed['macd_signal'] = macd.macd_signal()

    # Перевернуть DataFrame обратно
    df = df_reversed[::-1]

    transactions = []
    profit_factor = 1.5
    profit_percent = 3
    open_price = 0
    open_time = 0
    type = 1 # 1 - long, -1 - short
    current_balance = 100
    balance = [[],[]]
    balance[0].append(current_balance)
    balance[1].append(df.index[-1])
    position_size = 1
    trade_open = False 

    for i in range(len(df) - 1, 0, -1):
        if trade_open:
            if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                close_price = tp
                close_time = df.index[i]
                result = 1
                trade_open = False
                transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                current_balance = current_balance+current_balance*position_size*0.01*profit_percent
                balance[0].append(current_balance)
                balance[1].append(df.index[i])
            elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                close_price = sl
                close_time = df.index[i]
                result = 0
                trade_open = False
                transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                current_balance = current_balance-current_balance*position_size*0.01*profit_percent/profit_factor
                balance[0].append(current_balance)
                balance[1].append(df.index[i])
            else:
                balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type)
                balance[1].append(df.index[i])  

        if not trade_open:
            if df['macd_signal'].iloc[i-1] < df['macd_signal'].iloc[i-2] and df['macd_signal'].iloc[i] > df['macd_signal'].iloc[i-1]:
                open_price = df['close'].iloc[i]
                open_time = df.index[i]
                tp = open_price * (1+0.01*profit_percent)
                sl = open_price * (1-0.01*profit_percent/profit_factor)
                type = 1
                trade_open = True
                balance[0].append(current_balance)
                balance[1].append(df.index[i]) 
            if df['macd_signal'].iloc[i-1] > df['macd_signal'].iloc[i-2] and df['macd_signal'].iloc[i] < df['macd_signal'].iloc[i-1]:
                open_price = df['close'].iloc[i]
                open_time = df.index[i]
                tp = open_price * (1-0.01*profit_percent)
                sl = open_price * (1+0.01*profit_percent/profit_factor)
                type = -1
                trade_open = True
                balance[0].append(current_balance)
                balance[1].append(df.index[i])
    return transactions, balance


def plot_candlestick(df, transactions, balance):
    df['ts'] = pd.to_datetime(df.index, unit='ms', errors='coerce')
    df.set_index('ts', inplace=True)
    # Переворачиваем DataFrame
    df_reversed = df[::-1]
    
    # Рассчитываем MACD на перевернутом DataFrame
    macd = ta.trend.MACD(df_reversed['close'])
    df_reversed['macd'] = macd.macd()
    df_reversed['macd_signal'] = macd.macd_signal()
    
    # Переворачиваем DataFrame обратно
    df = df_reversed[::-1]

    fig, (ax1, ax3) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [2, 1]}, facecolor='#151924')
    ax1.set_facecolor('#151924')
    ax3.set_facecolor('#151924')

    # Рисуем свечи
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
    candlestick_data = zip(mdates.date2num(df.index.to_pydatetime()), df['open'], df['high'], df['low'], df['close'])
    for date, open, high, low, close in candlestick_data:
        color = '#089981' if close >= open else '#F23645'
        ax1.plot([date, date], [low, high], color=color, linewidth=0.6)
        ax1.plot([date, date], [open, close], color=color, linewidth=1.8)

    # Рисуем сделки 
    wins = 0
    losses = 0
    winrate = 0
    for tp, sl, open_price, open_time, close_time, close_price, type, result in transactions:
        if type == 1:
            ax1.plot(mdates.date2num(open_time), open_price, marker='^', color='lime', markersize=7)
            ax1.plot(mdates.date2num(close_time), close_price, marker='X', color='salmon', markersize=7)
        if type == -1:
            ax1.plot(mdates.date2num(open_time), open_price, marker='v', color='salmon', markersize=7)
            ax1.plot(mdates.date2num(close_time), close_price, marker='X', color='lime', markersize=7)
        if result == 1:
            wins += 1
        else:
            losses += 1
    winrate = round(wins/(wins+losses)*100, ndigits=2)
    profit = round((balance[0][-1]-balance[0][0])/balance[0][0]*100, ndigits=2)

    # Рисуем области tp и sl 
    for tp, sl, open_price, open_time, close_time, close_price, type, result in transactions:
        if type == 1:
            ax1.add_patch(plt.Rectangle(
                (mdates.date2num(open_time), open_price),
                 mdates.date2num(close_time) - mdates.date2num(open_time),
                tp - open_price,
                color='lightgreen', alpha=0.1
            ))
            ax1.add_patch(plt.Rectangle(
                (mdates.date2num(open_time), sl),
                 mdates.date2num(close_time) - mdates.date2num(open_time),
                open_price - sl,
                color='salmon', alpha=0.1
            ))
        if type == -1:
            ax1.add_patch(plt.Rectangle(
                (mdates.date2num(open_time), open_price),
                 mdates.date2num(close_time) - mdates.date2num(open_time),
                sl - open_price,
                color='salmon', alpha=0.1
            ))
            ax1.add_patch(plt.Rectangle(
                (mdates.date2num(open_time), tp),
                 mdates.date2num(close_time) - mdates.date2num(open_time),
                open_price - tp,
                color='lightgreen', alpha=0.1
            ))

    # Рисуем MACD
    ax2 = ax1.twinx()
    ax2.plot(df.index, df['macd'], label='MACD', color='blue', linestyle='--', alpha = 0.5)
    ax2.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', alpha = 0.5)

    # Рисуем баланс
    ax3.semilogy(balance[1], balance[0], label='Balance', color='#089981', linestyle='-')
    NbData = len(balance[1])
    MaxBL = [[MaxBL] * NbData for MaxBL in range(int(max(balance[0])+1))]
    Max = [np.asarray(MaxBL[x]) for x in range(int(max(balance[0])+1))]
    step = int((max(balance[0])-min(balance[0]))/20)
    if step == 0:
        step = 1
    for x in range (int(balance[0][0]), int(max(balance[0])), step):
        ax3.fill_between(balance[1], Max[x], balance[0], where=balance[0] >= Max[x], facecolor='#089981', alpha=0.05)
    for x in range (int(min(balance[0])), int(balance[0][0]), step):
        ax3.fill_between(balance[1], balance[0], Max[x], where=balance[0] <= Max[x], facecolor='#FF5045', alpha=0.05)
    max_drawdown = 0
    max_balance = 0
    for i in range(0, len(balance[0])):
        if max_balance < balance[0][i]:
            max_balance = balance[0][i]
        if (max_balance - balance[0][i]) * 100 / max_balance > max_drawdown:
            max_drawdown = (max_balance - balance[0][i]) * 100 / max_balance

    # Меняем цвет надписей
    ax1.tick_params(colors='white', direction='out')
    for tick in ax1.get_xticklabels():
        tick.set_color('white')
    for tick in ax1.get_yticklabels():
        tick.set_color('white')
    ax3.tick_params(colors='white', direction='out')
    for tick in ax3.get_xticklabels():
        tick.set_color('white')
    for tick in ax3.get_yticklabels():
        tick.set_color('white')

    # Рисуем линии на фоне
    ax1.grid(True, axis='both', linewidth=0.3, color='gray')
    ax3.grid(True, axis='both', linewidth=0.3, color='gray', which="both")

    # Четкие надписи внизу
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)

    # Легенды 
    ax2.legend(loc='upper left', edgecolor='white')
    ax3.legend(loc='upper left', edgecolor='white')
    text = dict()
    transform = ax1.transAxes
    textprops ={'size':'9'}
    period = balance[1][-1] - balance[1][0]
    period_days = f"{period.days} days"

    text[0] = ax1.text(0, -0.04, 'Winrate', transform = transform, ha = 'left', color = 'white', **textprops)
    text[1] = ax1.text(0, -0.07, str(winrate)+'%', transform = transform, ha = 'left', color = '#089981', **textprops)
    text[2] = ax1.text(0.15, -0.04, 'Profit', transform = transform, ha = 'left', color = 'white', **textprops)
    text[3] = ax1.text(0.15, -0.07, str(profit)+'%', transform = transform, ha = 'left', color = '#089981', **textprops)
    text[4] = ax1.text(0.3, -0.04, 'Trades', transform = transform, ha = 'left', color = 'white', **textprops)
    text[5] = ax1.text(0.3, -0.07, str(wins+losses), transform = transform, ha = 'left', color = 'white', **textprops)
    text[6] = ax1.text(0.45, -0.04, 'Period', transform = transform, ha = 'left', color = 'white', **textprops)
    text[7] = ax1.text(0.45, -0.07, period_days, transform = transform, ha = 'left', color = 'white', **textprops)
    text[8] = ax1.text(0.6, -0.04, 'Initial balance', transform = transform, ha = 'left', color = 'white', **textprops)
    text[9] = ax1.text(0.6, -0.07, str(balance[0][0])+' USDT', transform = transform, ha = 'left', color = '#089981', **textprops)
    text[10] = ax1.text(0.75, -0.04, 'Final balance', transform = transform, ha = 'left', color = 'white', **textprops)
    text[11] = ax1.text(0.75, -0.07, str(round(balance[0][-1], ndigits=1))+' USDT', transform = transform, ha = 'left', color = '#089981', **textprops)
    text[12] = ax1.text(0.9, -0.04, 'Max drawdown', transform = transform, ha = 'left', color = 'white', **textprops)
    text[13] = ax1.text(0.9, -0.07, str(round(max_drawdown, ndigits=1))+'%', transform = transform, ha = 'left', color = '#F23645', **textprops)
    text[14] = ax1.text(0.01, 0.02, 'CheetosTrading', transform = transform, ha = 'left', color = 'white')
    plt.subplots_adjust(left=0.04, bottom=0.03, right=1, top=1, hspace=0.12)
    plt.show()

if __name__ == '__main__':
    symbol = 'BTC-USDT'
    interval = '1H'
    limit = 5000
    data = get_okx_ohlcv(symbol, interval, limit)
    if data:
        df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
        df['ts'] = pd.to_datetime(df['ts'], unit='ms')
        df.set_index('ts', inplace=True)
        transactions, balance = macd_v2_strategy(df)
        plot_candlestick(df, transactions, balance)
