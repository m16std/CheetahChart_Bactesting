
import sys
from PyQt5.QtWidgets import  QMainWindow, QApplication, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QHBoxLayout, QComboBox, QSpinBox, QFormLayout, QProgressBar  # type: ignore
from PyQt5 import QtCore, QtGui, QtWidgets # type: ignore
from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot # type: ignore
import requests # type: ignore
import pandas as pd # type: ignore
import matplotlib as mpl # type: ignore
import matplotlib.pyplot as plt # type: ignore
import matplotlib.dates as mdates # type: ignore
from matplotlib.path import Path # type: ignore
from matplotlib.patches import PathPatch # type: ignore
from matplotlib.figure import Figure # type: ignore
import matplotlib.ticker as ticker # type: ignore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas # type: ignore
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar # type: ignore
import qdarktheme # type: ignore
from datetime import datetime 
import numpy as np # type: ignore
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure # type: ignore
import concurrent.futures
import ta # type: ignore

pd.options.mode.chained_assignment = None


class DataLoader(QThread):
    data_loaded = pyqtSignal(pd.DataFrame)

    def __init__(self, num_candles, num_threads, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_candles = num_candles
        self.num_threads = num_threads

    def run(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            candles_per_thread = self.num_candles // self.num_threads

            for i in range(self.num_threads):
                start_index = i * candles_per_thread
                end_index = (i + 1) * candles_per_thread
                futures.append(executor.submit(self.load_data_chunk, start_index, end_index))

            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            full_data = pd.concat(results).sort_index()

            self.data_loaded.emit(full_data)

    def load_data_chunk(self, start_index, end_index):
        # Replace with actual data loading logic
        time = np.arange(start_index, end_index)
        price = np.random.randn(end_index - start_index) + 100
        df = pd.DataFrame({'time': time, 'price': price})
        return df
    

class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig, (self.ax1, self.ax3) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [2, 1]}, facecolor='#151924')
        self.ax2 = self.ax1.twinx()
        self.ax1.set_facecolor('#151924')
        self.ax3.set_facecolor('#151924')
        # Меняем цвет надписей
        self.ax1.tick_params(colors='white', direction='out')
        for tick in self.ax1.get_xticklabels():
            tick.set_color('white')
        for tick in self.ax1.get_yticklabels():
            tick.set_color('white')
        self.ax3.tick_params(colors='white', direction='out')
        for tick in self.ax3.get_xticklabels():
            tick.set_color('white')
        for tick in self.ax3.get_yticklabels():
            tick.set_color('white')

        plt.subplots_adjust(left=0.04, bottom=0.03, right=1, top=1, hspace=0.12)
        super(MplCanvas, self).__init__(fig)

class CryptoTradingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()        
        
    def get_okx_ohlcv(self, symbol, interval, limit):
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
            self.bar.setValue(round(len(data) / limit*100)) 
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

        self.bar.setValue(100) 
        return data

    def macd_strategy(self, df):
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

        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        return transactions, balance

    def macd_v2_strategy(self, df):
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

        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        return transactions, balance

    def bollinger_vwap_rsi_strategy(self, df):
        # Убедиться, что все данные числовые
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # Перевернуть DataFrame для удобства расчета индикаторов
        df_reversed = df[::-1]
        
        # Рассчитать индикаторы на перевернутом DataFrame
        bollinger = ta.volatility.BollingerBands(df_reversed['close'])
        df_reversed['bollinger_high'] = bollinger.bollinger_hband()
        df_reversed['bollinger_low'] = bollinger.bollinger_lband()
        
        vwap = ta.volume.VolumeWeightedAveragePrice(
            df_reversed['high'], df_reversed['low'], df_reversed['close'], df_reversed['volume'], window = 200
        )
        df_reversed['vwap'] = vwap.vwap
        
        df_reversed['rsi'] = ta.momentum.RSIIndicator(df_reversed['close']).rsi()
        
        # Перевернуть DataFrame обратно для дальнейшего анализа
        df = df_reversed[::-1]

        transactions = []
        current_balance = 100
        balance = [[], []]
        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
        position_size = 1
        trade_open = False
        open_price = 0
        open_time = 0
        profit_factor = 1.5
        profit_percent = 1
        tp = 0
        sl = 0
        type = 0  # 1 - long, -1 - short

        for i in range(len(df)-201, 00, -1):
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
            else:
                if (df['close'].iloc[i] < df['bollinger_low'].iloc[i]) and \
                (df['close'].iloc[i-15:i] > df['vwap'].iloc[i-15:i]).all():
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    tp = open_price * (1+0.01*profit_percent)
                    sl = open_price * (1-0.01*profit_percent/profit_factor)
                    type = 1  # long
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                
                elif (df['close'].iloc[i] > df['bollinger_high'].iloc[i]) and \
                    (df['close'].iloc[i-15:i] < df['vwap'].iloc[i-15:i]).all():
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    tp = open_price * (1-0.01*profit_percent)
                    sl = open_price * (1+0.01*profit_percent/profit_factor)
                    type = -1  # short
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        return transactions, balance

    def plot_candlestick(self, df, transactions, balance):

        self.canvas.ax1.clear()
        self.canvas.ax3.clear()

        # Рисуем линии на фоне
        self.canvas.ax1.grid(True, axis='both', linewidth=0.3, color='gray')
        self.canvas.ax3.grid(True, axis='both', linewidth=0.3, color='gray', which="both")

        # Переворачиваем DataFrame
        df_reversed = df[::-1]

        # Расчитываем индикаторы
        macd = ta.trend.MACD(df_reversed['close'])
        df_reversed['macd'] = macd.macd()
        df_reversed['macd_signal'] = macd.macd_signal()
        bollinger = ta.volatility.BollingerBands(df_reversed['close'])
        df_reversed['bollinger_high'] = bollinger.bollinger_hband()
        df_reversed['bollinger_low'] = bollinger.bollinger_lband()
        vwap = ta.volume.VolumeWeightedAveragePrice(df_reversed['high'], df_reversed['low'], df_reversed['close'], df_reversed['volume'], window = 200)
        df_reversed['vwap'] = vwap.vwap
        df_reversed['rsi'] = ta.momentum.RSIIndicator(df_reversed['close']).rsi()
        
        # Переворачиваем DataFrame обратно
        df = df_reversed[::-1]

        # Рисуем индикаторы
        """
        ax2.plot(df.index, df['macd'], label='MACD', color='blue', linestyle='--', alpha = 0.5)
        ax2.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', alpha = 0.5)
        """
        self.canvas.ax1.plot(df.index, df['bollinger_high'], label='BB High', color='red', alpha = 0.5)
        self.canvas.ax1.plot(df.index, df['bollinger_low'], label='BB Low', color='green', alpha = 0.5)
        self.canvas.ax1.plot(df.index, df['vwap'], label='VWAP', color='orange', linestyle='--', alpha = 0.5)
        #ax2.plot(df.index, df['rsi'], label='RSI', color='blue', linestyle='--', alpha = 0.5)

        # Рисуем свечи
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
        candlestick_data = zip(mdates.date2num(df.index.to_pydatetime()), df['open'], df['high'], df['low'], df['close'])
        for date, open, high, low, close in candlestick_data:
            color = '#089981' if close >= open else '#F23645'
            self.canvas.ax1.plot([date, date], [low, high], color=color, linewidth=0.8)
            self.canvas.ax1.plot([date, date], [open, close], color=color, linewidth=2)

        # Рисуем сделки 
        wins = 0
        losses = 0
        winrate = 0
        for tp, sl, open_price, open_time, close_time, close_price, type, result in transactions:
            if type == 1:
                self.canvas.ax1.plot(mdates.date2num(open_time), open_price, marker='^', color='lime', markersize=7)
                self.canvas.ax1.plot(mdates.date2num(close_time), close_price, marker='X', color='salmon', markersize=7)
            if type == -1:
                self.canvas.ax1.plot(mdates.date2num(open_time), open_price, marker='v', color='salmon', markersize=7)
                self.canvas.ax1.plot(mdates.date2num(close_time), close_price, marker='X', color='lime', markersize=7)
            if result == 1:
                wins += 1
            else:
                losses += 1
        if wins+losses == 0:
            winrate = 0
        else:
            winrate = round(wins/(wins+losses)*100, ndigits=2)
        profit = round((balance[0][-1]-balance[0][0])/balance[0][0]*100, ndigits=2)

        # Рисуем области tp и sl 
        for tp, sl, open_price, open_time, close_time, close_price, type, result in transactions:
            if type == 1:
                self.canvas.ax1.add_patch(plt.Rectangle(
                    (mdates.date2num(open_time), open_price),
                    mdates.date2num(close_time) - mdates.date2num(open_time),
                    tp - open_price,
                    color='lightgreen', alpha=0.1
                ))
                self.canvas.ax1.add_patch(plt.Rectangle(
                    (mdates.date2num(open_time), sl),
                    mdates.date2num(close_time) - mdates.date2num(open_time),
                    open_price - sl,
                    color='salmon', alpha=0.1
                ))
            if type == -1:
                self.canvas.ax1.add_patch(plt.Rectangle(
                    (mdates.date2num(open_time), open_price),
                    mdates.date2num(close_time) - mdates.date2num(open_time),
                    sl - open_price,
                    color='salmon', alpha=0.1
                ))
                self.canvas.ax1.add_patch(plt.Rectangle(
                    (mdates.date2num(open_time), tp),
                    mdates.date2num(close_time) - mdates.date2num(open_time),
                    open_price - tp,
                    color='lightgreen', alpha=0.1
                ))

        # Рисуем баланс
        self.canvas.ax3.plot(balance[1], balance[0], label='Balance', color='#089981', linestyle='-')
        NbData = len(balance[1])
        MaxBL = [[MaxBL] * NbData for MaxBL in range(int(max(balance[0])+1))]
        Max = [np.asarray(MaxBL[x]) for x in range(int(max(balance[0])+1))]
        step = int((max(balance[0])-min(balance[0]))/20)
        if step == 0:
            step = 1
        for x in range (int(balance[0][0]), int(max(balance[0])), step):
            self.canvas.ax3.fill_between(balance[1], Max[x], balance[0], where=balance[0] >= Max[x], facecolor='#089981', alpha=0.05)
        for x in range (int(min(balance[0])), int(balance[0][0]), step):
            self.canvas.ax3.fill_between(balance[1], balance[0], Max[x], where=balance[0] <= Max[x], facecolor='#FF5045', alpha=0.05)
        max_drawdown = 0
        max_balance = 0
        for i in range(0, len(balance[0])):
            if max_balance < balance[0][i]:
                max_balance = balance[0][i]
            if (max_balance - balance[0][i]) * 100 / max_balance > max_drawdown:
                max_drawdown = (max_balance - balance[0][i]) * 100 / max_balance

        for label in self.canvas.ax3.get_yticklabels(which='both'):
            label.set_color("white")

        # Четкие надписи внизу графика цен
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        self.canvas.ax1.xaxis.set_major_locator(locator)
        self.canvas.ax1.xaxis.set_major_formatter(formatter)

        # Легенды 
        self.canvas.ax2.legend(loc='upper left', edgecolor='white')
        self.canvas.ax3.legend(loc='upper left', edgecolor='white')

        # Побочная инфа
        text = dict()
        transform = self.canvas.ax1.transAxes
        textprops ={'size':'10'}
        period = balance[1][-1] - balance[1][0]
        period_days = f"{period.days} days"
        text[0] = self.canvas.ax1.text(0, -0.04, 'Winrate', transform = transform, ha = 'left', color = 'white', **textprops)
        text[1] = self.canvas.ax1.text(0, -0.075, str(winrate)+'%', transform = transform, ha = 'left', color = '#089981', **textprops)
        text[2] = self.canvas.ax1.text(0.15, -0.04, 'Profit', transform = transform, ha = 'left', color = 'white', **textprops)
        text[3] = self.canvas.ax1.text(0.15, -0.075, str(profit)+'%', transform = transform, ha = 'left', color = '#089981', **textprops)
        text[4] = self.canvas.ax1.text(0.3, -0.04, 'Trades', transform = transform, ha = 'left', color = 'white', **textprops)
        text[5] = self.canvas.ax1.text(0.3, -0.075, str(wins+losses), transform = transform, ha = 'left', color = 'white', **textprops)
        text[6] = self.canvas.ax1.text(0.45, -0.04, 'Period', transform = transform, ha = 'left', color = 'white', **textprops)
        text[7] = self.canvas.ax1.text(0.45, -0.075, period_days, transform = transform, ha = 'left', color = 'white', **textprops)
        text[8] = self.canvas.ax1.text(0.6, -0.04, 'Initial balance', transform = transform, ha = 'left', color = 'white', **textprops)
        text[9] = self.canvas.ax1.text(0.6, -0.075, str(balance[0][0])+' USDT', transform = transform, ha = 'left', color = '#089981', **textprops)
        text[10] = self.canvas.ax1.text(0.75, -0.04, 'Final balance', transform = transform, ha = 'left', color = 'white', **textprops)
        text[11] = self.canvas.ax1.text(0.75, -0.075, str(round(balance[0][-1], ndigits=1))+' USDT', transform = transform, ha = 'left', color = '#089981', **textprops)
        text[12] = self.canvas.ax1.text(0.9, -0.04, 'Max drawdown', transform = transform, ha = 'left', color = 'white', **textprops)
        text[13] = self.canvas.ax1.text(0.9, -0.075, str(round(max_drawdown, ndigits=1))+'%', transform = transform, ha = 'left', color = '#F23645', **textprops)
        text[14] = self.canvas.ax1.text(0.01, 0.02, 'CheetosTrading', transform = transform, ha = 'left', color = 'white')

        self.canvas.draw()
        self.show()

    def initUI(self):
        self.setWindowTitle('Crypto Trading Strategies')
        self.setStyleSheet("background-color: #151924;")

        self.data_loader = None
        self.current_data = None
        self.setGeometry(100, 100, 1600, 900)

        layout = QVBoxLayout(self)

        self.symbol_input = QComboBox(self)
        self.symbol_input.addItems(['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'PEPE-USDT', 'TON-USDT', 'BNB-USDT'])

        self.interval_input = QComboBox(self)
        self.interval_input.addItems(['1m', '5m', '15m', '1H', '4H', '1D'])

        self.limit_input = QSpinBox(self)
        self.limit_input.setRange(100, 100000)
        self.limit_input.setValue(1000)

        self.strat_input = QComboBox(self)
        self.strat_input.addItems(['MACD', 'MACD v2', 'Bollinger + VWAP + RSI'])

        form_layout = QFormLayout()
        symbol_label = QtWidgets.QLabel('Symbol:')
        interval_label = QtWidgets.QLabel('Interval:')
        limit_label = QtWidgets.QLabel('Limit:')
        strategy_label = QtWidgets.QLabel('Strategy:')
        download_label = QtWidgets.QLabel('Donwload:')

        symbol_label.setFont(QtGui.QFont('Trebuchet MS', 10))
        interval_label.setFont(QtGui.QFont('Trebuchet MS', 10))
        limit_label.setFont(QtGui.QFont('Trebuchet MS', 10))
        strategy_label.setFont(QtGui.QFont('Trebuchet MS', 10))
        download_label.setFont(QtGui.QFont('Trebuchet MS', 10))

        form_layout.addRow(symbol_label, self.symbol_input)
        form_layout.addRow(interval_label, self.interval_input)
        form_layout.addRow(limit_label, self.limit_input)
        form_layout.addRow(strategy_label, self.strat_input)

        self.bar = QProgressBar(self) 
        self.bar.setGeometry(200, 100, 200, 30) 
        self.bar.setValue(0) 
        self.bar.setAlignment(Qt.AlignCenter) 
        
        form_layout.addRow(download_label, self.bar)

        self.run_button = QPushButton('Run Strategy', self)
        self.run_button.clicked.connect(self.run_strategy)

        layout.addLayout(form_layout)
        layout.addWidget(self.run_button)

        # Создаем canvas и добавляем в layout
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        layout.addWidget(self.canvas)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("QToolButton { color: white; }")
        layout.addWidget(self.toolbar)

        # Настраиваем политику размера для динамического изменения
        self.canvas.setSizePolicy(
            self.sizePolicy().Expanding,
            self.sizePolicy().Expanding
        )
        self.canvas.updateGeometry()
        self.show()

    def run_strategy(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()

        if not symbol:
            self.result_label.setText("Please enter a valid symbol")
            return

        data = self.get_okx_ohlcv(symbol, interval, limit)
        df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        df[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']] = df[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']].astype(float)
        df['ts'] = pd.to_datetime(df['ts'], unit='ms')
        df.set_index('ts', inplace=True)
        
        self.current_strategy = self.macd_strategy
        if self.strat_input.currentText() == "MACD":
            self.current_strategy = self.macd_strategy
        elif self.strat_input.currentText() == "MACD v2":
            self.current_strategy = self.macd_v2_strategy
        elif self.strat_input.currentText() == "Bollinger + VWAP + RSI":
            self.current_strategy = self.bollinger_vwap_rsi_strategy

        transactions, balance = self.current_strategy(df)
        self.plot_candlestick(df, transactions, balance)


def main():
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    ex = CryptoTradingApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

