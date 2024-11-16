from PyQt5.QtWidgets import  QVBoxLayout, QWidget, QHBoxLayout, QComboBox, QSpinBox, QProgressBar, QFrame, QDialog, QAction, QMenu, QMenuBar, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPainter, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSettings, QSize
from pyqttoast import Toast, ToastPreset
from PyQt5.QtSvg import QSvgRenderer
import pyqtgraph as pg
import pandas as pd
import numpy as np
import qdarktheme
import datetime
import logging
import math
import os


from lib.managers.strategies_manager import StrategyManager
from lib.windows.positions_window import PositionsTable
from lib.windows.settings_window import SettingsDialog
from lib.api.cryptocompare_api import CryptocompareApi
from lib.managers.trading_timer import TradingTimer
from lib.api.okx_load_api import DataDownloadThread
from lib.managers.file_manager import FileManager 
from lib.managers.neural_network import AIManager
from lib.managers.price_timer import PriceTimer
from lib.managers.pg_canvas import PGCanvas
from lib.windows.log_window import LogWindow
from lib.api.okx_trade_api import OKXApi

pd.options.mode.chained_assignment = None

class CryptoTradingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.is_trade = False
        self.positions = None
        self.previous_price = '0.0'
        self.file_handler = FileManager(self)
        self.strategy_manager = StrategyManager()
        self.ai_manager = AIManager(self)
        self.icon_dir = "resources/crypto_icons"
        self.initUI()       
        self.load_external_strategies()
        self.api = OKXApi(api_key='your_api_key', api_secret='your_api_secret', passphrase='your_passphrase')
        logging.basicConfig(filename='trading_log.txt',
                    level=logging.INFO,
                    format='%(asctime)s - %(message)s')
        self.log_window = LogWindow()
        self.setup_price_updates()
        


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

        

        # Создаем canvas и добавляем в layout
        self.canvas = PGCanvas(facecolor='#151924', textcolor = 'white')
        self.layout.addWidget(self.canvas.get_canvas())
        self.canvas.add_cursor_line()
     
        # Загружаем тему
        self.current_theme = self.load_theme() 
        self.apply_theme()

        self.menubar = self.get_menubar()
        self.layout.setContentsMargins(9, 9, 9, 9)
        self.layout.setMenuBar(self.menubar)

        self.show()

    def crosshair(self, sel):
        x = sel.target[0]
        y1 = np.interp(x, self.plot1x, self.plot1y)
        self.hline1.set_ydata([y1])
        self.vline1.set_xdata([x])
        
    def add_toolbar(self):
        self.layout.addWidget(self.toolbar)

    def del_toolbar(self):
        self.toolbar.setParent(None)
        
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

        icon_label = QLabel(self)
        pixmap = QPixmap("resources/cheetoslogo.svg")  
        scaled_pixmap = pixmap.scaled(QSize(48, 24)) 
        icon_label.setPixmap(scaled_pixmap)
        icon_label.setFixedSize(48, 24) 

        # Добавляем иконку в menubar слева
        menubar.setCornerWidget(icon_label, Qt.TopLeftCorner)

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

        dat_action = QAction('Загрузить данные', self)
        dat_action.triggered.connect(self.download_and_run)

        oat_action = QAction('Открыть данные', self)
        oat_action.triggered.connect(self.open_and_run)

        test_action = QAction('Протестировать на текущих данных', self)
        test_action.triggered.connect(self.run_strategy)

        strat_submenu = strat_menu.addMenu("Запустить")
        strat_submenu.setIcon(self.recolor_svg_icon("resources/stopwatch.svg", icon_color))
        strat_submenu.addAction(dat_action)
        strat_submenu.addAction(oat_action)
        strat_submenu.addAction(test_action)

        strat_menu.addSeparator()

        upd_action = QAction('Запустить', self)
        upd_action.triggered.connect(self.start_price_updates)

        stop_upd_action = QAction('Остановить', self)
        stop_upd_action.triggered.connect(self.stop_price_updates)
        
        upd_submenu = strat_menu.addMenu("Обновление цены")
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


        trade_menu = QMenu(' Торговля ', self)
        menubar.addMenu(trade_menu)

        trade_start_action = QAction('Запустить', self)
        trade_start_action.triggered.connect(self.start_trading)
        trade_start_action.setIcon(self.recolor_svg_icon("resources/export.svg", icon_color))
        trade_menu.addAction(trade_start_action)

        trade_stop_action = QAction('Остновить', self)
        trade_stop_action.triggered.connect(self.stop_trading)
        trade_stop_action.setIcon(self.recolor_svg_icon("resources/export.svg", icon_color))
        trade_menu.addAction(trade_stop_action)

        open_log_action = QAction('Открыть логи', self)
        open_log_action.triggered.connect(self.show_log_window)
        open_log_action.setIcon(self.recolor_svg_icon("resources/export.svg", icon_color))
        trade_menu.addAction(open_log_action)

        set_api_action = QAction('Настроить API', self)
        set_api_action.setIcon(self.recolor_svg_icon("resources/export.svg", icon_color))
        trade_menu.addAction(set_api_action)



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

        add_tb_action = QAction('Открыть тулбар', self)
        add_tb_action.triggered.connect(self.add_toolbar)
        add_tb_action.setIcon(self.recolor_svg_icon("resources/theme.svg", icon_color))
        theme_menu.addAction(add_tb_action)

        del_tb_action = QAction('Скрыть тулбар', self)
        del_tb_action.triggered.connect(self.del_toolbar)
        del_tb_action.setIcon(self.recolor_svg_icon("resources/theme.svg", icon_color))
        theme_menu.addAction(del_tb_action)

        settings_menu = QMenu(' Правка ', self)
        menubar.addMenu(settings_menu)

        settings_action = QAction('Настройки', self)
        settings_action.triggered.connect(self.open_settings_dialog)
        settings_action.setIcon(self.recolor_svg_icon("resources/settings2.svg", icon_color))
        settings_menu.addAction(settings_action)

        crypto_list_update_action = QAction('Перезагрузить список криптовалют', self)
        crypto_list_update_action.triggered.connect(self.update_crypto_dropdown)
        crypto_list_update_action.setIcon(self.recolor_svg_icon("resources/settings2.svg", icon_color))
        settings_menu.addAction(crypto_list_update_action)


        

        help_menu = QMenu(' Справка ', self)
        menubar.addMenu(help_menu)

        return menubar

    def get_inputs_layout(self):
        font_size = 10 
        
        self.symbol_input = QComboBox(self)
        font = self.symbol_input.font()
        font.setPointSize(font_size)
        self.symbol_input.setMinimumWidth(200)
        self.symbol_input.setIconSize(QSize(40, 40))
        self.symbol_input.setMaximumHeight(25) 
        self.update_crypto_dropdown()
        self.symbol_input.setFont(font)
        self.symbol_input.currentIndexChanged.connect(self.update_price_symbol)

        self.price_label = QLabel(f"<p style='color: grey; font-size: 7pt; margin: 0px; padding: 0px;'>рын.</p>"
                f"<p style='font-size: 10pt; font-weight: bold; margin: 0px; padding: 0px;'>0.0</p>")
        self.price_label.setAlignment(Qt.AlignLeft)
        self.price_label.setMinimumWidth(70)

        self.interval_input = QComboBox(self)
        self.interval_input.addItems(['1m', '5m', '15m','30m', '1H', '4H', '12H','1D'])
        self.interval_input.setMaximumHeight(25) 
        self.interval_input.setCurrentIndex(2)
        self.interval_input.setFont(font)

        self.limit_input = QSpinBox(self)
        self.limit_input.setRange(100, 100000)
        self.limit_input.setValue(500)
        self.limit_input.setSingleStep(500)
        self.limit_input.setMaximumHeight(25) 
        self.limit_input.setFont(font)

        self.strat_input = QComboBox(self)
        self.strat_input.addItems(self.strategy_manager.strategy_dict.keys())
        self.strat_input.setFont(font)
        self.strat_input.setMaximumHeight(25) 

        self.bar = QProgressBar(self) 
        self.bar.setGeometry(200, 100, 200, 50) 
        self.bar.setMaximumHeight(25) 
        self.bar.setValue(0) 
        self.bar.setAlignment(Qt.AlignCenter) 

        inputs_layout = QHBoxLayout()
        inputs_layout.addWidget(self.symbol_input)
        inputs_layout.addWidget(self.price_label)
        inputs_layout.addWidget(self.interval_input)
        inputs_layout.addWidget(self.limit_input)
        inputs_layout.addWidget(self.strat_input)
        inputs_layout.addWidget(self.bar)

        return inputs_layout
    
    def load_icon_from_file(self, crypto_name):
        """Загружает иконку из локальной директории, если она существует"""
        icon_path = os.path.join(self.icon_dir, f"{crypto_name}.png")
        if os.path.exists(icon_path):
            return QPixmap(icon_path)
        return None

    def load_crypto_list(self):
        """Загружает список популярных криптовалют и их иконки"""
        stablecoins = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'PAX', 'GUSD', 'SUSD'}
        self.cryptocompare_api = CryptocompareApi()
        self.cryptocompare_api.show_toast.connect(self.show_toast)
        data = self.cryptocompare_api.get_coins()

        crypto_list = []
        for coin in data['Data']:
                symbol = coin['CoinInfo']['Name']
                if symbol not in stablecoins:
                    crypto_name = coin['CoinInfo']['Name']

                    # Попытка загрузить иконку из файла
                    pixmap = self.load_icon_from_file(crypto_name)
                    
                    if pixmap is None:
                        # Если иконка не найдена, загружаем её с API
                        pixmap = self.cryptocompare_api.load_icon_from_url(coin, self.icon_dir)

                    crypto_list.append((crypto_name, pixmap))

        return crypto_list
    
    def update_crypto_dropdown(self):
        """Обновляет выпадающий список криптовалют"""
        try:
            crypto_list = self.load_crypto_list()

            # Очищаем выпадающий список перед обновлением
            self.symbol_input.clear()

            # Добавляем новые элементы в выпадающий список
            for crypto_name, pixmap in crypto_list:
                if pixmap is not None and not pixmap.isNull():
                    self.symbol_input.addItem(QIcon(pixmap), str(crypto_name+'-USDT'))
                else:
                    # Если иконка не найдена, используем дефолтную иконку
                    self.symbol_input.addItem(QIcon("resources/crypto_icons/default.png"), crypto_name)

        except Exception as e:
            self.show_toast(ToastPreset.ERROR, 'Ошибка загрузки иконок валют. Скорее всего нет интернета или не отвечает апи cryptocompare.com',  f"{e}")

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
        self.thread.import_complete.connect(self.add_strategy)
        self.thread.create_toast.connect(self.show_toast)
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
            self.update_strat_input()

    def update_strat_input(self):
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
        #self.show_toast(ToastPreset.SUCCESS, 'Загружены настройки!',  f"Комиссия: {self.commission}, Начальный баланс: {self.initial_balance}, Плечо: {self.leverage}, Профит фактор: {self.profit_factor}, Размер позиции: {self.position_size}, Тип: {self.position_type}, Частота обновления: {self.refresh_interval}")

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
            #self.plot_statistics()
            #self.finalize_canvas()
            #self.draw_canvas()
            self.menubar = self.get_menubar()
            self.layout.setMenuBar(self.menubar)
                
        else:
            qdarktheme.setup_theme(self.current_theme)
            self.canvas.update_colors(facecolor='#ffffff', textcolor = 'black')
            #self.plot_statistics()
            #self.finalize_canvas()
            #self.draw_canvas()
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
            self.plot(self.df, [], [], [])

    def download_and_run(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        self.bar.setFormat("Загрузка")

        self.thread = DataDownloadThread(symbol, interval, limit)
        self.thread.progress_changed.connect(self.on_progress_changed) 
        self.thread.data_downloaded.connect(self.on_data_downloaded_run_it)
        self.thread.show_toast.connect(self.show_toast)
        self.stop_price_updates()
        self.thread.start()  # Запускаем поток

    def download_and_save(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        self.bar.setFormat("Загрузка")
    
        self.thread = DataDownloadThread(symbol, interval, limit)
        self.thread.progress_changed.connect(self.on_progress_changed)
        self.thread.data_downloaded.connect(self.on_data_downloaded_save_it)
        self.thread.show_toast.connect(self.show_toast)
        self.stop_price_updates()
        self.thread.start()

    def download_and_draw(self):
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        self.bar.setFormat("Загрузка")

        self.thread = DataDownloadThread(symbol, interval, limit)
        self.thread.progress_changed.connect(self.on_progress_changed) 
        self.thread.data_downloaded.connect(self.on_data_downloaded_draw_it)
        self.thread.show_toast.connect(self.show_toast)
        self.stop_price_updates()
        self.thread.start()  # Запускаем поток

    def on_progress_changed(self, value):
        # Обновляем значение прогресс-бара
        self.bar.setValue(value)

    def on_data_downloaded_run_it(self, data):
        # Метод, который будет вызван после завершения скачивания
        self.thread.progress_changed.disconnect(self.on_progress_changed) 
        self.thread.data_downloaded.disconnect(self.on_data_downloaded_run_it)
        self.thread = None
        self.df = data
        self.run_strategy()

    def on_data_downloaded_save_it(self, data):
        # Метод, который будет вызван после завершения скачивания
        self.df = data
        self.file_handler.save_candlesticks()
        self.start_price_updates()
    
    def on_data_downloaded_draw_it(self, data):
        # Метод, который будет вызван после завершения скачивания
        self.df = data
        print(self.df)
        self.plot(self.df, [], [], [])

    def run_strategy(self):
        self.bar.setFormat("Тестирование")

        self.thread = self.strategy_manager

        self.thread.profit_factor = self.profit_factor
        self.thread.leverage = self.leverage
        self.thread.initial_balance = self.initial_balance
        self.thread.position_type = self.position_type
        self.thread.position_size = self.position_size
        self.thread.df = self.df
        self.thread.strat_name = self.strat_input.currentText()
        self.thread.commission = self.commission

        self.thread.progress_changed.connect(self.on_progress_changed) 

        if self.is_trade == 1:
            self.thread.calculation_complete.connect(self.on_calculation_complete_on_trade)
        else:
            self.thread.calculation_complete.connect(self.on_calculation_complete)
        
        self.thread.run() 
    
    def on_calculation_complete(self, positions, balance, indicators):
        self.positions = positions
        self.thread.progress_changed.disconnect(self.on_progress_changed) 
        self.thread.calculation_complete.disconnect(self.on_calculation_complete)
        self.plot(self.df, positions, balance, indicators)

    def on_calculation_complete_on_trade(self, positions, balance, indicators):
        self.positions = self.compare_positions(positions, self.positions)
        self.thread.progress_changed.disconnect(self.on_progress_changed) 
        self.thread.calculation_complete.disconnect(self.on_calculation_complete_on_trade)
        self.plot(self.df, positions, balance, indicators)

    def compare_positions(self, current_positions, previous_positions):
        log = []
        """
        Синхронизирует изменения между таблицами позиций и записывает лог в файл.
        
        :param current_positions: DataFrame с текущими позициями
        :param previous_positions: DataFrame с позициями с предыдущего цикла или None, если это первый цикл
        :param exchange_api: Объект API для работы с биржей
        :param log_file_path: Путь к файлу для записи логов
        :return: Обновленная таблица с синхронизацией
        """

            # Первый цикл: если нет предыдущей таблицы
        if not previous_positions:
            for pos in current_positions:
                pos['syncStatus'] = 'synced'  # Добавляем поле синхронизации
            return current_positions
        
        # Сравнение текущих и предыдущих позиций
        for current_pos in current_positions:
            matching_pos = next((p for p in previous_positions if p['posId'] == current_pos['posId']), None)

            # Игнорируем не синхронизированные позиции из предыдущей таблицы
            if matching_pos and matching_pos['syncStatus'] == 'unsynced':
                continue
            
            # Обрабатываем изменения тейка, стопа, статуса
            if matching_pos:
                changes = []
                
                if current_pos['tpTriggerPx'] != matching_pos['tpTriggerPx']:
                    changes.append('take profit changed')

                if current_pos['slTriggerPx'] != matching_pos['slTriggerPx']:
                    changes.append('stop loss changed')

                if current_pos['status'] != matching_pos['status']:
                    changes.append(f"status changed to {current_pos['status']}")

                if changes:
                    try:
                        # Пытаемся синхронизировать с биржей
                        #self.api.sync_position(current_pos)
                        current_pos['syncStatus'] = 'synced'
                        message = f"Position {current_pos['posId']} synced: {', '.join(changes)}"
                        self.log_message(message)
                        self.log_window.update_log(message)
                    except Exception as e:
                        current_pos['syncStatus'] = 'unsynced'
                        message = f"Error syncing position {current_pos['posId']}: {str(e)}"
                        self.log_message(message)
                        self.log_window.update_log(message)
                else:
                    current_pos['syncStatus'] = 'synced'
            else:
                if current_pos['status'] == 'open':
                    # Новая позиция
                    try:
                        #self.api.open_position(current_pos)
                        current_pos['syncStatus'] = 'synced'
                        message = f"New position {current_pos['posId']} opened"
                        self.log_message(message)
                        self.log_window.update_log(message)
                    except Exception as e:
                        current_pos['syncStatus'] = 'unsynced'
                        message = f"Error opening new position {current_pos['posId']}: {str(e)}"
                        self.log_message(message)
                        self.log_window.update_log(message)
        
        print(log)
        return current_positions

# Отрисовка графиков

    """
    def plot(self, df, positions, balance, indicators):
        self.bar.setFormat("Отрисовка")

        if len(df) <= 5000 and len(df) > 0:
            # Рисуем индикаторы
            self.plot_indicators(df, indicators)
            # Рисуем свечи            
            self.plot_candles(df)
            # Рисуем сделки
            self.plot_trades(positions)
            

        if len(positions) > 0:
            self.bar.setValue(90)
            # Рисуем баланс
            self.plot_balance(balance)
            # Получаем статистику
            self.stats = self.get_statistic(balance, positions)
            # Рисуем статистику
            self.plot_statistics()


        self.finalize_canvas()
        self.draw_canvas()
        self.bar.setValue(100)
        self.bar.setFormat("Готово")
        self.start_price_updates()
        
    def plot_candles(self, df):
        percent5 = int(len(df) / 80)
        index = 0 
        label_added = False
        candlestick_data = zip(mdates.date2num(df.index.to_pydatetime()), df['open'], df['high'], df['low'], df['close'])

        for date, open, high, low, close in candlestick_data:
            if index % percent5 == 0:
                self.bar.setValue(int(index / len(df) * 80))
            index += 1
            color = '#089981' if close >= open else '#F23645'
            if not label_added:
                self.canvas.ax1.plot([date, date], [open, close], color=color, label = str(self.symbol_input.currentText()+' OKX'), linewidth=2)
                label_added = True
            else:
                self.canvas.ax1.plot([date, date], [open, close], color=color, linewidth=2)

            self.canvas.ax1.plot([date, date], [low, high], color=color, linewidth=0.8)
            self.canvas.ax1.legend(loc='upper left')

    def plot_indicators(self, df, indicators):
        flag_ax2 = False
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
                    flag_ax2 = True
            else:
                print(f"Индикатор '{column}' отсутствует в DataFrame.")

            if flag_ax2:
                self.canvas.ax2.legend(loc='upper right')

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
                        (balance['ts'].iloc[-1] - balance['ts'].iloc[0])/patch_count*0.95,
                        abs((balance['value'].iloc[i+step] - balance['value'].iloc[i]) / balance['value'].iloc[i])/max_rise*(max(balance['value'])-min(balance['value'])),
                        color=patch_color, alpha=0.2
                    ))  
            
        self.canvas.ax3.legend(loc='upper left')

    

    def plot_trades(self, positions):
        for position in positions:
            if position['posSide'] == 'long':
                self.canvas.ax1.plot(mdates.date2num(position['openTimestamp']), position['openPrice'], marker='^', color='lime', markersize=7)
                if position['status'] == 'closed':
                    self.canvas.ax1.plot(mdates.date2num(position['closeTimestamp']), position['closePrice'], marker='X', color='salmon', markersize=7)
            if position['posSide'] == 'short':
                self.canvas.ax1.plot(mdates.date2num(position['openTimestamp']), position['openPrice'], marker='v', color='salmon', markersize=7)
                if position['status'] == 'closed':
                    self.canvas.ax1.plot(mdates.date2num(position['closeTimestamp']), position['closePrice'], marker='X', color='lime', markersize=7)
                else:
                    self.canvas.ax1.axhline(y = position['openPrice'], xmin = mdates.date2num(position['openTimestamp']), xmax = len(self.df), linestyle = 'dashed', color = '#089981') 
        

        # Рисуем области tp и sl 
        for position in positions:
            if position['status'] == 'closed':
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

    def finalize_canvas(self):

        # Линии на фоне
        self.canvas.ax1.grid(True, axis='both', linewidth=0.3, color='gray')
        self.canvas.ax3.grid(True, axis='both', linewidth=0.3, color='gray', which="both")

        # Переустановка форматтера оси X
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        self.canvas.ax1.xaxis.set_major_locator(locator)
        self.canvas.ax1.xaxis.set_major_formatter(formatter)

    def draw_canvas(self):
        #multi = MultiCursor(self.canvas.fig.canvas, (self.canvas.ax1, self.canvas.ax3), color='r', lw=2, horizOn=True, vertOn=True) 

        self.canvas.draw()
        #self.show()

    """

    def plot(self, df, positions, balance, indicators):
        self.bar.setFormat("Отрисовка")

        self.canvas.candlestick_plot.clear()
        self.canvas.balance_plot.clear()

        self.canvas.plot_candlestick(df)
        self.canvas.plot_indicators(df, indicators)
        self.canvas.plot_balance(balance)
        self.canvas.plot_positions(positions, df)
        self.canvas.get_statistic(balance, positions)
        self.canvas.plot_statistic()


        self.canvas.add_cursor_line()
        
        self.bar.setValue(100)
        self.bar.setFormat("Готово")
        self.start_price_updates()

# Внешние взаимодействия

    def open_positions_table(self):
        if self.positions: 
            positions_table = PositionsTable(self.positions, self.current_theme, self.is_trade)
            positions_table.exec_()

    def setup_price_updates(self):
        self.price_updater = PriceTimer()
        self.price_updater.new_price_signal.connect(self.update_price)
        self.price_updater.set_refresh_interval(1)
        self.price_updater.update_symbol(self.symbol_input.currentText())
        self.start_price_updates()

    def start_price_updates(self):
        """Запускает обновление цены в реальном времени."""
        self.price_updater.start_updating()

    def update_price_symbol(self):
        if self.price_updater:
            self.price_updater.update_symbol(self.symbol_input.currentText())

    def stop_price_updates(self):
        """Останавливает обновление цены."""
        self.price_updater.stop_updating()

    def update_price(self, new_price):
        """Обновление цены на основе выбранной криптовалюты"""
        if self.previous_price is not None:
            if new_price > self.previous_price:
                self.price_label.setStyleSheet("color: #089981; padding: 0px; margin: 0px;")
            elif new_price < self.previous_price:
                self.price_label.setStyleSheet("color: #F23645; padding: 0px; margin: 0px;")
            else:
                if self.current_theme == "light":
                    self.price_label.setStyleSheet("color: black; padding: 0px; margin: 0px;")
                else:
                    self.price_label.setStyleSheet("color: white; padding: 0px; margin: 0px;")

            self.previous_price = new_price

            display_text = (f"<p style='color: grey; font-size: 7pt; margin: 0px; padding: 0px;'>рын.</p>"
                f"<p style='font-size: 10pt; font-weight: bold; margin: 0px; padding: 0px;'>{new_price}</p>")

            self.price_label.setText(display_text)
            self.price_label.repaint()

    def show_toast(self, preset, title, text):
        toast = Toast(self)
        toast.setDuration(7000)  # Hide after 5 seconds
        toast.setTitle(title)
        toast.setText(text)
        toast.applyPreset(preset)  # Apply style preset
        toast.show()

############

    def start_trading(self):
        self.is_trade = True
        self.positions = None
        self.bar.setFormat("Загрузка")

        self.timer = TradingTimer(sync_interval=1, delay=3)
        self.timer.update_chart_signal.connect(self.update_trading)
        self.timer.start()

    def stop_trading(self):
        self.timer.stop()
        self.timer = None
        self.is_trade = False
        
    def setup_logging(self, log_file='trading_log.txt'):
        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
        logger = logging.getLogger()
        return logger
    
    def show_log_window(self):
        self.log_window.show() 

    def log_message(self, message):
        logging.info(message)

    def update_trading(self):
        # Функция для загрузки данных и синхронизации с биржей
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        run = True
        self.thread = DataDownloadThread(symbol, interval, limit, run)
        self.thread.progress_changed.connect(self.on_progress_changed) 
        self.thread.data_downloaded.connect(self.on_data_downloaded_run_it)
        self.thread.start() 
        message = datetime.datetime.now().strftime("%I:%M:%S %p on %B %d, %Y")
        self.log_message(message)
        self.log_window.update_log(message)
        



    
    


        