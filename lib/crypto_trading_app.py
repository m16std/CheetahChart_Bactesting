from PyQt5.QtWidgets import  QVBoxLayout, QStyledItemDelegate, QWidget, QHBoxLayout, QComboBox, QSpinBox, QProgressBar, QFrame, QDialog, QAction, QMenu, QMenuBar, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox
from PyQt5.QtGui import QPainter, QPixmap, QIcon, QColor, QPainterPath, QPen
from PyQt5.QtCore import Qt, QSettings, QSize, QRect, QRectF, QTimer, QThread, pyqtSignal
from pyqttoast import Toast, ToastPreset
from PyQt5.QtSvg import QSvgRenderer
import pandas as pd
import numpy as np
import qdarktheme
from datetime import datetime, timezone
import logging
import os

from lib.managers.strategies_manager import StrategyManager
from lib.managers.trading_sync_manager import TradingSyncManager
from lib.windows.positions_window import PositionsWindow
from lib.windows.settings_window import SettingsWindow
from lib.api.cryptocompare_api import CryptocompareApi
from lib.threads.trading_timer import TradingTimer
from lib.api.okx_load_api import DataDownloadThread
from lib.managers.file_manager import FileManager, QFileDialog 
from lib.managers.neural_network import AIManager
from lib.threads.price_timer import PriceTimer
from lib.managers.pg_canvas import PGCanvas
from lib.windows.multitask.log_window import LogWindow
from lib.api.okx_trade_api import OKXApi
from lib.windows.real_positions_window import RealPositionsWindow
from lib.windows.multitask.multitask_window import MultitaskWindow
from PyQt5.QtWidgets import QSplitter
from lib.api.api_manager import APIManager
from lib.widgets.padded_item_delegate import PaddedItemDelegate
from lib.threads.trading_status_updater import TradingStatusUpdater
from lib.windows.python_editor_window import PythonEditorWindow
from lib.threads.strategy_test_thread import StrategyTestThread

pd.options.mode.chained_assignment = None

import os

class CryptoTradingApp(QWidget):
    add_tab_signal = pyqtSignal(QWidget, str)  # Сигнал для добавления новой вкладки
    update_tab_title_signal = pyqtSignal(str)  # Сигнал для обновления названия вкладки
    theme_changed_signal = pyqtSignal(str)  # Signal to notify theme changes

    def __init__(self):
        super().__init__()
        self.api_manager = APIManager()  # Инициализация APIManager
        # Инициализация переменных
        self.is_trade = False
        self.positions = None
        self.previous_price = '0.0'
        self.file_handler = FileManager(self)
        self.strategy_manager = StrategyManager()
        self.cryptocompare_api = CryptocompareApi()
        self.trading_sync_manager = TradingSyncManager()
        self.icon_dir = "resources/crypto_icons"
        logging.basicConfig(filename='trading_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')
        logging.info("Приложение запущено.")
        self.log_window = LogWindow()
        self.initUI()       
        self.load_external_strategies()
        self.setup_price_updates()

        self.active_api = None
        self.load_active_api()

        self.status_updater = TradingStatusUpdater(self)
        self.status_updater.update_signal.connect(self._apply_trading_status_update)
        self.timer_refresh = QTimer(self)  # Таймер для обновления окна торговли
        self.timer_refresh.timeout.connect(self.update_trading_status_window)
        self.timer_refresh.start(5000) 

     

