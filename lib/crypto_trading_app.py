import sys
from PyQt5.QtWidgets import  QApplication, QVBoxLayout, QWidget, QSpacerItem, QSizePolicy, QPushButton, QHBoxLayout, QComboBox, QSpinBox, QProgressBar, QFrame, QDialog, QMessageBox # type: ignore
from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtCore import Qt, QSettings # type: ignore
import pandas as pd # type: ignore
import matplotlib.pyplot as plt # type: ignore
import matplotlib.dates as mdates # type: ignore
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar # type: ignore
from matplotlib.offsetbox import OffsetImage, AnnotationBbox # type: ignore
import matplotlib.image as mpimg # type: ignore
import qdarktheme # type: ignore
import numpy as np # type: ignore
import math

from lib.file_manager import FileManager 
from lib.neural_network import AIManager
from lib.strategies_manager import StrategyManager
from lib.settings_window import SettingsDialog
from lib.data_loader import DataDownloadThread
from lib.mpl_canvas import MPlCanvas

pd.options.mode.chained_assignment = None

class CryptoTradingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.file_handler = FileManager(self)
        self.strategy_manager = StrategyManager()
        self.ai_manager = AIManager(self)
        self.initUI()       
      
# Инициализация окна

    def initUI(self):
        self.df = []
        self.setWindowTitle('Cheetos Trading')

        self.data_loader = None
        self.current_data = None
        self.setGeometry(100, 100, 1300, 800)

        layout = QVBoxLayout(self)

        # Создаем лейаут кнопок и добавляем в layout
        button_layout = self.get_button_layout()
        layout.addLayout(button_layout)

        # Создаем лейаут полей ввода и добавляем в layout
        inputs_layout = self.get_inputs_layout()
        layout.addLayout(inputs_layout)

        # Создаем canvas и добавляем в layout
        self.canvas = MPlCanvas(facecolor='#151924', textcolor = 'white')
        layout.addWidget(self.canvas)

        # Включаем масштабирование и перемещения графиков
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.zoom()
        self.toolbar.pan()
        self.toolbar.setParent(None)
        #layout.addWidget(self.toolbar)

        self.stats = {'winrate': '0%', \
                'profit': '0%', \
                'trades': '0', \
                'period': '0 days', \
                'init': '0 USDT', \
                'final': '0 USDT', \
                'drawdown': '0%'}

        # Загружаем настройки    
        self.settings = QSettings("MyApp", "MyCompany")
        self.load_settings()

        # Загружаем тему
        self.current_theme = self.load_theme() 
        self.apply_theme()

        self.canvas.updateGeometry()
        self.show()

    def get_button_layout(self):

        style = "border: none; font-size: 12px;"
        
        button_layout = QHBoxLayout()

        self.lr_button = QPushButton('Download and run', self)
        self.lr_button.clicked.connect(self.download_and_run)
        self.lr_button.setStyleSheet(style)
        button_layout.addWidget(self.lr_button)

        button_layout.addWidget(self.create_vertical_separator())
        
        self.load_button = QPushButton('Download candlesticks', self)
        self.load_button.clicked.connect(self.download_and_save_candlesticks)
        self.load_button.setStyleSheet(style)
        button_layout.addWidget(self.load_button)

        button_layout.addWidget(self.create_vertical_separator())
        
        self.run_button = QPushButton('Run strategy', self)
        self.run_button.clicked.connect(self.open_and_run)
        self.run_button.setStyleSheet(style)
        button_layout.addWidget(self.run_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.tai_button = QPushButton('Train AI', self)
        self.tai_button.clicked.connect(self.ai_manager.train_model)
        self.tai_button.setStyleSheet(style)
        button_layout.addWidget(self.tai_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.rai_button = QPushButton('Run AI', self)
        self.rai_button.clicked.connect(self.ai_manager.run_ai)
        self.rai_button.setStyleSheet(style)
        button_layout.addWidget(self.rai_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.rai_button = QPushButton('Export strategy', self)
        self.rai_button.clicked.connect(self.export_strategy)
        self.rai_button.setStyleSheet(style)
        button_layout.addWidget(self.rai_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.rai_button = QPushButton('Import strategy', self)
        self.rai_button.setStyleSheet(style)
        self.rai_button.clicked.connect(self.import_strategy)
        button_layout.addWidget(self.rai_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.toggle_theme_button = QPushButton("Switch Theme")
        self.toggle_theme_button.clicked.connect(self.toggle_theme)
        self.toggle_theme_button.setStyleSheet(style)
        button_layout.addWidget(self.toggle_theme_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.settings_button.setStyleSheet(style)
        button_layout.addWidget(self.settings_button)

        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addItem(spacer)

        return button_layout

    def get_inputs_layout(self):
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
        self.strat_input.addItems(self.strategy_manager.strategy_dict.keys())
        font = self.strat_input.font()
        font.setPointSize(font_size)
        self.strat_input.setFont(font)

        self.symbol_input.setStyleSheet("border: none;")
        self.interval_input.setStyleSheet("border: none;")
        self.limit_input.setStyleSheet("border: none;")
        self.strat_input.setStyleSheet("border: none;")

        inputs_layout = QHBoxLayout()

        inputs_layout.addWidget(self.symbol_input)
        inputs_layout.addWidget(self.interval_input)
        inputs_layout.addWidget(self.limit_input)
        inputs_layout.addWidget(self.strat_input)
        inputs_layout.addWidget(self.bar)

        return inputs_layout
    
    def create_vertical_separator(self):
        # Создаем QFrame для вертикального разделителя
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)  # Вертикальная линия
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: gray; background-color: gray;")
        separator.setFixedWidth(2)  # Устанавливаем фиксированную ширину линии

        return separator

# Импорт-экспорт стратегий

    def export_strategy(self):
        self.thread = StrategyManager()
        self.thread.run('', [], 0, 0, 0, 0, 0, 0, mode="export") 
  
    def import_strategy(self):
    
        self.thread = StrategyManager()

        self.thread.profit_factor = self.profit_factor
        self.thread.leverage = self.leverage
        self.thread.initial_balance = self.initial_balance
        self.thread.position_type = self.position_type
        self.thread.position_size = self.position_size
        self.thread.df = self.df
        self.thread.strat_name = self.strat_input.currentText()
        self.thread.commission = self.commission
    
        self.thread.import_complete.connect(self.add_strategy)
        self.thread.run(mode="import") 

    def add_strategy(self, strategy_name, strategy_function):
        # Добавление новой стратегии в словарь и обновление выпадающего списка
        self.strat_input.addItem(strategy_name)
        self.strategy_manager.strategy_dict[strategy_name] = strategy_function
        print(f'Strategy "{strategy_name}" imported successfully.')

# Настройки

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
        print(f"Загружены настройки: Комиссия: {self.commission}, Начальный баланс: {self.initial_balance}, Плечо: {self.leverage}, Профит фактор: {self.profit_factor}, Размер позиции: {self.position_size}, Тип: {self.position_type}")
    
# Тема приложения

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
            self.plot_statistics()
                
        else:
            qdarktheme.setup_theme(self.current_theme)
            self.canvas.update_colors(facecolor='#ffffff', textcolor = 'black')
            self.plot_statistics()

    def toggle_theme(self):
        # Переключаем между темной и светлой темой
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.current_theme = new_theme  # Обновляем текущую тему
        self.apply_theme()

        # Сохраняем состояние темы
        self.settings.setValue("theme", self.current_theme)

    def load_theme(self):
        return self.settings.value("theme")
    
# Запуск стратегий

    def open_and_run(self):
        if self.file_handler.load_candlesticks():
            self.run_strategy()

    def download_and_run(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        run = True

        self.thread = DataDownloadThread(symbol, interval, limit, run)
        self.thread.progress_changed.connect(self.on_progress_changed)  # Подключаем слот для прогресса
        self.thread.data_downloaded_run_it.connect(self.on_data_downloaded_run_it)
        self.thread.data_downloaded_save_it.connect(self.on_data_downloaded_save_it)
        self.thread.start()  # Запускаем поток

    def on_progress_changed(self, value):
        # Обновляем значение прогресс-бара
        self.bar.setValue(value)

    def on_data_downloaded_run_it(self, data):
        # Метод, который будет вызван после завершения скачивания
        self.df = data
        self.run_strategy()

    def on_data_downloaded_save_it(self, data):
        # Метод, который будет вызван после завершения скачивания
        self.df = data
        self.file_handler.save_candlesticks()
    
    def download_and_save_candlesticks(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        run = False
    
        self.thread = DataDownloadThread(symbol, interval, limit, run)
        self.thread.progress_changed.connect(self.on_progress_changed)  # Подключаем слот для прогресса
        self.thread.data_downloaded_run_it.connect(self.on_data_downloaded_run_it)
        self.thread.data_downloaded_save_it.connect(self.on_data_downloaded_save_it)
        self.thread.start()

    def run_strategy(self):

        self.thread = self.strategy_manager

        self.thread.profit_factor = self.profit_factor
        self.thread.leverage = self.leverage
        self.thread.initial_balance = self.initial_balance
        self.thread.position_type = self.position_type
        self.thread.position_size = self.position_size
        self.thread.df = self.df
        self.thread.strat_name = self.strat_input.currentText()
        self.thread.commission = self.commission

        self.thread.progress_changed.connect(self.on_progress_changed)  # Подключаем слот для прогресса
        self.thread.calculation_complete.connect(self.on_calculation_complete)
        self.thread.run() 
    
    def on_calculation_complete(self, transactions, balance, indicators):
        self.canvas.ax1.clear()
        self.canvas.ax2.clear()
        self.canvas.ax3.clear()
        # Метод, который будет вызван после выполнения стратегии
        self.plot(self.df, transactions, balance, indicators)

# Отрисовка графиков

    def plot(self, df, transactions, balance, indicators):

        if len(df) <= 5000 and len(df) > 0:
            # Рисуем индикаторы
            self.plot_indicators(df, indicators)
            # Рисуем свечи            
            self.plot_candles(df)
            # Рисуем сделки
            self.plot_trades(transactions)

        if len(transactions) > 0:
            # Рисуем баланс
            self.plot_balance(balance)
            # Получаем статистику
            self.stats = self.get_statistic(balance, transactions)
            # Рисуем статистику
            self.plot_statistics()


        self.formatter_canvas()
        self.bar.setValue(100)
        self.canvas.draw()
        self.show()

    def plot_statistics(self):

        if self.current_theme == "dark":
            textcolor = 'white'
        else:
            textcolor = 'black'

        self.canvas.ax4.clear()
        transform = self.canvas.ax4.transAxes
        textprops = {'size': '10'}

        self.canvas.ax4.text(0, -0.04, 'Winrate', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0, -0.075, self.stats['winrate'], transform = transform, ha = 'left', color = '#089981', **textprops)
        self.canvas.ax4.text(0.15, -0.04, 'Profit', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.15, -0.075, self.stats['profit'], transform = transform, ha = 'left', color = '#089981', **textprops)
        self.canvas.ax4.text(0.3, -0.04, 'Trades', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.3, -0.075, self.stats['trades'], transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.45, -0.04, 'Period', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.45, -0.075, self.stats['period'], transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.6, -0.04, 'Initial balance', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.6, -0.075, self.stats['init'], transform = transform, ha = 'left', color = '#089981', **textprops)
        self.canvas.ax4.text(0.75, -0.04, 'Final balance', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.75, -0.075, self.stats['final'], transform = transform, ha = 'left', color = '#089981', **textprops)
        self.canvas.ax4.text(0.9, -0.04, 'Max drawdown', transform = transform, ha = 'left', color = textcolor, **textprops)
        self.canvas.ax4.text(0.9, -0.075, self.stats['drawdown'], transform = transform, ha = 'left', color = '#F23645', **textprops)
        #self.canvas.ax4.text(0.01, 0.02, 'CheetosTrading', transform = transform, ha = 'left', color = textcolor) 

        logo = mpimg.imread('resources/logo.png' )
        imagebox = OffsetImage(logo, zoom=0.2, alpha=0.3)

        # Фиксирование логотипа в координатах фигуры (левый нижний угол)
        ab = AnnotationBbox(imagebox, (0.01, 0.02), xycoords='axes fraction', frameon=False, box_alignment=(0, 0))

        self.canvas.ax4.add_artist(ab)

        self.canvas.draw()
        self.show()

    def plot_balance(self, balance):
        above_initial = balance['value'] >= self.initial_balance

        # Рисуем всю линию графика, а затем изменяем цвет участков
        if max(balance['value']) / min(balance['value']) < 4:
            self.canvas.ax3.plot(balance['ts'], balance['value'], color='black', label = 'balance', alpha=0)
        else:
            self.canvas.ax3.semilogy(balance['ts'], balance['value'], color='black', label = 'balance', alpha=0)

        start_idx = 0

        while start_idx < len(balance):
            # Ищем конец участка, где значение выше или ниже начального баланса
            end_idx = start_idx + 1
            while end_idx < len(balance) and above_initial[end_idx] == above_initial[start_idx]:
                end_idx += 1
            # Выбираем цвет в зависимости от того, выше или ниже начального баланса
            color = '#089981' if above_initial[start_idx] else '#F23645'
            # Рисуем участок линии
            self.canvas.ax3.plot(balance['ts'][start_idx:end_idx + 1], 
                                balance['value'][start_idx:end_idx + 1], 
                                color=color)
            # Переход к следующему участку
            start_idx = end_idx

        NbData = len(balance['ts'])
        MaxBL = [[MaxBL] * NbData for MaxBL in range(int(max(balance['value'])+1))]
        Max = [np.asarray(MaxBL[x]) for x in range(int(max(balance['value'])+1))]
        step = int((max(balance['value'])-min(balance['value']))/20)
        
        try:
            if step == 0:
                step = 1
            for x in range (int(balance['value'].iloc[0]), int(max(balance['value'])), step):
                self.canvas.ax3.fill_between(balance['ts'], Max[x], balance['value'], where=balance['value'] >= Max[x], facecolor='#089981', alpha=0.05)
            for x in range (int(min(balance['value'])), int(balance['value'].iloc[0]), step):
                self.canvas.ax3.fill_between(balance['ts'], balance['value'], Max[x], where=balance['value'] <= Max[x], facecolor='#FF5045', alpha=0.05)
        except:
            print('Ошибка в процессе создания градиента баланса')   

        # Квадратики на фоне баланса
        max_rise = 0.0
        patch_count = 30
        step = int((len(balance)-1)/patch_count)
        for i in range (0, len(balance)-1-step, step):
            rise = abs((balance['value'].iloc[i+step] - balance['value'].iloc[i]) / balance['value'].iloc[i])
            if rise > max_rise:
                max_rise = rise

        for i in range (0, len(balance)-1-step, step):
            patch_color = '#089981' if (balance['value'].iloc[i+step] - balance['value'].iloc[i]) > 0 else '#F23645'
            self.canvas.ax3.add_patch(plt.Rectangle(
                        (balance['ts'].iloc[i], min(balance['value'])),
                        (balance['ts'].iloc[-1] - balance['ts'].iloc[0])/patch_count*0.98,
                        abs((balance['value'].iloc[i+step] - balance['value'].iloc[i]) / balance['value'].iloc[i])/max_rise*(max(balance['value'])-min(balance['value'])),
                        color=patch_color, alpha=0.2
                    ))  

    def get_statistic(self, balance, transactions):
        # Рассчет максимальной просадки 
        max_drawdown = 0
        max_balance = 0
        for i in range(0, len(balance['value'])):
            if max_balance < balance['value'].iloc[i]:
                max_balance = balance['value'].iloc[i]
            if (max_balance - balance['value'].iloc[i]) * 100 / max_balance > max_drawdown:
                max_drawdown = (max_balance - balance['value'].iloc[i]) * 100 / max_balance

        # Рассчет профита, винрейта
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
        profit = round((float(balance['value'].iloc[-1])-float(balance['value'].iloc[0]))/float(balance['value'].iloc[0])*100, ndigits=2)

        # Статистика
        period = balance['ts'].iloc[-1] - balance['ts'].iloc[0]
        period_days = f"{period.days} days"
        stats = {'winrate': str(winrate)+'%', \
                'profit': str(profit)+'%', \
                'trades': str(wins+losses), \
                'period': period_days, \
                'init': str(balance['value'].iloc[0])+' USDT', \
                'final': str(round(balance['value'].iloc[-1], ndigits=1))+' USDT', \
                'drawdown': str(round(max_drawdown, ndigits=1))+'%'}
        
        return stats

    def plot_trades(self, transactions):
        for tp, sl, position_size, open_price, open_time, close_time, close_price, type, result, pnl in transactions:
            if type == 1:
                self.canvas.ax1.plot(mdates.date2num(open_time), open_price, marker='^', color='lime', markersize=7)
                self.canvas.ax1.plot(mdates.date2num(close_time), close_price, marker='X', color='salmon', markersize=7)
            if type == -1:
                self.canvas.ax1.plot(mdates.date2num(open_time), open_price, marker='v', color='salmon', markersize=7)
                self.canvas.ax1.plot(mdates.date2num(close_time), close_price, marker='X', color='lime', markersize=7)
        self.bar.setValue(25)

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

    def plot_candles(self, df):
        percent5 = int(len(df) / 20)
        index = 0 
        label_added = False
        candlestick_data = zip(mdates.date2num(df.index.to_pydatetime()), df['open'], df['high'], df['low'], df['close'])

        for date, open, high, low, close in candlestick_data:
            if index % percent5 == 0:
                self.bar.setValue(int(index / len(df) * 100))
            index += 1
            color = '#089981' if close >= open else '#F23645'
            if not label_added:
                self.canvas.ax1.plot([date, date], [open, close], color=color, label = str(self.symbol_input.currentText()+' OKX'), linewidth=2)
                label_added = True
            else:
                self.canvas.ax1.plot([date, date], [open, close], color=color, linewidth=2)
            self.canvas.ax1.plot([date, date], [low, high], color=color, linewidth=0.8)

    def plot_indicators(self, df, indicators):
        for column in indicators:
            if column in df.columns:
                i = len(df) - 1
                while i > 0 and math.isnan(df[column].iloc[i]):
                    i -= 1
                # проверка на то нужно ли рисовать индикатор на одном графике с ценой
                if df[column].iloc[i] > df['close'].iloc[i] * 0.7 and df[column].iloc[i] < df['close'].iloc[i] * 1.3: 
                    self.canvas.ax1.plot(df.index, df[column], label=column, alpha=0.5)
                else:
                    self.canvas.ax2.plot(df.index, df[column], label=column, alpha=0.5)
            else:
                print(f"Индикатор '{column}' отсутствует в DataFrame.")

    def formatter_canvas(self):
        # Легенды
        self.canvas.ax1.legend(loc='upper left')
        self.canvas.ax2.legend(loc='upper right')
        self.canvas.ax3.legend(loc='upper left')

        # Линии на фоне
        self.canvas.ax1.grid(True, axis='both', linewidth=0.3, color='gray')
        self.canvas.ax3.grid(True, axis='both', linewidth=0.3, color='gray', which="both")

        # Переустановка форматтера оси X
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        self.canvas.ax1.xaxis.set_major_locator(locator)
        self.canvas.ax1.xaxis.set_major_formatter(formatter)



