import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout, QFrame, QSizePolicy, QMenu, QAction, QToolButton, QStackedWidget, QTextEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

from lib.crypto_trading_app import QPainter, QPixmap, QSvgRenderer
from lib.api.api_manager import APIManager
from lib.windows.multitask.statistics_window import StatisticsWindow
from lib.windows.multitask.strategy_settings_window import StrategySettingsWindow

class MultitaskWindow(QWidget):
    start_trading_signal = pyqtSignal()
    stop_trading_signal = pyqtSignal()
    toggle_log_signal = pyqtSignal()  

    def __init__(self, theme="dark", parent=None):
        super().__init__(parent)
        self.api_manager = APIManager() 
        self.current_theme = theme
        self.strategy = None  
        self.setWindowTitle("Статус торговли")
        self.setMinimumWidth(300)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) 
        self.layout.setSpacing(0) 

        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(2, 2, 2, 2)
        self.header_layout.setSpacing(5)

        view_buttons_container = QWidget()
        self.view_buttons_layout = QHBoxLayout(view_buttons_container)
        self.view_buttons_layout.setSpacing(0)
        self.view_buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.trade_button = QPushButton("ТОРГОВЛЯ")
        self.stats_button = QPushButton("СТАТИСТИКА")
        self.settings_button = QPushButton("НАСТРОЙКИ")
        self.logs_button = QPushButton("ЛОГИ")

        button_style = """
            QPushButton {
                border: none;
                padding: 5px 0px;
                font-size: 10pt;
                margin: 0px;
                background-color: transparent;
                width: 100%;
            }
            QPushButton[active="true"] {
                border: 2px solid #669FD3;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """

        for btn in [self.trade_button, self.stats_button, self.settings_button, self.logs_button]:
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(1, 0, 1, 0)
            container_layout.setSpacing(0)
            
            btn.setStyleSheet(button_style)
            container_layout.addWidget(btn)
            self.view_buttons_layout.addWidget(container, 1)  # Добавляем с весом 1

        self.header_layout.addWidget(view_buttons_container, 1)  # Расширяем на всю доступную ширину
        self.header_layout.addStretch(0)  # Убираем растяжение после кнопок

        self.trade_button.setProperty("active", True)
        self.stats_button.setProperty("active", False)
        self.settings_button.setProperty("active", False)
        self.logs_button.setProperty("active", False)
        
        self.trade_button.clicked.connect(lambda: self.switch_view("trade"))
        self.stats_button.clicked.connect(lambda: self.switch_view("stats"))
        self.settings_button.clicked.connect(lambda: self.switch_view("settings"))
        self.logs_button.clicked.connect(lambda: self.switch_view("logs"))

        # Кнопка меню
        self.menu_button = QToolButton()
        self.menu_button.setFixedSize(15, 15)
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu_button.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 0;
            }
            QToolButton::menu-indicator {
                width: 0px;
                height: 0px;
            }
        """) 
        self.menu_button.setMenu(self.create_menu())
        #self.header_layout.addWidget(self.menu_button)

        # Кнопка закрытия
        self.close_button = QToolButton()
        self.close_button.setFixedSize(15, 15)
        self.close_button.setStyleSheet("""
            border: none;
            padding: 0;
        """)  
        self.close_button.clicked.connect(self.close)
        #self.header_layout.addWidget(self.close_button)

        self.layout.addLayout(self.header_layout)

        self.header_line = QFrame()
        self.header_line.setFrameShape(QFrame.HLine)
        self.header_line.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(self.header_line)

        # Установка иконок
        self.update_close_button_icon(Qt.black)

        # Create stacked widget for views
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Create and add trading view
        self.trading_view = QWidget()
        self.trading_layout = QVBoxLayout(self.trading_view)
        self.trading_layout.setContentsMargins(0, 0, 0, 0) 
        self.init_trading_view()
        self.stacked_widget.addWidget(self.trading_view)

        # Create and add statistics view
        self.stats_view = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_view)
        self.stats_layout.setContentsMargins(0, 0, 0, 0) 
        self.init_stats_view()
        self.stacked_widget.addWidget(self.stats_view)

        # Create and add settings view
        self.settings_view = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_view)
        self.settings_layout.setContentsMargins(0, 0, 0, 0) 
        self.init_settings_view()
        self.stacked_widget.addWidget(self.settings_view)

        # Create and add logs view
        self.logs_view = QWidget()
        self.logs_layout = QVBoxLayout(self.logs_view)
        self.logs_layout.setContentsMargins(0, 0, 0, 0) 
        self.init_logs_view()
        self.stacked_widget.addWidget(self.logs_view)

        # Set initial view
        self.stacked_widget.setCurrentIndex(0)
        self.apply_theme(self.current_theme)  # Apply theme after UI initialization

    def init_trading_view(self):
        """Initialize trading view widgets"""
        # Статус торговли
        self.status_layout = QHBoxLayout()
        self.status_label = QLabel("Статус:")
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_value = QLabel("Ожидание")
        self.status_value.setAlignment(Qt.AlignRight)
        self.status_layout.addWidget(self.status_label)
        self.status_layout.addWidget(self.status_value)
        self.trading_layout.addLayout(self.status_layout)

        # Текущая пара
        self.pair_layout = QHBoxLayout()
        self.pair_label = QLabel("Текущая пара:")
        self.pair_label.setAlignment(Qt.AlignLeft)
        self.pair_value = QLabel("N/A")
        self.pair_value.setAlignment(Qt.AlignRight)
        self.pair_layout.addWidget(self.pair_label)
        self.pair_layout.addWidget(self.pair_value)
        self.trading_layout.addLayout(self.pair_layout)

        # Время до следующего цикла
        self.time_layout = QHBoxLayout()
        self.time_label = QLabel("Время до следующего цикла:")
        self.time_label.setAlignment(Qt.AlignLeft)
        self.time_value = QLabel("N/A")
        self.time_value.setAlignment(Qt.AlignRight)
        self.time_layout.addWidget(self.time_label)
        self.time_layout.addWidget(self.time_value)
        self.trading_layout.addLayout(self.time_layout)

        # Баланс
        self.current_balance_layout = QHBoxLayout()
        self.current_balance_label = QLabel("Текущий баланс:")
        self.current_balance_label.setAlignment(Qt.AlignLeft)
        self.current_balance_value = QLabel("0 USDT")
        self.current_balance_value.setAlignment(Qt.AlignRight)
        self.current_balance_layout.addWidget(self.current_balance_label)
        self.current_balance_layout.addWidget(self.current_balance_value)
        self.trading_layout.addLayout(self.current_balance_layout)

        # Плавающие прибыль и убытки
        self.pnl_layout = QHBoxLayout()
        self.pnl_label = QLabel("Плавающие PnL:")
        self.pnl_label.setAlignment(Qt.AlignLeft)
        self.pnl_value = QLabel("0 USDT")
        self.pnl_value.setAlignment(Qt.AlignRight)
        self.pnl_layout.addWidget(self.pnl_label)
        self.pnl_layout.addWidget(self.pnl_value)
        self.trading_layout.addLayout(self.pnl_layout)

        # Используется
        self.used_margin_layout = QHBoxLayout()
        self.used_margin_label = QLabel("Используется:")
        self.used_margin_label.setAlignment(Qt.AlignLeft)
        self.used_margin_value = QLabel("0 USDT")
        self.used_margin_value.setAlignment(Qt.AlignRight)
        self.used_margin_layout.addWidget(self.used_margin_label)
        self.used_margin_layout.addWidget(self.used_margin_value)
        self.trading_layout.addLayout(self.used_margin_layout)

        # Минимальная маржа
        self.min_margin_layout = QHBoxLayout()
        self.min_margin_label = QLabel("Минимальная маржа:")
        self.min_margin_label.setAlignment(Qt.AlignLeft)
        self.min_margin_value = QLabel("0 USDT")
        self.min_margin_value.setAlignment(Qt.AlignRight)
        self.min_margin_layout.addWidget(self.min_margin_label)
        self.min_margin_layout.addWidget(self.min_margin_value)
        self.trading_layout.addLayout(self.min_margin_layout)

        # Таблица позиций
        self.positions_table = QTableWidget(0, 5)
        self.positions_table.setHorizontalHeaderLabels(["ID", "Сторона", "Открытие", "Закрытие", "PnL"])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trading_layout.addWidget(self.positions_table)

        # Кнопки управления
        self.buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Запустить торговлю")
        self.start_button.clicked.connect(self.start_trading_signal.emit)
        self.start_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.stop_button = QPushButton("Остановить торговлю")
        self.stop_button.clicked.connect(self.stop_trading_signal.emit)
        self.stop_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.buttons_layout.addWidget(self.start_button)
        self.buttons_layout.addWidget(self.stop_button)
        self.trading_layout.addLayout(self.buttons_layout)

        self.stop_button.setEnabled(False)

    def init_stats_view(self):
        """Initialize statistics view widgets"""
        from lib.windows.multitask.statistics_window import StatisticsWindow
        # Create default stats with zeros
        default_stats = {
            'total_return': 0,
            'profit_factor': 0,
            'win_rate': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'start_date': '-',
            'end_date': '-',
            'total_days': 0,
            'avg_holding_time': '0h'
        }
        # Передаем текущую тему при создании окна статистики
        self.stats_content = StatisticsWindow(default_stats, theme=self.current_theme, parent=self)
        self.stats_layout.addWidget(self.stats_content)

    def init_settings_view(self):
        """Initialize settings view"""
        from lib.windows.multitask.strategy_settings_window import StrategySettingsWindow
        if self.strategy:
            self.settings_content = StrategySettingsWindow(self.strategy, theme=self.current_theme, parent=self)
        else:
            # Create empty placeholder widget if no strategy is set
            self.settings_content = QWidget()
            layout = QVBoxLayout(self.settings_content)
            label = QLabel("No strategy selected")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
        self.settings_layout.addWidget(self.settings_content)

    def init_logs_view(self):
        """Initialize logs view"""
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)
        self.logs_layout.addWidget(self.log_text_edit)
        self.load_logs()

    def load_logs(self, log_file='trading_log.txt'):
        """Load logs from file"""
        try:
            with open(log_file, 'r') as file:
                self.log_text_edit.setText(file.read())
            self.scroll_to_bottom()
        except Exception as e:
            self.log_text_edit.setText(f"Ошибка загрузки логов: {e}")

    def scroll_to_bottom(self):
        """Scroll logs to bottom"""
        self.log_text_edit.moveCursor(self.log_text_edit.textCursor().End)

    def switch_view(self, view_type):
        """Switch between views"""
        views = {
            "trade": (0, self.trade_button), 
            "stats": (1, self.stats_button),
            "settings": (2, self.settings_button),  # Add settings view
            "logs": (3, self.logs_button)
        }
        
        # Reset all buttons
        for button in [self.trade_button, self.stats_button, self.settings_button, self.logs_button]:
            button.setProperty("active", False)
            
        # Activate selected view
        if view_type in views:
            index, button = views[view_type]
            self.stacked_widget.setCurrentIndex(index)
            button.setProperty("active", True)
            
            # If switching to logs, reload them
            if view_type == "logs":
                self.load_logs()
            elif view_type == "settings":
                self.load_strategy_settings()

        # Force style update
        for button in [self.trade_button, self.stats_button, self.settings_button, self.logs_button]:
            button.style().unpolish(button)
            button.style().polish(button)

    def load_strategy_settings(self):
        """Reload strategy settings view"""
        if not self.strategy:
            return
            
        # Remove old settings widget if exists
        if hasattr(self, 'settings_content'):
            self.settings_content.setParent(None)
            
        # Create new settings widget with current strategy
        self.settings_content = StrategySettingsWindow(self.strategy, theme=self.current_theme, parent=self)
        self.settings_layout.addWidget(self.settings_content)

    def load_strategy_settings(self):
        """Reload strategy settings view"""
        if not self.strategy:
            return
            
        # Remove old settings widget if exists
        if hasattr(self, 'settings_content'):
            self.settings_content.setParent(None)
            
        # Create new settings widget
        self.settings_content = StrategySettingsWindow(self.strategy, theme=self.current_theme, parent=self)
        # Connect parameters changed signal
        self.settings_content.parameters_changed.connect(self.on_strategy_parameters_changed)
        self.settings_layout.addWidget(self.settings_content)

    def on_strategy_parameters_changed(self):
        """Handle strategy parameter changes"""
        # Trigger strategy rerun if we have data loaded
        if hasattr(self, 'parent') and hasattr(self.parent, 'run_strategy'):
            self.parent.run_strategy()

    def update_strategy(self, strategy):
        """Update the current strategy and refresh settings view"""
        self.strategy = strategy
        # Always reload settings view since we want to show parameters 
        # for the newly selected strategy
        self.load_strategy_settings()

    def update_statistics(self, stats_data):
        """Update statistics view with new data"""
        # Удаляем старый виджет
        for i in reversed(range(self.stats_layout.count())): 
            self.stats_layout.itemAt(i).widget().setParent(None)
        
        # Создаем новый с текущей темой
        self.stats_content = StatisticsWindow(stats_data, theme=self.current_theme, parent=self)
        self.stats_layout.addWidget(self.stats_content)

    def apply_theme(self, theme):
        """Apply theme to components"""
        self.current_theme = theme
        # Обновляем тему в окне статистики если оно существует
        if hasattr(self, 'stats_content') and self.stats_content:
            self.stats_content = StatisticsWindow(self.stats_content.stats_data, theme=theme, parent=self)
            # Удаляем старый виджет и добавляем новый
            for i in reversed(range(self.stats_layout.count())): 
                self.stats_layout.itemAt(i).widget().setParent(None)
            self.stats_layout.addWidget(self.stats_content)
        # Обновляем цвет иконок в зависимости от темы
        icon_color = Qt.white if theme == "dark" else Qt.black
        self.update_close_button_icon(icon_color)

    def create_menu(self):
        """Создает QMenu для кнопки с троеточием."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                border: 1px solid gray;  
                border-radius: 5px;     
                padding: 5px;
            }
        """)  # Добавлен стиль для QMenu

        # Кнопка "Окно логов"
        toggle_log_action = QAction("Окно логов", self)
        toggle_log_action.triggered.connect(self.toggle_log)
        menu.addAction(toggle_log_action)

        # Кнопка "Настроить API"
        set_api_action = QAction("Настроить API", self)
        set_api_action.triggered.connect(lambda: self.api_manager.open_api_settings_dialog(self))
        menu.addAction(set_api_action)

        # Кнопка "Проверить API"
        check_api_action = QAction("Проверить API", self)
        check_api_action.triggered.connect(lambda: self.api_manager.check_api_status(self))
        menu.addAction(check_api_action)

        return menu

    def toggle_log(self):
        """Изменяет текст кнопки в зависимости от состояния окна логов."""
        self.toggle_log_signal.emit()

    def update_data(self, is_active, current_pair, open_positions, time_to_next_cycle, current_balance, floating_pnl, used_margin, min_margin):
        self.status_value.setText("Активно" if is_active else "Остановлено")
        self.pair_value.setText(current_pair if current_pair else "N/A")
        self.time_value.setText(f"{time_to_next_cycle} сек" if time_to_next_cycle != "N/A" else "N/A")
        self.current_balance_value.setText(f"{current_balance} USDT")
        self.pnl_value.setText(f"{floating_pnl} USDT")
        self.used_margin_value.setText(f"{used_margin} USDT")
        self.min_margin_value.setText(f"{min_margin} USDT")

        # Принудительное обновление интерфейса
        self.status_value.repaint()
        self.pair_value.repaint()
        self.time_value.repaint()
        self.current_balance_value.repaint()
        self.pnl_value.repaint()
        self.used_margin_value.repaint()
        self.min_margin_value.repaint()

        self.positions_table.setRowCount(len(open_positions) if open_positions else 0)
        if open_positions:
            for row, position in enumerate(open_positions):
                self.positions_table.setItem(row, 0, QTableWidgetItem(str(position.get('posId', 'N/A'))))

                # Цвет текста для направления сделки
                pos_side_item = QTableWidgetItem(position.get('posSide', 'N/A'))
                if position.get('posSide', '').lower() == 'long':
                    pos_side_item.setForeground(QColor('#089981'))  # Зеленый
                elif position.get('posSide', '').lower() == 'short':
                    pos_side_item.setForeground(QColor('#F23645'))  # Красный
                self.positions_table.setItem(row, 1, pos_side_item)

                self.positions_table.setItem(row, 2, QTableWidgetItem(str(position.get('openPrice', 'N/A'))))
                self.positions_table.setItem(row, 3, QTableWidgetItem(str(position.get('closePrice', 'N/A'))))

                # Цвет текста для PnL с округлением до 3 знаков
                pnl_value = round(position.get('pnl', 0), 3)
                pnl_item = QTableWidgetItem(str(pnl_value))
                if pnl_value > 0:
                    pnl_item.setForeground(QColor('#089981'))  # Зеленый
                elif pnl_value < 0:
                    pnl_item.setForeground(QColor('#F23645'))  # Красный
                self.positions_table.setItem(row, 4, pnl_item)

        self.positions_table.repaint()

        # Обновление состояния кнопок
        self.start_button.setEnabled(not is_active)
        self.stop_button.setEnabled(is_active)

    def update_status(self, status_message):
        """Обновляет текст статуса торговли."""
        self.status_value.setText(status_message)

    def update_close_button_icon(self, icon_color):
        """Обновляет иконки кнопок меню и закрытия."""
        # Иконка для кнопки закрытия
        close_icon = self.recolor_svg_icon("resources/close.svg", icon_color)
        self.close_button.setIcon(close_icon)

        # Иконка для кнопки меню (троеточие)
        menu_icon = self.recolor_svg_icon("resources/menu.svg", icon_color)
        self.menu_button.setIcon(menu_icon)

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