# Инициализация окна

    def initUI(self):
        self.df = []
        self.setWindowTitle('Cheetos Trading')

        # Загрузка настроек    
        self.settings = QSettings("MyApp", "MyCompany")
        self.load_settings()

        self.data_loader = None
        self.current_data = None
        self.setGeometry(50, 50, 1300, 800)

        # Создание основного макета с разделителем
        self.splitter = QSplitter(Qt.Horizontal, self)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) 
        self.layout.setSpacing(1)
        self.layout.addWidget(self.splitter)

        # Левая часть разделителя (основное содержимое)
        self.left_widget = QWidget(self)
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(5, 5, 5, 0) 
        self.splitter.addWidget(self.left_widget)

        # Создание макета ввода и добавление в левый виджет
        inputs_layout = self.get_inputs_layout()
        self.left_layout.addLayout(inputs_layout)

        # Создание холста и добавление в левый виджет
        self.canvas = PGCanvas(facecolor='#151924', textcolor='white')
        self.left_layout.addWidget(self.canvas.get_canvas())
        self.canvas.add_cursor_line()

        # Правая часть разделителя (панель статуса торговли с окном логов ниже)
        self.right_splitter = QSplitter(Qt.Vertical, self)
        self.trading_status_window = MultitaskWindow(theme=self.load_theme(), parent=self)
        self.trading_status_window.start_trading_signal.connect(self.start_trading)
        self.trading_status_window.stop_trading_signal.connect(self.stop_trading)
        self.right_splitter.addWidget(self.trading_status_window)
        self.splitter.addWidget(self.right_splitter)

        # Установка начальных размеров разделителей
        self.splitter.setSizes([1050, 250])  # Левая часть занимает большую часть пространства

        # Загрузка темы и строки меню
        self.current_theme = self.load_theme()
        self.apply_theme()
        self.menubar = self.get_menubar()
        self.layout.setMenuBar(self.menubar)
        self.setLayout(self.layout)

        self.show()

    def toggle_log_window(self):
        """Переключение видимости окна логов."""
        if self.log_window.isVisible():
            self.log_window.hide()
            self.right_splitter.setSizes([600, 0])  # Скрыть окно логов
        else:
            self.log_window.show()
            self.log_window.load_logs()  # Загружаем содержимое файла лога
            self.right_splitter.setSizes([400, 200])  # Настроить размеры для отображения окна логов
 
 
    def get_menubar(self):

        if self.current_theme == "dark":
            icon_color = Qt.white        
        else:
            icon_color = Qt.black

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
        draw_action.triggered.connect(self.open_file)
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

        strat_menu.addSeparator()

        show_stats_action = QAction('Детальная статистика', self)
        show_stats_action.triggered.connect(self.show_detailed_statistics)
        show_stats_action.setIcon(self.recolor_svg_icon("resources/binoculars.svg", icon_color))
        strat_menu.addAction(show_stats_action)

        # Add optimization action
        optimize_action = QAction('Оптимизация параметров', self)
        optimize_action.triggered.connect(self.show_optimization_dialog)
        optimize_action.setIcon(self.recolor_svg_icon("resources/optimization.svg", icon_color))
        strat_menu.addAction(optimize_action)

        strat_menu.addSeparator()

        trade_menu = QMenu(' Торговля ', self)
        menubar.addMenu(trade_menu)

        add_trading_panel_action = QAction('Окно торговли', self)
        add_trading_panel_action.triggered.connect(self.toggle_trading_status_panel)
        add_trading_panel_action.setIcon(self.recolor_svg_icon("resources/open_window.svg", icon_color))
        trade_menu.addAction(add_trading_panel_action)

        # Add action to open real positions window
        open_real_positions_action = QAction('Окно позиций', self)
        open_real_positions_action.triggered.connect(self.open_real_positions_window)
        open_real_positions_action.setIcon(self.recolor_svg_icon("resources/binoculars.svg", icon_color))
        trade_menu.addAction(open_real_positions_action)

        set_api_action = QAction('Настроить API', self)
        set_api_action.triggered.connect(self.open_api_settings_dialog)
        set_api_action.setIcon(self.recolor_svg_icon("resources/export.svg", icon_color))
        trade_menu.addAction(set_api_action)

        # Restore "Check API" button
        check_api_action = QAction('Проверить API', self)
        check_api_action.triggered.connect(self.check_api_status)
        check_api_action.setIcon(self.recolor_svg_icon("resources/check.svg", icon_color))
        trade_menu.addAction(check_api_action)

        ai_menu = QMenu(' ИИ ', self)
        menubar.addMenu(ai_menu)

        tai_action = QAction('Обучить', self)
        tai_action.triggered.connect(self.train_model)
        tai_action.setIcon(self.recolor_svg_icon("resources/integrations.svg", icon_color))
        ai_menu.addAction(tai_action)

        rai_action = QAction('Запустить', self)
        rai_action.triggered.connect(self.train_model)
        rai_action.setIcon(self.recolor_svg_icon("resources/brain-organ.svg", icon_color))
        ai_menu.addAction(rai_action)

        theme_menu = QMenu(' Оформление ', self)
        menubar.addMenu(theme_menu)

        toggle_theme_action = QAction('Сменить тему', self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        toggle_theme_action.setIcon(self.recolor_svg_icon("resources/theme.svg", icon_color))
        theme_menu.addAction(toggle_theme_action)

        add_tb_action = QAction('Очистить график', self)
        add_tb_action.triggered.connect(self.clear_plot)
        add_tb_action.setIcon(self.recolor_svg_icon("resources/clean.svg", icon_color))
        theme_menu.addAction(add_tb_action)
        

        settings_menu = QMenu(' Правка ', self)
        menubar.addMenu(settings_menu)

        settings_action = QAction('Настройки', self)
        settings_action.triggered.connect(self.open_settings_dialog)
        settings_action.setIcon(self.recolor_svg_icon("resources/settings2.svg", icon_color))
        settings_menu.addAction(settings_action)

        crypto_list_update_action = QAction('Перезагрузить список криптовалют', self)
        crypto_list_update_action.triggered.connect(self.update_crypto_dropdown)
        crypto_list_update_action.setIcon(self.recolor_svg_icon("resources/refresh.svg", icon_color))
        settings_menu.addAction(crypto_list_update_action)

        help_menu = QMenu(' Справка ', self)
        menubar.addMenu(help_menu)

        return menubar

    def open_file(self):
        """Открывает файл и обрабатывает его в зависимости от типа."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "CSV or Python Files (*.csv *.py)")
        if file_name:
            if file_name.endswith(".csv"):
                if self.file_handler.load_candlesticks(file_name):
                    self.plot(self.df, [], [], [])
            elif file_name.endswith(".py"):
                editor_tab = PythonEditorWindow(file_name, theme=self.current_theme)
                self.add_tab_signal.emit(editor_tab, f"Редактор: {os.path.basename(file_name)}")
            else:
                QMessageBox.warning(self, "Ошибка", "Неподдерживаемый формат файла.")

    def get_inputs_layout(self):
        font_size = 13
        
        self.symbol_input = QComboBox(self)
        font = self.symbol_input.font()
        font.setPointSize(font_size)
        self.symbol_input.setMinimumWidth(200)
        self.symbol_input.setIconSize(QSize(60, 60))
        self.symbol_input.setMaximumHeight(25) 
        self.update_crypto_dropdown()
        self.symbol_input.setFont(font)
        self.symbol_input.currentIndexChanged.connect(self.update_price_symbol)
        self.symbol_input.setItemDelegate(PaddedItemDelegate(padding=3, height=34, parent=self.symbol_input))

        self.price_label = QLabel(f"<p style='color: grey; font-size: 10pt; margin: 0px; padding: 0px;'>рын.</p>"
                f"<p style='font-size: 13pt; font-weight: bold; margin: 0px; padding: 0px;'>0.0</p>")
        self.price_label.setAlignment(Qt.AlignLeft)
        self.price_label.setMinimumWidth(70)

        self.interval_input = QComboBox(self)
        self.interval_input.addItems(['1m', '5m', '15m','30m', '1H', '4H', '12H','1D'])
        self.interval_input.setMaximumHeight(25) 
        self.interval_input.view().setMinimumWidth(60) 
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
        self.strat_input.currentTextChanged.connect(self.on_strategy_changed)

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
    
    def on_strategy_changed(self, strategy_name):
        """Handle strategy selection change"""
        self.update_tab_title(strategy_name)
        # Get current strategy and update trading window
        current_strategy = self.strategy_manager.strategy_dict.get(strategy_name)
        if hasattr(self, 'trading_status_window'):
            self.trading_status_window.update_strategy(current_strategy)

    def update_tab_title(self, strategy_name):
        """Emit a signal to update the tab title with the selected strategy name."""
        self.update_tab_title_signal.emit(strategy_name)

    def load_icon_from_file(self, crypto_name):
        """Загружает иконку из локальной директории, если она существует"""
        icon_path = os.path.join(self.icon_dir, f"{crypto_name}.png")
        if os.path.exists(icon_path):
            return QPixmap(icon_path)
        return None

    def load_crypto_list(self):
        """Загружает список популярных криптовалют и их иконки"""
        stablecoins = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'PAX', 'GUSD', 'SUSD'}
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
        # Update strategy in trading window when strategy list changes
        if hasattr(self, 'trading_status_window'):
            current_strategy = self.strategy_manager.strategy_dict.get(self.strat_input.currentText())
            self.trading_status_window.update_strategy(current_strategy)
        
# Настройки

    def open_settings_dialog(self):
        dialog = SettingsWindow(self.settings, self)
        if (dialog.exec_() == QDialog.Accepted):
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

# Тема приложения theme

    def apply_theme(self, theme=None):
        """Apply the theme to CryptoTradingApp."""
        if theme:
            self.current_theme = theme  # Update the current theme if provided
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
            self.canvas.update_colors(facecolor='#151924', textcolor='white')
            if self.trading_status_window:
                self.trading_status_window.update_close_button_icon(Qt.white)
        else:
            qdarktheme.setup_theme(self.current_theme)
            self.canvas.update_colors(facecolor='#ffffff', textcolor='black')
            if self.trading_status_window:
                self.trading_status_window.update_close_button_icon(Qt.black)

        if hasattr(self, 'trading_status_window') and self.trading_status_window:
            self.trading_status_window.apply_theme(self.current_theme)

    def toggle_theme(self):
        # Переключаем между темной и светлой темой
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.current_theme = new_theme  # Обновляем текущую тему
        self.theme_changed_signal.emit(self.current_theme)

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
        self.thread.show_toast.disconnect(self.show_toast)
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
        current_strategy = self.strategy_manager.strategy_dict.get(self.strat_input.currentText())
    
        # Update trading status window with current strategy
        if hasattr(self, 'trading_status_window'):
            self.trading_status_window.update_strategy(current_strategy)
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

        # Заполнение таблицы позиций в окне торговли
        self.trading_status_window.update_data(
            is_active=self.is_trade,
            current_pair=self.symbol_input.currentText(),
            open_positions=positions,
            time_to_next_cycle="N/A",
            current_balance=0,
            floating_pnl=0,
            used_margin=0,
            min_margin=0
        )

        # Update statistics if available
        stats = self.calculate_detailed_statistics()
        self.trading_status_window.update_statistics(stats)

    def on_calculation_complete_on_trade(self, positions, balance, indicators):
        self.positions = self.trading_sync_manager.compare_positions(positions, self.positions)
        self.thread.progress_changed.disconnect(self.on_progress_changed) 
        self.thread.calculation_complete.disconnect(self.on_calculation_complete_on_trade)
        self.plot(self.df, positions, balance, indicators)




    def train_model(self):
        self.bar.setFormat("Обучение")

        if self.file_handler.load_candlesticks():
            self.thread = AIManager()
            self.thread.df = self.df

            #self.thread.progress_changed.connect(self.on_progress_changed) 
            self.thread.training_complete.connect(self.on_training_complete)
            self.thread.plot_some.connect(self.plot)
            
            self.thread.run() 

    def on_training_complete(self, model):
        self.model = model
        self.file_handler.save_model_dialog()
        #self.thread.progress_changed.disconnect(self.on_progress_changed) 
        self.thread.training_complete.disconnect(self.on_training_complete)
        self.thread.plot_some.connect(self.plot)
        #self.plot(self.df)

# Отрисовка графиков

    def clear_plot(self):
        self.canvas.candlestick_plot.clear()
        self.canvas.balance_plot.clear()

    def plot(self, df, positions, balance, indicators):
        self.bar.setFormat("Отрисовка")

        self.canvas.candlestick_plot.clear()
        self.canvas.balance_plot.clear()
        if (len(df) < 5001):
            self.canvas.plot_candlestick(df)
        if len(indicators)>0: self.canvas.plot_indicators(df, indicators)
        if len(balance)>0: self.canvas.plot_balance(balance)
        if len(positions)>0: 
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
            positions_table = PositionsWindow(self.positions, self.current_theme, self.is_trade)
            positions_table.exec_()

    def open_real_positions_window(self):
        """Fetch real positions from the API and open the RealPositionsWindow."""
        if not self.active_api:
            QMessageBox.warning(self, "Ошибка", "API не настроен. Пожалуйста, настройте API в разделе 'Настроить API'.")
            return

        try:
            window = RealPositionsWindow(self.trading_sync_manager.api, self.current_theme)
            window.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно позиций. Ошибка: {str(e)}")

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

            display_text = (f"<p style='color: grey; font-size: 10pt; margin: 0px; padding: 0px;'>рын.</p>"
                f"<p style='font-size: 13pt; font-weight: bold; margin: 0px; padding: 0px;'>{new_price}</p>")

            self.price_label.setText(display_text)
            self.price_label.repaint()

    def show_toast(self, preset, title, text):
        toast = Toast(self)
        toast.setDuration(7000)  # Hide after 5 seconds
        toast.setTitle(title)
        toast.setText(text)
        toast.applyPreset(preset)  # Apply style preset
        toast.show()

# Торговля

    def start_trading(self):
        self.is_trade = True
        self.positions = None
        self.bar.setFormat("Загрузка")

        if not hasattr(self, 'timer') or self.timer is None:
            self.timer = TradingTimer(sync_interval=1, delay=3)
            self.timer.update_chart_signal.connect(self.update_trading)
            self.timer.start()
            
        self.trading_status_window.show()
        self.update_trading_status_window()

    def stop_trading(self):
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.is_trade = False

        # Update and close the trading status window
        if self.trading_status_window:
            self.trading_status_window.update_status("Остановлено")  # Исправлено сообщение
        
    def setup_logging(self, log_file='trading_log.txt'):
        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
        logger = logging.getLogger()
        return logger

    def log_message(self, message):
        """Логирует сообщение с временем в 24-часовом формате до секунд."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Формат времени до секунд
        log_entry = f"{timestamp} - {message}"
        logging.info(log_entry)
        self.log_window.add_log_entry(log_entry)  # Добавление строки в окно логов

    def update_trading(self):
        # Функция для загрузки данных и синхронизации с биржей
        symbol = self.symbol_input.currentText()
        interval = self.interval_input.currentText()
        limit = self.limit_input.value()
        run = True
        self.thread = DataDownloadThread(symbol, interval, limit, run)
        self.thread.progress_changed.connect(self.on_progress_changed) 
        self.thread.show_toast.connect(self.show_toast)
        self.thread.data_downloaded.connect(self.on_data_downloaded_run_it)
        self.thread.start() 
        message = datetime.now().strftime("%I:%M:%S %p on %B %d, %Y")
        self.log_message(message)
        self.log_window.update_log(message)
        self.update_trading_status_window()

    def update_trading_status_window(self):
        """Update the trading status window asynchronously."""
        if not hasattr(self, 'status_updater') or not self.status_updater:
            self.status_updater = TradingStatusUpdater(self)
            self.status_updater.update_signal.connect(self._apply_trading_status_update)
            self.status_updater.error_signal.connect(self.handle_updater_error)
        
        if not self.status_updater.isRunning():
            self.status_updater.start()

    def handle_updater_error(self, error_msg):
        """Handle errors from the status updater."""
        self.show_toast(ToastPreset.ERROR, "Ошибка обновления статуса", error_msg)

    def _apply_trading_status_update(self, data):
        """Apply the updates received from the worker thread."""
        self.trading_status_window.update_data(
            is_active=data["is_active"],
            current_pair=data["current_pair"],
            open_positions=data["open_positions"],
            time_to_next_cycle=round(data["time_to_next_cycle"]) if isinstance(data["time_to_next_cycle"], (int, float)) else data["time_to_next_cycle"],
            current_balance=round(data["current_balance"], 3) if isinstance(data["current_balance"], (int, float)) else data["current_balance"],
            floating_pnl=round(data["floating_pnl"], 3) if isinstance(data["floating_pnl"], (int, float)) else data["floating_pnl"],
            used_margin=round(data["used_margin"], 3) if isinstance(data["used_margin"], (int, float)) else data["used_margin"],
            min_margin=round(data["min_margin"], 3) if isinstance(data["min_margin"], (int, float)) else data["min_margin"],
        )

    def load_active_api(self):
        """Загружает активный API из настроек."""
        settings = QSettings("MyApp", "MyCompany")
        active_api_name = settings.value("active_api", None)

        if active_api_name:
            self.active_api = {
                "name": active_api_name,
                "key": settings.value(f"{active_api_name}_key"),
                "secret": settings.value(f"{active_api_name}_secret"),
                "passphrase": settings.value(f"{active_api_name}_passphrase")
            }
        else:
            self.active_api = None

        # Ensure the TradingSyncManager uses the correct API credentials
        if self.active_api:
            self.trading_sync_manager.api = OKXApi(
                api_key=self.active_api["key"],
                api_secret=self.active_api["secret"],
                passphrase=self.active_api["passphrase"]
            )

    def open_api_settings_dialog(self):
        """Открывает диалог настроек API."""
        self.api_manager.open_api_settings_dialog(self)

    def check_api_status(self):
        """Проверяет доступность API."""
        self.api_manager.check_api_status(self)

    def toggle_trading_status_panel(self):
        """Toggle the visibility of the trading status panel."""
        if self.trading_status_window.isVisible():
            self.trading_status_window.hide()
            self.splitter.setSizes([1300, 0])  
        else:
            self.trading_status_window.show()
            self.splitter.setSizes([1050, 250])  

    def closeEvent(self, event):
        """Останавливает все потоки перед закрытием приложения."""
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
            self.timer.wait()
        if hasattr(self, 'price_updater') and self.price_updater:
            self.price_updater.stop_updating()
        if hasattr(self, 'status_updater') and self.status_updater:
            self.status_updater.stop()  # Используем новый метод stop
        super().closeEvent(event)

    def show_detailed_statistics(self):
        """Show detailed statistics window"""
        if not hasattr(self, 'df') or len(self.df) == 0:
            self.show_toast(ToastPreset.ERROR, 'Ошибка', 'Нет данных для анализа')
            return
            
        if not self.positions:
            self.show_toast(ToastPreset.ERROR, 'Ошибка', 'Сначала запустите тестирование стратегии')
            return

        # Calculate statistics
        stats = self.calculate_detailed_statistics()
        
        # Create and show statistics window
        from lib.windows.multitask.statistics_window import StatisticsWindow
        stats_window = StatisticsWindow(stats, self.current_theme)
        stats_window.exec_()

    def calculate_detailed_statistics(self):
        """Calculate detailed statistics from positions and balance data"""
        winning_trades = [p for p in self.positions if p['pnl'] > 0]
        losing_trades = [p for p in self.positions if p['pnl'] <= 0]
        
        # Add positions data for plotting
        positions_data = []
        for pos in self.positions:
            if pos['status'] == 'closed':  # Only include closed positions
                positions_data.append((
                    pos['closeTimestamp'],  # timestamp
                    float(pos['pnl']),      # PnL value
                    float(pos['pnl']) > 0   # is profit boolean
                ))
        
        stats = {
            'total_return': round((float(self.canvas.stats['final'].split()[0]) - float(self.canvas.stats['init'].split()[0])) / float(self.canvas.stats['init'].split()[0]) * 100, 2),
            'profit_factor': round(sum(p['pnl'] for p in winning_trades) / abs(sum(p['pnl'] for p in losing_trades)) if losing_trades else float('inf'), 2),
            'win_rate': float(self.canvas.stats['winrate'].strip('%')),
            'max_drawdown': float(self.canvas.stats['drawdown'].strip('%')),
            'sharpe_ratio': round(self.calculate_sharpe_ratio(), 2),
            'total_trades': len(self.positions),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_win': round(sum(p['pnl'] for p in winning_trades) / len(winning_trades), 2) if winning_trades else 0,
            'avg_loss': round(sum(p['pnl'] for p in losing_trades) / len(losing_trades), 2) if losing_trades else 0,
            'largest_win': round(max((p['pnl'] for p in winning_trades), default=0), 2),
            'largest_loss': round(min((p['pnl'] for p in losing_trades), default=0), 2),
            'start_date': self.df.index[0].strftime('%Y-%m-%d'),
            'end_date': self.df.index[-1].strftime('%Y-%m-%d'),
            'total_days': (self.df.index[-1] - self.df.index[0]).days,
            'avg_holding_time': self.calculate_avg_holding_time(),
            'positions_data': positions_data,
            # Add strategy settings
            'strategy_name': self.strat_input.currentText(),
            'commission': self.commission,
            'initial_balance': self.initial_balance,
            'leverage': self.leverage,
            'position_type': self.position_type,
            'position_size': self.position_size,
            'symbol': self.symbol_input.currentText(),
            'interval': self.interval_input.currentText()
        }
        
        return stats

    def calculate_sharpe_ratio(self):
        """Calculate Sharpe Ratio from positions"""
        if not self.positions:
            return 0
            
        returns = [p['pnl'] for p in self.positions]
        if not returns:
            return 0
            
        mean_return = sum(returns) / len(returns)
        std_dev = (sum((r - mean_return) ** 2 for r in returns) / len(returns)) ** 0.5
        
        return mean_return / std_dev if std_dev != 0 else 0

    def calculate_avg_holding_time(self):
        """Calculate average holding time for positions"""
        if not self.positions:
            return "0h"
            
        total_hours = sum((p['closeTimestamp'] - p['openTimestamp']).total_seconds() / 3600 
                         for p in self.positions if p['status'] == 'closed')
        avg_hours = total_hours / len([p for p in self.positions if p['status'] == 'closed'])
        
        return f"{round(avg_hours, 1)}h"

    def show_optimization_dialog(self):
        """Open parameter optimization in new tab"""
        from lib.windows.parameter_optimization_window import ParameterOptimizationWindow
        optimizer = ParameterOptimizationWindow(self.strategy_manager, parent=self)
        self.add_tab_signal.emit(optimizer, "Оптимизация параметров")






