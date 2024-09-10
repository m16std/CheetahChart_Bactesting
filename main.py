import sys
from PyQt5.QtWidgets import  QApplication, QVBoxLayout, QWidget, QSpacerItem, QSizePolicy, QPushButton, QHBoxLayout, QComboBox, QSpinBox, QProgressBar, QFrame, QDialog # type: ignore
from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal # type: ignore
import pandas as pd # type: ignore
import matplotlib.pyplot as plt # type: ignore
import matplotlib.dates as mdates # type: ignore
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar # type: ignore
import qdarktheme # type: ignore
import numpy as np # type: ignore
import pickle
from file_manager import FileManager 
from neural_network import AIManager
from strategies import StrategyManager
from settings_window import SettingsDialog
from data_loader import DataDownloadThread
from mpl_canvas import MPlCanvas

pd.options.mode.chained_assignment = None

class CryptoTradingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.file_handler = FileManager(self)
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
        self.strat_input.addItems(['MA-50 cross MA-200', 'RSI', 'DCA', 'Supertrend v3 SOLANA 1H SETUP', 'Hawkes Process', 'Supertrend', 'Triple Supertrend','Bollinger + VWAP', 'Bollinger v2', 'MACD', 'MACD v2', 'MACD v3', 'MACD VWAP'])

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
        
        self.load_button = QPushButton('Download candlesticks', self)
        self.load_button.clicked.connect(self.download_and_save_candlesticks)
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

        self.rai_button = QPushButton('Export strategy', self)
        self.rai_button.setStyleSheet("border: none; font-size: 12px; ")
        button_layout.addWidget(self.rai_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.rai_button = QPushButton('Open strategy', self)
        self.rai_button.setStyleSheet("border: none; font-size: 12px; ")
        button_layout.addWidget(self.rai_button)

        button_layout.addWidget(self.create_vertical_separator())

        self.toggle_theme_button = QPushButton("Switch Theme")
        self.toggle_theme_button.clicked.connect(self.toggle_theme)
        self.toggle_theme_button.setStyleSheet("border: none; font-size: 12px; ")
        button_layout.addWidget(self.toggle_theme_button)

        button_layout.addWidget(self.create_vertical_separator())

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
        self.canvas = MPlCanvas(facecolor='#151924', textcolor = 'white')
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
        separator.setFrameShape(QFrame.VLine)  # Вертикальная линия
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: gray; background-color: gray;")
        separator.setFixedWidth(2)  # Устанавливаем фиксированную ширину линии

        return separator

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
        self.canvas.ax1.clear()
        self.canvas.ax2.clear()
        self.canvas.ax3.clear()

        self.thread = StrategyManager(self.strat_input.currentText(), self.df, self.initial_balance, self.position_size, self.position_type, self.profit_factor, self.leverage, self.commission)
        self.thread.progress_changed.connect(self.on_progress_changed)  # Подключаем слот для прогресса
        self.thread.calculation_complete.connect(self.on_calculation_complete)
        self.thread.start() 
    
    def on_calculation_complete(self, transactions, balance, indicators):
        # Метод, который будет вызван после выполнения стратегии
        self.plot_candlestick(self.df, transactions, balance, indicators)

    def plot_candlestick(self, df, transactions, balance, indicators):
        if self.current_theme == "dark":
            textcolor = 'white'
        else:
            textcolor = 'black'

        # Рисуем линии на фоне
        self.canvas.ax1.grid(True, axis='both', linewidth=0.3, color='gray')
        self.canvas.ax3.grid(True, axis='both', linewidth=0.3, color='gray', which="both")

        if len(df) <= 5000 and len(df) > 0:
            
            # Строим графики индикаторов
            for column in indicators:
                if column in df.columns:
                    self.canvas.ax2.plot(df.index, df[column], label=column, alpha=0.3)
                else:
                    print(f"Индикатор '{column}' отсутствует в DataFrame.")

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


            # Статистика
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

            self.plot_statistics()

        # Легенды
        self.canvas.ax1.legend([str(self.symbol_input.currentText()+' OKX')], loc='upper left', edgecolor='white') 
        self.canvas.ax2.legend(loc='upper right', edgecolor='white')
        self.canvas.ax3.legend(loc='upper left', edgecolor='white')

        # Переустановка форматтера оси X для ax1
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        self.canvas.ax1.xaxis.set_major_locator(locator)
        self.canvas.ax1.xaxis.set_major_formatter(formatter)

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

"""
def plot_balance(self, balance_data, initial_balance):
    # Очистка оси для графика баланса
    self.canvas.ax1.clear()

    # Проходим по каждому интервалу, разделяя его на участки выше и ниже начального баланса
    above_initial = balance_data >= initial_balance
    below_initial = balance_data < initial_balance

    # Функция для отрисовки непрерывных участков
    def plot_segment(data, mask, color, label=None):
        # Ищем начало и конец каждой непрерывной области
        start_idx = None
        for i in range(len(mask)):
            if mask[i] and start_idx is None:
                start_idx = i
            elif not mask[i] and start_idx is not None:
                # Рисуем участок от start_idx до текущего i
                self.canvas.ax1.plot(data.index[start_idx:i], data[start_idx:i], color=color, label=label if start_idx == 0 else "")
                start_idx = None
        if start_idx is not None:
            # Рисуем оставшийся участок в конце
            self.canvas.ax1.plot(data.index[start_idx:], data[start_idx:], color=color, label=label if start_idx == 0 else "")

    # Отрисовка участков баланса выше начального
    plot_segment(balance_data, above_initial, 'green', label='Above Initial Balance')

    # Отрисовка участков баланса ниже начального
    plot_segment(balance_data, below_initial, 'red', label='Below Initial Balance')
"""