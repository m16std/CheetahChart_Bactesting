
import sys
from PyQt5.QtWidgets import  QApplication, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QComboBox, QSpinBox, QFormLayout, QProgressBar # type: ignore
from PyQt5 import QtGui, QtWidgets # type: ignore
from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtCore import Qt # type: ignore
import requests # type: ignore
import pandas as pd # type: ignore
import matplotlib.pyplot as plt # type: ignore
import matplotlib.dates as mdates # type: ignore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas # type: ignore
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar # type: ignore
import qdarktheme # type: ignore
import numpy as np # type: ignore

from data_loader import FileManager 
from neural_network import AIManager
from strategies import StrategyManager

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
        self.file_handler = FileManager(self)
        self.strategy_manager = StrategyManager(self)
        self.ai_manager = AIManager(self)
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
        self.strat_input.addItems(['Supertrend', 'Supertrend stupid','Bollinger + VWAP', 'Bollinger v2', 'MACD', 'MACD v2', 'MACD v3'])

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
        self.run_button.clicked.connect(self.download_and_run)
        button_layout.addWidget(self.run_button)
        
        self.save_button = QPushButton('Save Candlesticks', self)
        self.save_button.clicked.connect(self.file_handler.save_candlesticks)
        button_layout.addWidget(self.save_button)
        
        self.load_button = QPushButton('Open Candlesticks', self)
        self.load_button.clicked.connect(self.open_and_run)
        button_layout.addWidget(self.load_button)

        self.tai_button = QPushButton('Train AI', self)
        self.tai_button.clicked.connect(self.ai_manager.train_model)
        button_layout.addWidget(self.tai_button)

        self.rai_button = QPushButton('Run AI', self)
        self.rai_button.clicked.connect(self.ai_manager.run_ai)
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

    def open_and_run(self):
        self.file_handler.load_candlesticks()
        self.run_strategy()

    def download_and_run(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()

        self.df = self.get_okx_ohlcv(symbol, interval, limit)
        
        self.run_strategy()

    def run_strategy(self):
        if self.strat_input.currentText() == "MACD":
            self.current_strategy = self.strategy_manager.macd_strategy
        elif self.strat_input.currentText() == "MACD v2":
            self.current_strategy = self.strategy_manager.macd_v2_strategy
        elif self.strat_input.currentText() == "Bollinger + VWAP":
            self.current_strategy = self.strategy_manager.bollinger_vwap_strategy
        elif self.strat_input.currentText() == "Bollinger v2":
            self.current_strategy = self.strategy_manager.bollinger_v2
        elif self.strat_input.currentText() == "Supertrend":
            self.current_strategy = self.strategy_manager.supertrend_strategy
        elif self.strat_input.currentText() == "Supertrend stupid":
            self.current_strategy = self.strategy_manager.supertrend_stupid
        elif self.strat_input.currentText() == "MACD v3":
            self.current_strategy = self.strategy_manager.macd_v3_strategy
            
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
        data = data[::-1]

        data = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        data[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']] = data[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']].astype(float)
        data['ts'] = pd.to_datetime(data['ts'], unit='ms')
        data.set_index('ts', inplace=True)

        return data

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

        max_profit = 0.0
        patch_count = 50
        step = int((len(balance[0])-1)/patch_count)
        for i in range (0, len(balance[0])-1-step, step):
            if abs((balance[0][i+step] - balance[0][i]) / balance[0][i]) > max_profit:
                        max_profit = abs((balance[0][i+step] - balance[0][i]) / balance[0][i])

        for i in range (patch_count):
            patch_color = '#089981' if (balance[0][i+step] - balance[0][i]) > 0 else '#F23645'
            self.canvas.ax3.add_patch(plt.Rectangle(
                        (balance[1][i], min(balance[0])),
                        (balance[1][-1] - balance[1][0])/patch_count,
                        abs((balance[0][i+step] - balance[0][i]) / balance[0][i])/max_profit*max(balance[0]),
                        color=patch_color, alpha=0.2
                    ))

        # Рисуем баланс
        index = 0 
        if max(balance[0]) / min(balance[0]) < 4:
            self.canvas.ax3.plot(balance[1], balance[0], label='Balance', color='#089981', linestyle='-')
        else:
            self.canvas.ax3.semilogy(balance[1], balance[0], label='Balance', color='#089981', linestyle='-')
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

def main():
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    ex = CryptoTradingApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

