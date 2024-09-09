
import sys
from PyQt5.QtWidgets import  QApplication, QVBoxLayout, QWidget, QSpacerItem, QSizePolicy, QPushButton, QHBoxLayout, QComboBox, QSpinBox, QProgressBar, QFrame, QDialog # type: ignore
from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal # type: ignore
import requests # type: ignore
import pandas as pd # type: ignore
import matplotlib.pyplot as plt # type: ignore
import matplotlib.dates as mdates # type: ignore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas # type: ignore
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar # type: ignore
import qdarktheme # type: ignore
import numpy as np # type: ignore
import pickle
from data_loader import FileManager 
from neural_network import AIManager
from strategies import StrategyManager
from settings_window import SettingsDialog
from threading import Thread

pd.options.mode.chained_assignment = None

class DataDownloadThread(QThread):
    # Сигнал, который можно отправить после завершения скачивания
    data_downloaded = pyqtSignal(object)
    progress_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super(DataDownloadThread, self).__init__(parent)
        self.data = None

    def __init__(self, symbol, interval, limit, parent=None):
        super(DataDownloadThread, self).__init__(parent)
        self.symbol = symbol
        self.interval = interval
        self.limit = limit

    def run(self):
        # Запускаем метод скачивания данных с переданными параметрами
        data = self.get_okx_ohlcv(self.symbol, self.interval, self.limit)

        # После завершения, сигнализируем об этом
        self.data_downloaded.emit(data)

        
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
        url = f'https://www.okx.com/api/v5/market/history-candles'
        while len(data) < limit:
            self.progress_changed.emit(round(len(data) / limit*100)) 
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

        self.progress_changed.emit(100) 
        data = data[::-1]

        data = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        data[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']] = data[['open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote']].astype(float)
        data['ts'] = pd.to_datetime(data['ts'], unit='ms')
        data.set_index('ts', inplace=True)

        return data

class MplCanvas(FigureCanvas):

    def __init__(self, facecolor, textcolor):
        self.fig, (self.ax1, self.ax3) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]}, facecolor=facecolor)

        # Вызов конструктора базового класса FigureCanvas
        super(MplCanvas, self).__init__(self.fig)

        self.ax2 = self.ax1.twinx()
        self.ax4 = self.ax1.twinx()
        self.init_canvas(facecolor, textcolor)  # Инициализация настроек canvas

    def init_canvas(self, facecolor, textcolor):
        """Метод для инициализации или обновления цветов"""
        self.fig.patch.set_facecolor(facecolor)
        self.ax1.set_facecolor(facecolor)
        self.ax3.set_facecolor(facecolor)

        # Обновляем цвета для осей и текста
        self.ax1.tick_params(colors=textcolor, direction='out')
        for tick in self.ax1.get_xticklabels():
            tick.set_color(textcolor)
        for tick in self.ax1.get_yticklabels():
            tick.set_color(textcolor)

        self.ax3.tick_params(colors=textcolor, direction='out')
        for tick in self.ax3.get_xticklabels():
            tick.set_color(textcolor)
        for tick in self.ax3.get_yticklabels():
            tick.set_color(textcolor)

        plt.subplots_adjust(left=0.04, bottom=0.03, right=1, top=1, hspace=0.12)

        # Перерисовываем график
        self.draw()

    def update_colors(self, facecolor, textcolor):
        """Метод для обновления цветов и перерисовки"""
        self.init_canvas(facecolor, textcolor)

class CryptoTradingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.file_handler = FileManager(self)
        self.strategy_manager = StrategyManager(self)
        self.ai_manager = AIManager(self)
        self.initUI()       

    def export_strategy(self, strategy_function, filename):
        with open(filename, 'wb') as file:
            pickle.dump(strategy_function, file) 
        
    def initUI(self):
        self.df = []
        self.setWindowTitle('Cheetos Trading')
        #self.setStyleSheet("background-color: #151924;")

        self.data_loader = None
        self.current_data = None
        self.setGeometry(100, 100, 1300, 800)

        layout = QVBoxLayout(self)

        font_size = 10

        self.symbol_input = QComboBox(self)
        self.symbol_input.addItems(['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'PEPE-USDT', 'TON-USDT', 'BNB-USDT'])

        font = self.symbol_input.font()
        font.setPointSize(font_size)
        self.symbol_input.setFont(font)

        self.interval_input = QComboBox(self)
        self.interval_input.addItems(['1m', '5m', '15m','30m', '1H', '4H', '12H','1D'])
        self.interval_input.setCurrentIndex(2)

        font = self.interval_input.font()
        font.setPointSize(font_size)
        self.interval_input.setFont(font)

        self.limit_input = QSpinBox(self)
        self.limit_input.setRange(100, 100000)
        self.limit_input.setValue(1000)

        font = self.limit_input.font()
        font.setPointSize(font_size)
        self.limit_input.setFont(font)

        self.bar = QProgressBar(self) 
        self.bar.setGeometry(200, 100, 200, 30) 
        self.bar.setValue(0) 
        self.bar.setAlignment(Qt.AlignCenter) 

        self.strat_input = QComboBox(self)
        self.strat_input.addItems(['MA-50 cross MA-200', 'RSI', 'DCA', 'Supertrend v3 SOLANA 1H SETUP', 'Hawkes Process', 'Supertrend', 'Supertrend v2','Bollinger + VWAP', 'Bollinger v2', 'MACD', 'MACD v2', 'MACD v3', 'MACD VWAP'])

        font = self.strat_input.font()
        font.setPointSize(font_size)
        self.strat_input.setFont(font)

        self.symbol_input.setStyleSheet("border: none;")
        self.interval_input.setStyleSheet("border: none;")
        self.limit_input.setStyleSheet("border: none;")
        self.strat_input.setStyleSheet("border: none;")

        button_layout = QHBoxLayout()

        self.lr_button = QPushButton('Download and run', self)
        self.lr_button.clicked.connect(self.download_and_run)
        self.lr_button.setStyleSheet("border: none; font-size: 12px; ")
        button_layout.addWidget(self.lr_button)

        button_layout.addWidget(self.create_vertical_separator())
        
        self.load_button = QPushButton('Load candlesticks', self)
        self.load_button.clicked.connect(self.file_handler.save_candlesticks)
        self.load_button.setStyleSheet("border: none; font-size: 12px; ")
        button_layout.addWidget(self.load_button)

        button_layout.addWidget(self.create_vertical_separator())
        
        self.run_button = QPushButton('Run strategy', self)
        self.run_button.clicked.connect(self.open_and_run)
        self.run_button.setStyleSheet("border: none; font-size: 12px;")
        button_layout.addWidget(self.run_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.tai_button = QPushButton('Train AI', self)
        self.tai_button.clicked.connect(self.ai_manager.train_model)
        self.tai_button.setStyleSheet("border: none; font-size: 12px; ")
        button_layout.addWidget(self.tai_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.rai_button = QPushButton('Run AI', self)
        self.rai_button.clicked.connect(self.ai_manager.run_ai)
        self.rai_button.setStyleSheet("border: none; font-size: 12px; ")
        button_layout.addWidget(self.rai_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.toggle_theme_button = QPushButton("Switch Theme")
        self.toggle_theme_button.clicked.connect(self.toggle_theme)
        self.toggle_theme_button.setStyleSheet("border: none; font-size: 12px; ")
        button_layout.addWidget(self.toggle_theme_button)

        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.settings_button.setStyleSheet("border: none; font-size: 12px; ")
        button_layout.addWidget(self.settings_button)


        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addItem(spacer)

        layout.addLayout(button_layout)

        hbox_layout = QHBoxLayout()

        hbox_layout.addWidget(self.symbol_input)
        hbox_layout.addWidget(self.interval_input)
        hbox_layout.addWidget(self.limit_input)
        hbox_layout.addWidget(self.strat_input)
        hbox_layout.addWidget(self.bar)

        layout.addLayout(hbox_layout)

        # Создаем canvas и добавляем в layout
        self.canvas = MplCanvas(facecolor='#151924', textcolor = 'white')
        layout.addWidget(self.canvas)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.zoom()
        self.toolbar.pan()
        self.toolbar.setParent(None)
        #layout.addWidget(self.toolbar)

        # Настраиваем политику размера для динамического изменения
        self.canvas.setSizePolicy(
            self.sizePolicy().Expanding,
            self.sizePolicy().Expanding
        )

        self.text = []
        self.text.append('0%') 
        self.text.append('0%')
        self.text.append('0')
        self.text.append('0 days')
        self.text.append('0 USDT')
        self.text.append('0 USDT')
        self.text.append('0%')
        self.text.append('CheetosTrading')

        self.settings = QSettings("MyApp", "MyCompany")
        self.load_settings()
        self.current_theme = self.load_theme()  # Загружаем тему
        self.apply_theme()
        

        self.canvas.updateGeometry()
        self.show()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_settings()

    def load_settings(self):
        # Здесь можно применять настройки в логике программы
        self.commission = float(self.settings.value("commission", "0.0008"))
        self.initial_balance = int(self.settings.value("initial_balance", "100"))
        self.leverage = float(self.settings.value("leverage", "1"))
        self.profit_factor = float(self.settings.value("profit_factor", "1.5"))
        self.position_type = self.settings.value("position_type", "percent")
        self.position_size = float(self.settings.value("position_size", "100"))
        print(f"Загружены настройки: Комиссия: {self.commission}, Начальный баланс: {self.initial_balance}, Плечо: {self.leverage}, Профит фактор: {self.profit_factor}, , Размер позиции: {self.position_size}, Тип: {self.position_type}")

    def create_vertical_separator(self):
        # Создаем QFrame для вертикального разделителя
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: gray; background-color: gray;")
        separator.setFixedWidth(2)

        # Создаем виджет-контейнер для разделителя
        container = QWidget()
        vbox = QVBoxLayout()
        vbox.addStretch(1)  # Добавляем отступ сверху
        vbox.addWidget(separator)
        vbox.addStretch(1)  # Добавляем отступ снизу
        vbox.setContentsMargins(0, 0, 0, 0)  # Убираем отступы по краям
        container.setLayout(vbox)

        return container

    def apply_theme(self):
        if self.current_theme == "dark":
            qdarktheme.setup_theme(
                custom_colors={
                    "[dark]": {
                        "background": "#151924",
                        "primary": "#ffffff",
                        "primary>button.hoverBackground": "#669ff55c",
                        "primary>progressBar.background": "#669ff5",
                    }
                }
            )
            self.canvas.update_colors(facecolor='#151924', textcolor = 'white')
            self.plot_statistics(textcolor = 'white')
                
        else:
            qdarktheme.setup_theme(self.current_theme)
            self.canvas.update_colors(facecolor='#ffffff', textcolor = 'black')
            self.plot_statistics(textcolor = 'black')

    def toggle_theme(self):
        # Переключаем между темной и светлой темой
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.current_theme = new_theme  # Обновляем текущую тему
        self.apply_theme()

        # Сохраняем состояние темы
        self.settings.setValue("theme", self.current_theme)

    def load_theme(self):
        return self.settings.value("theme")
    
    def open_and_run(self):
        if self.file_handler.load_candlesticks():
            self.run_strategy()

    def download_and_run(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()

        self.thread = DataDownloadThread(symbol, interval, limit)
        self.thread.progress_changed.connect(self.on_progress_changed)  # Подключаем слот для прогресса
        self.thread.data_downloaded.connect(self.on_data_downloaded)
        self.thread.start()  # Запускаем поток

    def on_progress_changed(self, value):
        # Обновляем значение прогресс-бара
        self.bar.setValue(value)

    def on_data_downloaded(self, data):
        # Метод, который будет вызван после завершения скачивания
        self.df = data

        self.run_strategy()

    def get_strategy_from_name(self, name):
        current_strategy = self.strategy_manager.macd_strategy
        if name == "MACD":
            current_strategy = self.strategy_manager.macd_strategy
        elif name == "MACD v2":
            current_strategy = self.strategy_manager.macd_v2_strategy
        elif name == "Bollinger + VWAP":
            current_strategy = self.strategy_manager.bollinger_vwap_strategy
        elif name == "Bollinger v2":
            current_strategy = self.strategy_manager.bollinger_v2
        elif name == "Supertrend":
            current_strategy = self.strategy_manager.supertrend_strategy
        elif name == "Supertrend v2":
            current_strategy = self.strategy_manager.supertrend_v2
        elif name == "MACD v3":
            current_strategy = self.strategy_manager.macd_v3_strategy
        elif name == "MACD VWAP":
            current_strategy = self.strategy_manager.macd_vwap_strategy
        elif name == "Hawkes Process":
            current_strategy = self.strategy_manager.hawkes_process_strategy
        elif name == "Supertrend v3 SOLANA 1H SETUP":
            current_strategy = self.strategy_manager.supertrend_v3
        elif name == "DCA":
            current_strategy = self.strategy_manager.dca_strategy
        elif name == "RSI":
            current_strategy = self.strategy_manager.rsi_strategy
        elif name == "MA-50 cross MA-200":
            current_strategy = self.strategy_manager.ma50200_cross_strategy

        return current_strategy

    def run_strategy(self):
        self.current_strategy = self.get_strategy_from_name(self.strat_input.currentText())
        self.canvas.ax1.clear()
        self.canvas.ax2.clear()
        self.canvas.ax3.clear()
        transactions, balance = self.current_strategy(self.df)
        self.plot_candlestick(self.df, transactions, balance)

    def plot_candlestick(self, df, transactions, balance):
        if self.current_theme == "dark":
            textcolor = 'white'
        else:
            textcolor = 'black'

        # Рисуем линии на фоне
        self.canvas.ax1.grid(True, axis='both', linewidth=0.3, color='gray')
        self.canvas.ax3.grid(True, axis='both', linewidth=0.3, color='gray', which="both")

        if len(df) <= 10000 and len(df) > 0:
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

        if len(balance[0]) > 0 and len(transactions) > 0:
            wins = 0
            losses = 0
            winrate = 0
            for tp, sl, position_size, open_price, open_time, close_time, close_price, type, result, pnl in transactions:
                if result == 1:
                    wins += 1
                else:
                    losses += 1
            if wins+losses == 0:
                winrate = 0
            else:
                winrate = round(wins/(wins+losses)*100, ndigits=2)
            profit = round((float(balance[0][-1])-float(balance[0][0]))/float(balance[0][0])*100, ndigits=2)


            if len(df) <= 10000:
                self.bar.setValue(0)
                # Рисуем сделки 
                for tp, sl, position_size, open_price, open_time, close_time, close_price, type, result, pnl in transactions:
                    if type == 1:
                        self.canvas.ax1.plot(mdates.date2num(open_time), open_price, marker='^', color='lime', markersize=7)
                        self.canvas.ax1.plot(mdates.date2num(close_time), close_price, marker='X', color='salmon', markersize=7)
                    if type == -1:
                        self.canvas.ax1.plot(mdates.date2num(open_time), open_price, marker='v', color='salmon', markersize=7)
                        self.canvas.ax1.plot(mdates.date2num(close_time), close_price, marker='X', color='lime', markersize=7)
                self.bar.setValue(20)

                # Рисуем области tp и sl 
                for tp, sl, position_size, open_price, open_time, close_time, close_price, type, result, pnl in transactions:
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
            
            # Квадратики на фоне баланса
            max_profit = 0.0
            patch_count = 30
            step = int((len(balance[0])-1)/patch_count)
            for i in range (0, len(balance[0])-1-step, step):
                if abs((balance[0][i+step] - balance[0][i]) / balance[0][i]) > max_profit:
                    max_profit = abs((balance[0][i+step] - balance[0][i]) / balance[0][i])

            for i in range (0, len(balance[0])-1-step, step):
                patch_color = '#089981' if (balance[0][i+step] - balance[0][i]) > 0 else '#F23645'
                self.canvas.ax3.add_patch(plt.Rectangle(
                            (balance[1][i], min(balance[0])),
                            (balance[1][-1] - balance[1][0])/patch_count*0.96,
                            abs((balance[0][i+step] - balance[0][i]) / balance[0][i])/max_profit*(max(balance[0])-min(balance[0])),
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
            try:
                if step == 0:
                    step = 1
                for x in range (int(balance[0][0]), int(max(balance[0])), step):
                    self.canvas.ax3.fill_between(balance[1], Max[x], balance[0], where=balance[0] >= Max[x], facecolor='#089981', alpha=0.05)
                for x in range (int(min(balance[0])), int(balance[0][0]), step):
                    self.canvas.ax3.fill_between(balance[1], balance[0], Max[x], where=balance[0] <= Max[x], facecolor='#FF5045', alpha=0.05)
            except:
                print('че-то не так')    

            max_drawdown = 0
            max_balance = 0
            self.bar.setValue(80)
            for i in range(0, len(balance[0])):
                if max_balance < balance[0][i]:
                    max_balance = balance[0][i]
                if (max_balance - balance[0][i]) * 100 / max_balance > max_drawdown:
                    max_drawdown = (max_balance - balance[0][i]) * 100 / max_balance


            for label in self.canvas.ax3.get_yticklabels(which='both'):
                label.set_color(textcolor)


            # Побочная инфа
            self.text = []
            period = balance[1][-1] - balance[1][0]
            period_days = f"{period.days} days"
            self.text.append(str(winrate)+'%') 
            self.text.append(str(profit)+'%')
            self.text.append(str(wins+losses))
            self.text.append(period_days)
            self.text.append(str(balance[0][0])+' USDT')
            self.text.append(str(round(balance[0][-1], ndigits=1))+' USDT')
            self.text.append(str(round(max_drawdown, ndigits=1))+'%')
            self.text.append('CheetosTrading')

            self.plot_statistics(textcolor)

        # Легенды
        self.canvas.ax1.legend(loc='upper left', edgecolor='white') 
        self.canvas.ax2.legend(loc='upper right', edgecolor='white')
        self.canvas.ax3.legend(loc='upper left', edgecolor='white')

        self.bar.setValue(100)
        self.canvas.draw()
        self.show()

    def plot_statistics(self, textcolor):

        self.canvas.ax4.clear()

        transform = self.canvas.ax4.transAxes
        textprops = {'size': '10'}

        self.canvas.ax4.text(0, -0.04, 'Winrate', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0, -0.075, self.text[0], transform = transform, ha = 'left', color = '#089981', **textprops)
        self.canvas.ax4.text(0.15, -0.04, 'Profit', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.15, -0.075, self.text[1], transform = transform, ha = 'left', color = '#089981', **textprops)
        self.canvas.ax4.text(0.3, -0.04, 'Trades', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.3, -0.075, self.text[2], transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.45, -0.04, 'Period', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.45, -0.075, self.text[3], transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.6, -0.04, 'Initial balance', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.6, -0.075, self.text[4], transform = transform, ha = 'left', color = '#089981', **textprops)
        self.canvas.ax4.text(0.75, -0.04, 'Final balance', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.75, -0.075, self.text[5], transform = transform, ha = 'left', color = '#089981', **textprops)
        self.canvas.ax4.text(0.9, -0.04, 'Max drawdown', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.9, -0.075, self.text[6], transform = transform, ha = 'left', color = '#F23645', **textprops)
        self.canvas.ax4.text(0.01, 0.02, 'CheetosTrading', transform = transform, ha = 'left', color = textcolor) 

        self.canvas.draw()
        self.show()



def main():
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")  # Начальная тема
    ex = CryptoTradingApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

