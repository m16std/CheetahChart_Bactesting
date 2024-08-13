
import sys
from PyQt5.QtWidgets import  QMainWindow, QApplication, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QHBoxLayout, QComboBox, QSpinBox, QFormLayout, QProgressBar, QFileDialog  # type: ignore
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
import mplfinance as mpf # type: ignore
from sklearn.preprocessing import MinMaxScaler  # type: ignore
from tensorflow.keras.models import Sequential  # type: ignore
from tensorflow.keras.layers import Dense, LSTM  # type: ignore
import joblib  # type: ignore

pd.options.mode.chained_assignment = None

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
        
    def initUI(self):
        self.setWindowTitle('Cheetos Trading')
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
        self.strat_input.addItems(['Supertrend', 'Bollinger v2','Bollinger + VWAP', 'MACD v2', 'MACD'])

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
        layout.addLayout(form_layout)


        button_layout = QHBoxLayout()

        self.run_button = QPushButton('Run Strategy', self)
        self.run_button.clicked.connect(self.load_and_run)
        button_layout.addWidget(self.run_button)
        
        self.save_button = QPushButton('Save Candlesticks', self)
        self.save_button.clicked.connect(self.save_candlesticks)
        button_layout.addWidget(self.save_button)
        
        self.load_button = QPushButton('Load Candlesticks', self)
        self.load_button.clicked.connect(self.load_candlesticks)
        button_layout.addWidget(self.load_button)

        self.tai_button = QPushButton('Train AI', self)
        self.tai_button.clicked.connect(self.train_ai)
        button_layout.addWidget(self.tai_button)

        self.rai_button = QPushButton('Run AI', self)
        self.rai_button.clicked.connect(self.run_ai)
        button_layout.addWidget(self.rai_button)

        layout.addLayout(button_layout)

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

    def save_candlesticks(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        data = self.get_okx_ohlcv(symbol, interval, limit)
        self.df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        self.df[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']] = self.df[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']].astype(float)
        self.df['ts'] = pd.to_datetime(self.df['ts'], unit='ms')
        self.df.set_index('ts', inplace=True)

        file_name, _ = QFileDialog.getSaveFileName(self, "Save Candlestick Data", "", "CSV Files (*.csv)")
        if file_name:
            self.df.to_csv(file_name)
            print(f"Candlestick data saved to {file_name}")
        else:
            print('suka')

    def load_candlesticks(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Candlestick Data", "", "CSV Files (*.csv)")
        if file_name:
            self.df = pd.read_csv(file_name, index_col=0, parse_dates=True)
            print(f"Candlestick data loaded from {file_name}")
            self.run_strategy()

    def load_and_run(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()

        data = self.get_okx_ohlcv(symbol, interval, limit)

        self.df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        self.df[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']] = self.df[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']].astype(float)
        self.df['ts'] = pd.to_datetime(self.df['ts'], unit='ms')
        self.df.set_index('ts', inplace=True)
        
        self.run_strategy()

    def run_strategy(self):
        self.current_strategy = self.macd_strategy
        if self.strat_input.currentText() == "MACD":
            self.current_strategy = self.macd_strategy
        elif self.strat_input.currentText() == "MACD v2":
            self.current_strategy = self.macd_v2_strategy
        elif self.strat_input.currentText() == "Bollinger + VWAP":
            self.current_strategy = self.bollinger_vwap_strategy
        elif self.strat_input.currentText() == "Bollinger v2":
            self.current_strategy = self.bollinger_v2
        elif self.strat_input.currentText() == "Supertrend":
            self.current_strategy = self.supertrend_strategy

        self.canvas.ax1.clear()
        self.canvas.ax2.clear()
        self.canvas.ax3.clear()
        transactions, balance = self.current_strategy(self.df)
        self.plot_candlestick(self.df, transactions, balance)

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

        df = df_reversed[::-1]

        # Рисуем индикаторы
        self.canvas.ax2.plot(df.index, df['macd'], label='MACD', color='blue', linestyle='--', alpha = 0.5)
        self.canvas.ax2.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', alpha = 0.5)

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
        percent5 = int(len(df) / 50)

        for i in range(len(df) - 1, 0, -1):
            if (len(df)-i) % percent5 == 0:
                self.bar.setValue(int((len(df)-i) / len(df) * 100)) 
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
        bollinger = ta.volatility.BollingerBands(df_reversed['close'])
        df_reversed['macd'] = macd.macd()
        df_reversed['macd_signal'] = macd.macd_signal()
        df_reversed['bollinger_high'] = bollinger.bollinger_hband()
        df_reversed['bollinger_low'] = bollinger.bollinger_lband()

        df = df_reversed[::-1]

        # Рисуем индикаторы
        self.canvas.ax2.plot(df.index, df['macd'], label='MACD', color='blue', linestyle='--', alpha = 0.5)
        self.canvas.ax2.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', alpha = 0.5)
        self.canvas.ax1.plot(df.index, df['bollinger_high'], label='BB High', color='red', alpha = 0.5)
        self.canvas.ax1.plot(df.index, df['bollinger_low'], label='BB Low', color='green', alpha = 0.5)

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

    def bollinger_vwap_strategy(self, df):
        # Убедиться, что все данные числовые
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # Перевернуть DataFrame для удобства расчета индикаторов
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

        df = df_reversed[::-1]
        
        # Рисуем индикаторы
        self.canvas.ax1.plot(df.index, df['bollinger_high'], label='BB High', color='red', alpha = 0.5)
        self.canvas.ax1.plot(df.index, df['bollinger_low'], label='BB Low', color='green', alpha = 0.5)
        self.canvas.ax1.plot(df.index, df['vwap'], label='VWAP', color='orange', linestyle='--', alpha = 0.5)

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

    def bollinger_v2(self, df):
        # Убедиться, что все данные числовые
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

        df_reversed = df[::-1]

        # Расчитываем индикаторы
        macd = ta.trend.MACD(df_reversed['close'])
        df_reversed['macd'] = macd.macd()
        df_reversed['macd_signal'] = macd.macd_signal()
        bollinger = ta.volatility.BollingerBands(df_reversed['close'])
        df_reversed['bollinger_high'] = bollinger.bollinger_hband()
        df_reversed['bollinger_low'] = bollinger.bollinger_lband()

        df = df_reversed[::-1]

        # Рисуем индикаторы
        self.canvas.ax1.plot(df.index, df['bollinger_high'], label='BB High', color='red', alpha = 0.5)
        self.canvas.ax1.plot(df.index, df['bollinger_low'], label='BB Low', color='green', alpha = 0.5)

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
                if (df['low'].iloc[i] < df['bollinger_low'].iloc[i]) and (df['close'].iloc[i] > df['open'].iloc[i]) and ((df['bollinger_high'].iloc[i] - df['bollinger_low'].iloc[i]) / ((df['bollinger_high'].iloc[i] + df['bollinger_low'].iloc[i])/2) > 0.03):
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    tp = open_price * (1+0.01*profit_percent)
                    sl = open_price * (1-0.01*profit_percent/profit_factor)
                    type = 1  # long
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                
                if (df['high'].iloc[i] > df['bollinger_high'].iloc[i]) and (df['close'].iloc[i] < df['open'].iloc[i])and ((df['bollinger_high'].iloc[i] - df['bollinger_low'].iloc[i]) / ((df['bollinger_high'].iloc[i] + df['bollinger_low'].iloc[i])/2) > 0.03):
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
    
    def Supertrend(self, df, atr_period, multiplier):
        high = df['high']
        low = df['low']
        close = df['close']
        
        # calculate ATR
        price_diffs = [high - low, 
                    high - close.shift(), 
                    close.shift() - low]
        true_range = pd.concat(price_diffs, axis=1)
        true_range = true_range.abs().max(axis=1)
        atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean() 
        # df['atr'] = df['tr'].rolling(atr_period).mean()
        
        # HL2 is simply the average of high and low prices
        hl2 = (high + low) / 2
        final_upperband = upperband = hl2 + (multiplier * atr)
        final_lowerband = lowerband = hl2 - (multiplier * atr)
        
        # initialize Supertrend column to True
        supertrend = [True] * len(df)
        
        for i in range(1, len(df.index)):
            
            # if current close price crosses above upperband
            if close.iloc[i] > final_upperband.iloc[i-1]:
                supertrend[i] = True
            # if current close price crosses below lowerband
            elif close.iloc[i] < final_lowerband.iloc[i-1]: 
                supertrend[i] = False
            # else, the trend continues
            else:
                supertrend[i] = supertrend[i-1]
                
                # adjustment to the final bands
                if supertrend[i] == True and final_lowerband.iloc[i] < final_lowerband.iloc[i-1]:
                    final_lowerband.iloc[i] = final_lowerband.iloc[i-1]
                if supertrend[i] == False and final_upperband.iloc[i] > final_upperband.iloc[i-1]:
                    final_upperband.iloc[i] = final_upperband.iloc[i-1]

            # to remove bands according to the trend direction
            if supertrend[i] == True:
                final_upperband.iloc[i] = np.nan
            else:
                final_lowerband.iloc[i] = np.nan
        
        return pd.DataFrame({
            'Supertrend': supertrend,
            'Final Lowerband': final_lowerband,
            'Final Upperband': final_upperband
        }, index=df.index)

    def supertrend_strategy(self, df):
        df_reversed = df[::-1]
        period = 16
        multiplier = 5

        # Calculate SuperTrend
        sti = self.Supertrend(df_reversed, period, multiplier)
        df_reversed = df_reversed.join(sti)
        macd = ta.trend.MACD(df_reversed['close'])
        df_reversed['macd'] = macd.macd()
        df_reversed['macd_signal'] = macd.macd_signal()
        bollinger = ta.volatility.BollingerBands(df_reversed['close'])
        df_reversed['bollinger_high'] = bollinger.bollinger_hband()
        df_reversed['bollinger_low'] = bollinger.bollinger_lband()
        vwap = ta.volume.VolumeWeightedAveragePrice(df_reversed['high'], df_reversed['low'], df_reversed['close'], df_reversed['volume'], window = 500)
        df_reversed['vwap'] = vwap.vwap

        df = df_reversed[::-1]
        
        # Рисуем индикаторы
        #self.canvas.ax1.plot(df.index, df['bollinger_high'], label='BB High', color='white', alpha = 0.5)
        #self.canvas.ax1.plot(df.index, df['bollinger_low'], label='BB Low', color='white', alpha = 0.5)
        #self.canvas.ax1.plot(df.index, df['vwap'], label='VWAP', color='orange', linestyle='--', alpha = 0.5)
        #self.canvas.ax2.plot(df.index, df['macd'], label='Macd', color='white', alpha = 0.5)
        #self.canvas.ax2.plot(df.index, df['macd_signal'], label='Macd signal', color='blue', alpha = 0.5)
        #self.canvas.ax2.plot(df.index, df['Supertrend'], label='SuperTrend', color='yellow', linestyle='--', alpha=0.5)
        self.canvas.ax1.plot(df.index, df['Final Lowerband'], label='Final Lowerband', color='green', linestyle='--', alpha=0.5)
        self.canvas.ax1.plot(df.index, df['Final Upperband'], label='Final Upperband', color='red', linestyle='--', alpha=0.5)

        transactions = []
        open_price = 0
        open_time = 0
        type = 1  # 1 - long, -1 - short
        current_balance = 100
        balance = [[], []]
        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
        position_size = 1
        trade_open = False
        percent5 = int(len(df) / 50)

        for i in range(len(df) - 12, 0, -1):
            if (len(df) - i) % percent5 == 0:
                self.bar.setValue(int((len(df) - i) / len(df) * 100))
            
            if trade_open:
                if df['Supertrend'].iloc[i+1] != df['Supertrend'].iloc[i]:
                    if type == 1:
                        close_price = df['Final Lowerband'].iloc[i+1]
                    else:
                        close_price = df['Final Upperband'].iloc[i+1]
                    close_time = df.index[i]
                    result = 1 if (type == 1 and close_price > open_price) or \
                                (type == -1 and close_price < open_price) else 0
                    if result == 1:
                        tp = close_price
                        sl = open_price
                        current_balance += current_balance * position_size * abs((close_price - open_price) / open_price)
                    else:
                        tp = open_price
                        sl = close_price
                        current_balance -= current_balance * position_size * abs((close_price - open_price) / open_price)
                    transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                    trade_open = False
                else:
                    balance[0].append(current_balance + current_balance * position_size * ((df['open'].iloc[i] + df['close'].iloc[i]) / 2 / open_price - 1) * type)
                    balance[1].append(df.index[i])

            if not trade_open:
                if df['Supertrend'].iloc[i+1] < df['Supertrend'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                elif df['Supertrend'].iloc[i+1] > df['Supertrend'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[0])

        wins = 0
        losses = 0
        winrate = 0
        for tp, sl, open_price, open_time, close_time, close_price, type, result in transactions:
            if result == 1:
                wins += 1
            else:
                losses += 1
        if wins+losses == 0:
            winrate = 0
        else:
            winrate = round(wins/(wins+losses)*100, ndigits=2)
        profit = round((balance[0][-1]-balance[0][0])/balance[0][0]*100, ndigits=2)

        """
        print(str('period: ' + str(period)))
        print(str('multiplier: ' + str(multiplier)))

        print(str('Profit: ' + str(profit)))
        print(str('Winrate: ' + str(winrate)))
        print(str('Trades: ' + str(wins+losses)+'\n'))
        """

        return transactions, balance

    def plot_candlestick(self, df, transactions, balance):

        # Рисуем линии на фоне
        self.canvas.ax1.grid(True, axis='both', linewidth=0.3, color='gray')
        self.canvas.ax3.grid(True, axis='both', linewidth=0.3, color='gray', which="both")


        wins = 0
        losses = 0
        winrate = 0
        for tp, sl, open_price, open_time, close_time, close_price, type, result in transactions:
            if result == 1:
                wins += 1
            else:
                losses += 1
        if wins+losses == 0:
            winrate = 0
        else:
            winrate = round(wins/(wins+losses)*100, ndigits=2)
        profit = round((balance[0][-1]-balance[0][0])/balance[0][0]*100, ndigits=2)


        if len(df) <= 10000:
            percent5 = int(len(df) / 20)
            index = 0 
            # Рисуем свечи
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
            candlestick_data = zip(mdates.date2num(df.index.to_pydatetime()), df['open'], df['high'], df['low'], df['close'])
            for date, open, high, low, close in candlestick_data:
                if index % percent5 == 0:
                    self.bar.setValue(int(index / len(df) * 100))
                index += 1
                color = '#089981' if close >= open else '#F23645'
                self.canvas.ax1.plot([date, date], [low, high], color=color, linewidth=0.8)
                self.canvas.ax1.plot([date, date], [open, close], color=color, linewidth=2)

            self.bar.setValue(0)
            # Рисуем сделки 
            for tp, sl, open_price, open_time, close_time, close_price, type, result in transactions:
                if type == 1:
                    self.canvas.ax1.plot(mdates.date2num(open_time), open_price, marker='^', color='lime', markersize=7)
                    self.canvas.ax1.plot(mdates.date2num(close_time), close_price, marker='X', color='salmon', markersize=7)
                if type == -1:
                    self.canvas.ax1.plot(mdates.date2num(open_time), open_price, marker='v', color='salmon', markersize=7)
                    self.canvas.ax1.plot(mdates.date2num(close_time), close_price, marker='X', color='lime', markersize=7)

            self.bar.setValue(20)

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

        self.bar.setValue(40)

        # Рисуем баланс
        index = 0 
        self.canvas.ax3.plot(balance[1], balance[0], label='Balance', color='#089981', linestyle='-')
        NbData = len(balance[1])
        MaxBL = [[MaxBL] * NbData for MaxBL in range(int(max(balance[0])+1))]
        Max = [np.asarray(MaxBL[x]) for x in range(int(max(balance[0])+1))]
        step = int((max(balance[0])-min(balance[0]))/20)
        self.bar.setValue(60)
        if step == 0:
            step = 1
        for x in range (int(balance[0][0]), int(max(balance[0])), step):
            self.canvas.ax3.fill_between(balance[1], Max[x], balance[0], where=balance[0] >= Max[x], facecolor='#089981', alpha=0.05)
        for x in range (int(min(balance[0])), int(balance[0][0]), step):
            self.canvas.ax3.fill_between(balance[1], balance[0], Max[x], where=balance[0] <= Max[x], facecolor='#FF5045', alpha=0.05)
        max_drawdown = 0
        max_balance = 0
        self.bar.setValue(80)
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
        self.canvas.ax1.legend(loc='upper left', edgecolor='white') 
        self.canvas.ax2.legend(loc='upper right', edgecolor='white')
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
        self.bar.setValue(100)
        self.canvas.draw()
        self.show()

    # Формирование обучающих и тестовых данных
    def create_dataset(self, dataset, time_step=1):
        X, Y = [], []
        for i in range(len(dataset) - time_step - 1):
            X.append(dataset[i:(i + time_step), 0])
            Y.append(dataset[i + time_step, 0])
        return np.array(X), np.array(Y)

    def train_ai(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Candlestick Data", "", "CSV Files (*.csv)")
        if file_name:
            self.df = pd.read_csv(file_name, index_col=0, parse_dates=True)
            print(f"Candlestick data loaded from {file_name}")

        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(self.df['close'].values.reshape(-1, 1))

        time_step = 5
        X, Y = self.create_dataset(scaled_data, time_step)
        X = X.reshape(X.shape[0], X.shape[1], 1)

        # Обучение модели LSTM
        self.model = Sequential()
        self.model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 1)))
        self.model.add(LSTM(50, return_sequences=False))
        self.model.add(Dense(25))
        self.model.add(Dense(1))
        self.model.compile(optimizer='adam', loss='mean_squared_error')
        self.model.fit(X, Y, epochs=5, batch_size=1, verbose=1)

        self.save_model_dialog()

    # Предсказания модели
    def predict_with_lstm(self, data, scaler, time_step=5):
        data_scaled = scaler.transform(data.reshape(-1, 1))
        X_test, _ = self.create_dataset(data_scaled, time_step)
        X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)
        predictions =  self.model.predict(X_test)
        predictions = scaler.inverse_transform(predictions)
        return predictions

    # Определение стратегий
    def strategy_with_lstm(self, data, scaler):
        predictions = self.predict_with_lstm(data, scaler)
        data = pd.DataFrame(data, columns=['close']) 
        data['Predictions'] = np.nan
        data['Predictions'].iloc[-len(predictions):] = predictions.flatten()
        data['Signal'] = np.where(data['Predictions'] > data['close'].shift(1), 1, -1)
        #self.canvas.ax2.plot(data.index, data['Predictions'], label='Predictions', color='white', alpha = 0.5)
        #self.canvas.ax2.plot(data.index, data['Signal'], label='Signal', color='blue', alpha = 0.5)
        self.df[['open', 'high', 'low', 'close']] = self.df[['open', 'high', 'low', 'close']].astype(float)
        candlestick_data = zip(mdates.date2num(self.df.index.to_pydatetime()), self.df['open'], self.df['high'], self.df['low'], self.df['close'])
        for date, open, high, low, close in candlestick_data:
            color = '#089981' if close >= open else '#F23645'
            self.canvas.ax1.plot([date, date], [low, high], color=color, linewidth=0.8)
            self.canvas.ax1.plot([date, date], [open, close], color=color, linewidth=2)
        self.canvas.ax2.plot(data.index, data['close'], label="Close Price")
        self.canvas.ax2.plot(data.index, data['Predictions'], label="Predictions", linestyle='--')
        self.canvas.ax2.plot(data.index, data['Signal'] * 50, label="Signal")
        self.canvas.draw()
        self.show()
        print(data['Predictions'])
        print(data['Signal'])
        return data
    
    def run_ai(self):
        self.load_model_dialog()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Candlestick Data", "", "CSV Files (*.csv)")
        if file_name:
            self.df = pd.read_csv(file_name, index_col=0, parse_dates=True)
            print(f"Candlestick data loaded from {file_name}")

        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(self.df['close'].values.reshape(-1, 1))
        self.strategy_with_lstm(scaled_data, scaler)
    
    def save_model(self, model, filename):
        """Сохраняет обученную модель в файл."""
        joblib.dump(model, filename)
        print(f"Модель сохранена в {filename}")

    def load_model(self, filename):
        """Загружает модель из файла."""
        model = joblib.load(filename)
        print(f"Модель загружена из {filename}")
        return model
    
    def save_model_dialog(self):
        """Открывает диалоговое окно для сохранения модели."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить модель", "", "Model Files (*.pkl);;All Files (*)", options=options)
        if file_name:
            self.save_model(self.model, file_name)

    def load_model_dialog(self):
        """Открывает диалоговое окно для загрузки модели."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Загрузить модель", "", "Model Files (*.pkl);;All Files (*)", options=options)
        if file_name:
            self.model = self.load_model(file_name)
            # Теперь можно использовать загруженную модель

def main():
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    ex = CryptoTradingApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

