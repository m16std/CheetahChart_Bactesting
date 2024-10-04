import sys
from PyQt5.QtWidgets import  QVBoxLayout, QWidget, QSpacerItem, QSizePolicy, QPushButton, QHBoxLayout, QComboBox, QSpinBox, QProgressBar, QFrame, QDialog, QMessageBox, QAction, QMenu, QMenuBar
from PyQt5.QtGui import QPainter, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtSvg import QSvgRenderer
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import qdarktheme
import numpy as np
import math

from lib.file_manager import FileManager 
from lib.neural_network import AIManager
from lib.strategies_manager import StrategyManager
from lib.settings_window import SettingsDialog
from lib.data_loader import DataDownloadThread
from lib.mpl_canvas import MPlCanvas
from lib.positions_table import PositionsTable
from lib.chart_updater import ChartUpdater

pd.options.mode.chained_assignment = None

class CryptoTradingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.file_handler = FileManager(self)
        self.strategy_manager = StrategyManager()
        self.ai_manager = AIManager(self)
        self.chart_updater = ChartUpdater()
        self.initUI()       
        self.load_external_strategies()
      
# Инициализация окна

    def initUI(self):
        self.df = []
        self.setWindowTitle('Cheetos Trading')

        # Загружаем настройки    
        self.settings = QSettings("MyApp", "MyCompany")
        self.load_settings()

        self.data_loader = None
        self.current_data = None
        self.setGeometry(100, 100, 1300, 800)

        self.layout = QVBoxLayout(self)


        # Создаем лейаут полей ввода и добавляем в layout
        inputs_layout = self.get_inputs_layout()
        self.layout.addLayout(inputs_layout)

        self.stats = {'winrate': '0%', \
            'profit': '0%', \
            'trades': '0', \
            'period': '0 days', \
            'init': '0 USDT', \
            'final': '0 USDT', \
            'drawdown': '0%'}

        # Создаем canvas и добавляем в layout
        self.canvas = MPlCanvas(facecolor='#151924', textcolor = 'white')
        self.layout.addWidget(self.canvas)

        
        # Загружаем тему
        self.current_theme = self.load_theme() 
        self.apply_theme()

        self.menubar = self.get_menubar()
        self.layout.setContentsMargins(9, 0, 9, 9)
        self.layout.setMenuBar(self.menubar)

        # Включаем масштабирование и перемещения графиков
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.zoom()
        self.toolbar.pan()
        self.toolbar.setParent(None)
        #layout.addWidget(self.toolbar)

        self.canvas.updateGeometry()
        self.show()

    def get_menubar(self):

        if self.current_theme == "dark":
            icon_color = Qt.white        
        else:
            icon_color = Qt.black

        if hasattr(self, 'menubar'):
            self.layout.removeWidget(self.menubar)
            self.menubar.deleteLater()
        
        menubar = QMenuBar()

        menubar.setStyleSheet("""
            QMenuBar {
                font-size: 13px;
            }
            QMenu {
                font-size: 13px; 
            }
        """)

        file_menu = QMenu(' Файл ', self)
        menubar.addMenu(file_menu)
        
        draw_action = QAction("Открыть", self)
        draw_action.triggered.connect(self.open_and_draw)
        draw_action.setIcon(self.recolor_svg_icon("resources/folder.svg", icon_color))
        file_menu.addAction(draw_action)

        open_action = QAction('Скачать и сохранить', self)
        open_action.triggered.connect(self.download_and_save)
        open_action.setIcon(self.recolor_svg_icon("resources/download.svg", icon_color))
        file_menu.addAction(open_action)

        dad_action = QAction("Скачать и посмотреть", self)
        dad_action.triggered.connect(self.download_and_draw)
        dad_action.setIcon(self.recolor_svg_icon("resources/file.svg", icon_color))
        file_menu.addAction(dad_action)

        strat_menu = QMenu(' Тестирование ', self)
        menubar.addMenu(strat_menu)

        dat_action = QAction('Скачать данные', self)
        dat_action.triggered.connect(self.download_and_run)

        oat_action = QAction('Открыть данные', self)
        oat_action.triggered.connect(self.open_and_run)

        test_action = QAction('Протестировать на текущих данных', self)
        test_action.triggered.connect(self.download_and_save)
        
        strat_submenu = strat_menu.addMenu("Запуск")
        strat_submenu.setIcon(self.recolor_svg_icon("resources/stopwatch.svg", icon_color))
        strat_submenu.addAction(dat_action)
        strat_submenu.addAction(oat_action)
        strat_submenu.addAction(test_action)

        strat_menu.addSeparator()

        upd_action = QAction('Запустить', self)
        upd_action.triggered.connect(self.start_chart_updates)

        stop_upd_action = QAction('Остановить', self)
        stop_upd_action.triggered.connect(self.stop_chart_updates)
        
        upd_submenu = strat_menu.addMenu("Авто-обновление")
        upd_submenu.setIcon(self.recolor_svg_icon("resources/time-refresh.svg", icon_color))
        upd_submenu.addAction(upd_action)
        upd_submenu.addAction(stop_upd_action)

        strat_menu.addSeparator()

        open_poss_action = QAction('Открыть список позиций', self)
        open_poss_action.triggered.connect(self.open_positions_table)
        open_poss_action.setIcon(self.recolor_svg_icon("resources/binoculars.svg", icon_color))
        strat_menu.addAction(open_poss_action)

        strat_submenu.addSeparator()

        import_action = QAction('Добавить стратегию из файла', self)
        import_action.triggered.connect(self.import_strategy)
        import_action.setIcon(self.recolor_svg_icon("resources/import.svg", icon_color))
        strat_menu.addAction(import_action)

        reimport_action = QAction('Обновить стратегии', self)
        reimport_action.triggered.connect(self.load_external_strategies)
        reimport_action.setIcon(self.recolor_svg_icon("resources/refresh.svg", icon_color))
        strat_menu.addAction(reimport_action)

        export_action = QAction('Экспорт стратегии', self)
        export_action.triggered.connect(self.export_strategy)
        export_action.setIcon(self.recolor_svg_icon("resources/export.svg", icon_color))
        strat_menu.addAction(export_action)




        ai_menu = QMenu(' ИИ ', self)
        menubar.addMenu(ai_menu)

        tai_action = QAction('Обучить', self)
        tai_action.triggered.connect(self.ai_manager.train_model)
        tai_action.setIcon(self.recolor_svg_icon("resources/integrations.svg", icon_color))
        ai_menu.addAction(tai_action)

        rai_action = QAction('Запустить', self)
        rai_action.triggered.connect(self.ai_manager.run_ai)
        rai_action.setIcon(self.recolor_svg_icon("resources/brain-organ.svg", icon_color))
        ai_menu.addAction(rai_action)



        theme_menu = QMenu(' Оформление ', self)
        menubar.addMenu(theme_menu)

        toggle_theme_action = QAction('Сменить тему', self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        toggle_theme_action.setIcon(self.recolor_svg_icon("resources/theme.svg", icon_color))
        theme_menu.addAction(toggle_theme_action)

        settings_menu = QMenu(' Правка ', self)
        menubar.addMenu(settings_menu)

        settings_action = QAction('Настройки', self)
        settings_action.triggered.connect(self.open_settings_dialog)
        settings_action.setIcon(self.recolor_svg_icon("resources/cogwheel.svg", icon_color))
        settings_menu.addAction(settings_action)

        help_menu = QMenu(' Справка ', self)
        menubar.addMenu(help_menu)

        return menubar
    
    def recolor_svg_icon(self, svg_path, color):
        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(32, 32)  # Размер иконки
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()

        return QIcon(pixmap)
    



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

    def load_external_strategies(self):
        strategy_directory = self.file_handler.check_strategy_directory()
        if strategy_directory != None:
            self.strategy_manager.strategy_directory = strategy_directory
            self.strategy_manager.load_strategies_from_directory()
            self.strat_input.clear()
            self.strat_input.addItems(self.strategy_manager.strategy_dict.keys())

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
        self.refresh_interval = int(self.settings.value("refresh_interval", "10"))
        print(f"Загружены настройки: Комиссия: {self.commission}, Начальный баланс: {self.initial_balance}, Плечо: {self.leverage}, Профит фактор: {self.profit_factor}, Размер позиции: {self.position_size}, Тип: {self.position_type}, Частота обновления: {self.refresh_interval}")
    
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
            self.finalize_canvas()
            self.draw_canvas()
            self.menubar = self.get_menubar()
            self.layout.setMenuBar(self.menubar)
                
        else:
            qdarktheme.setup_theme(self.current_theme)
            self.canvas.update_colors(facecolor='#ffffff', textcolor = 'black')
            self.plot_statistics()
            self.finalize_canvas()
            self.draw_canvas()
            self.menubar = self.get_menubar()
            self.layout.setMenuBar(self.menubar)

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

    def open_and_draw(self):
        if self.file_handler.load_candlesticks():
            self.canvas.ax1.clear()
            self.canvas.ax2.clear()
            self.canvas.ax3.clear()
            self.plot(self.df, [], [], [])

    def download_and_run(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        run = True

        self.thread = DataDownloadThread(symbol, interval, limit, run)
        self.thread.progress_changed.connect(self.on_progress_changed) 
        self.thread.data_downloaded.connect(self.on_data_downloaded_run_it)
        self.thread.start()  # Запускаем поток

    def download_and_save(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        run = False
    
        self.thread = DataDownloadThread(symbol, interval, limit, run)
        self.thread.progress_changed.connect(self.on_progress_changed)
        self.thread.data_downloaded.connect(self.on_data_downloaded_save_it)
        self.thread.start()

    def download_and_draw(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        run = True

        self.thread = DataDownloadThread(symbol, interval, limit, run)
        self.thread.progress_changed.connect(self.on_progress_changed) 
        self.thread.data_downloaded.connect(self.on_data_downloaded_draw_it)
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
    
    def on_data_downloaded_draw_it(self, data):
        # Метод, который будет вызван после завершения скачивания
        self.df = data
        self.canvas.ax1.clear()
        self.canvas.ax2.clear()
        self.canvas.ax3.clear()
        self.plot(self.df, [], [], [])



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
    
    def on_calculation_complete(self, positions, balance, indicators):
        self.canvas.ax1.clear()
        self.canvas.ax2.clear()
        self.canvas.ax3.clear()
        self.plot(self.df, positions, balance, indicators)

# Отрисовка графиков

    def plot(self, df, positions, balance, indicators):

        if len(df) <= 5000 and len(df) > 0:
            # Рисуем индикаторы
            self.plot_indicators(df, indicators)
            # Рисуем свечи            
            self.plot_candles(df)
            # Рисуем сделки
            self.plot_trades(positions)

        if len(positions) > 0:
            # Рисуем баланс
            self.plot_balance(balance)
            # Получаем статистику
            self.stats = self.get_statistic(balance, positions)
            # Рисуем статистику
            self.plot_statistics()


        self.finalize_canvas()
        self.draw_canvas()
        self.bar.setValue(100)

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

    def get_statistic(self, balance, positions):
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
        for position in positions:
            if position['pnl'] > 0:
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

    def plot_trades(self, positions):
        for position in positions:
            if position['posSide'] == 'long':
                self.canvas.ax1.plot(mdates.date2num(position['openTimestamp']), position['openPrice'], marker='^', color='lime', markersize=7)
                self.canvas.ax1.plot(mdates.date2num(position['closeTimestamp']), position['closePrice'], marker='X', color='salmon', markersize=7)
            if position['posSide'] == 'short':
                self.canvas.ax1.plot(mdates.date2num(position['openTimestamp']), position['openPrice'], marker='v', color='salmon', markersize=7)
                self.canvas.ax1.plot(mdates.date2num(position['closeTimestamp']), position['closePrice'], marker='X', color='lime', markersize=7)
        self.bar.setValue(25)

        # Рисуем области tp и sl 
        for position in positions:
            if position['tpTriggerPx'] > 0 and position['slTriggerPx'] > 0:
                if position['posSide'] == 'long':
                    self.canvas.ax1.add_patch(plt.Rectangle(
                        (mdates.date2num(position['openTimestamp']), position['openPrice']),
                        mdates.date2num(position['closeTimestamp']) - mdates.date2num(position['openTimestamp']),
                        position['tpTriggerPx'] - position['openPrice'],
                        color='lightgreen', alpha=0.1
                    ))
                    self.canvas.ax1.add_patch(plt.Rectangle(
                        (mdates.date2num(position['openTimestamp']), position['slTriggerPx']),
                        mdates.date2num(position['closeTimestamp']) - mdates.date2num(position['openTimestamp']),
                        position['openPrice'] - position['slTriggerPx'],
                        color='salmon', alpha=0.1
                    ))
                if position['posSide'] == 'short':
                    self.canvas.ax1.add_patch(plt.Rectangle(
                        (mdates.date2num(position['openTimestamp']), position['openPrice']),
                        mdates.date2num(position['closeTimestamp']) - mdates.date2num(position['openTimestamp']),
                        position['slTriggerPx'] - position['openPrice'],
                        color='salmon', alpha=0.1
                    ))
                    self.canvas.ax1.add_patch(plt.Rectangle(
                        (mdates.date2num(position['openTimestamp']), position['tpTriggerPx']),
                        mdates.date2num(position['closeTimestamp']) - mdates.date2num(position['openTimestamp']),
                        position['openPrice'] - position['tpTriggerPx'],
                        color='lightgreen', alpha=0.1
                    ))
            else:
                color = 'lightgreen' if position['pnl'] >= 0 else 'salmon'

                self.canvas.ax1.add_patch(plt.Rectangle(
                    (mdates.date2num(position['openTimestamp']), position['openPrice']),
                    mdates.date2num(position['closeTimestamp']) - mdates.date2num(position['openTimestamp']),
                    position['closePrice'] - position['openPrice'],
                    color=color, alpha=0.1
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

    def finalize_canvas(self):
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

    def draw_canvas(self):
        self.canvas.draw()
        self.show()


# Внешние взаимодействия

    def open_positions_table(self):
        positions_table = PositionsTable(self.strategy_manager.positions, self.current_theme)
        positions_table.exec_()

    def start_chart_updates(self):
        """Запускает обновление графика в реальном времени."""
        print('Обновление графика началось')
        self.thread = DataDownloadThread(self.symbol_input.currentText(), self.interval_input.currentText(), 300, True)
        self.thread.data_downloaded.connect(self.on_data_downloaded_run_it)

        self.chart_updater.update_chart_signal.connect(self.update_chart)
        self.chart_updater.set_refresh_interval(self.refresh_interval)
        self.chart_updater.start_updating()

    def stop_chart_updates(self):
        """Останавливает обновление графика."""
        print('Обновление графика приостановлено')

        self.chart_updater.stop_updating()
        #QMessageBox.information(self, "График", "Обновление графика приостановлено")

    def update_chart(self):
        """Метод для обновления графика (вставить логику обновления графика)."""
        print('Обновление')
        self.thread.start()  # Запускаем поток

        
