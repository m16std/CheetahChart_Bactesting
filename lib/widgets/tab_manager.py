from PyQt5.QtWidgets import (QTabWidget, QPushButton, QVBoxLayout, QMenu, 
                           QAction, QWidget, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QByteArray, QPoint, QMimeData
from PyQt5.QtGui import QPixmap, QDrag, QRegion

from lib.crypto_trading_app import CryptoTradingApp
from lib.windows.tab_selector_window import TabSelectorWindow
from lib.windows.python_editor_window import PythonEditorWindow
from lib.windows.visual_strategy_editor import VisualStrategyEditor
from lib.windows.parameter_optimization_window import ParameterOptimizationWindow
from .split_view import SplitView

class TabManager(QTabWidget):
    menubar_changed = pyqtSignal(object)  # Сигнал для изменения menubar
    theme_changed = pyqtSignal(str)  # Signal to propagate theme changes
    add_tab_signal = pyqtSignal(object, object)  # Добавляем новый сигнал
    editors_requested = pyqtSignal(list)  # Новый сигнал

    def __init__(self, create_tab_callback, parent=None):
        """
        :param create_tab_callback: Функция обратного вызова для создания новой вкладки.
        """
        super().__init__(parent)
        self.current_theme = "dark"  # Default theme
        self.create_tab_callback = create_tab_callback
        self.setTabsClosable(True)
        self.tabBar().setMovable(True)
        self.tabBar().setTabsClosable(True)
        self.tabBar().tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.update_menubar) 
        self.theme_changed.connect(self.apply_theme_to_all_tabs)  # Connect signal to method
        self.add_tab_signal.connect(self.add_new_tab)  # Подключаем сигнал к методу

        # Включаем перетаскивание вкладок
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setAcceptDrops(True)
        self.tabBar().installEventFilter(self)  # Устанавливаем фильтр событий

        # Добавляем отслеживание последней активной trading вкладки
        self.last_active_trading_tab = None

        # Create the first tab to determine the initial theme
        initial_tab = self.create_tab_callback()
        if isinstance(initial_tab, CryptoTradingApp):
            self.current_theme = initial_tab.load_theme()  # Store the initial theme
            self.apply_theme(self.current_theme)
            initial_tab.theme_changed_signal.connect(self.handle_theme_change)

        # Add the first tab
        self.add_new_tab(initial_tab)

        # Кнопка для добавления новой вкладки
        self.new_tab_button = QPushButton("+")
        self.new_tab_button.setFixedSize(27, 27)
        self.new_tab_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
            }
        """)
        self.new_tab_button.clicked.connect(self.add_new_tab)
        self.setCornerWidget(self.new_tab_button, Qt.TopRightCorner)

        self.setTabContextMenuPolicy()
        self.main_splitter = SplitView(self)

    def setTabContextMenuPolicy(self):
        """Настраивает контекстное меню для вкладок"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_tab_context_menu)

    def show_tab_context_menu(self, position):
        """Показывает контекстное меню для вкладки"""
        tab_bar = self.tabBar()
        tab_index = tab_bar.tabAt(position)
        if tab_index == -1:
            return

        menu = QMenu()
        split_right = menu.addAction("Разделить справа")
        split_bottom = menu.addAction("Разделить снизу")
        
        # Добавляем опцию обмена вкладками, если есть разделение
        if isinstance(self.parent(), SplitView):
            menu.addSeparator()
            swap_tabs = menu.addAction("Поменять местами с другим окном")
            
        action = menu.exec_(self.mapToGlobal(position))
        if action == split_right:
            self.split_tab(tab_index, Qt.Horizontal)
        elif action == split_bottom:
            self.split_tab(tab_index, Qt.Vertical)
        elif action == swap_tabs:
            self.swap_tabs_with_other()

    def swap_tabs_with_other(self):
        """Меняет местами все вкладки с другим TabManager в сплиттере."""
        if not isinstance(self.parent(), SplitView):
            return
            
        splitter = self.parent()
        # Находим другой TabManager в том же сплиттере
        other_tab_manager = None
        for i in range(splitter.count()):
            widget = splitter.widget(i)
            if isinstance(widget, TabManager) and widget != self:
                other_tab_manager = widget
                break
                
        if other_tab_manager:
            # Сохраняем вкладки
            our_tabs = []
            other_tabs = []
            
            # Сохраняем наши вкладки
            while self.count() > 0:
                widget = self.widget(0)
                title = self.tabText(0)
                self.removeTab(0)
                our_tabs.append((widget, title))
                
            # Сохраняем вкладки другого менеджера
            while other_tab_manager.count() > 0:
                widget = other_tab_manager.widget(0)
                title = other_tab_manager.tabText(0)
                other_tab_manager.removeTab(0)
                other_tabs.append((widget, title))
                
            # Меняем местами
            for widget, title in other_tabs:
                self.add_new_tab(widget, title)
                
            for widget, title in our_tabs:
                other_tab_manager.add_new_tab(widget, title)

    def split_tab(self, tab_index, orientation):
        """Разделяет область и перемещает вкладку"""
        widget = self.widget(tab_index)
        if not widget:
            return
            
        title = self.tabText(tab_index)
        
        def create_split():
            # Создаем новый TabManager для разделенной области с пустой вкладкой
            new_tab_manager = TabManager(self.create_tab_callback)
            # Подключаем сигнал изменения темы к новому TabManager
            self.theme_changed.connect(new_tab_manager.apply_theme_to_all_tabs)
            
            selector = TabSelectorWindow()
            selector.tab_selected.connect(new_tab_manager.handle_tab_selection)
            new_tab_manager.removeTab(0)
            new_tab_manager.addTab(selector, "Новая вкладка")
            
            # Применяем текущую тему к новому TabManager
            new_tab_manager.apply_theme(self.current_theme)

            # Добавляем в сплиттер (текущий виджет слева, новый справа)
            if not isinstance(self.parent(), SplitView):
                splitter = SplitView()
                splitter.setOrientation(orientation)
                root_splitter = self.window().findChild(QWidget, "root_splitter")
                if root_splitter and isinstance(root_splitter, SplitView):
                    index = root_splitter.indexOf(self)
                    if index >= 0:
                        root_splitter.insertWidget(index, splitter)
                        splitter.addWidget(self)
                        splitter.addWidget(new_tab_manager)
            else:
                self.parent().split(self, new_tab_manager, orientation)

        QTimer.singleShot(0, create_split)
        
    def add_new_tab(self, widget=None, title=None):
        """Добавляет новую вкладку с использованием функции обратного вызова или переданного виджета."""
        if widget is None or widget is False:
            # Создаем окно выбора типа вкладки
            selector = TabSelectorWindow()
            selector.tab_selected.connect(self.handle_tab_selection)
            index = self.addTab(selector, "Новая вкладка")
            self.setCurrentIndex(index)
        else:
            if isinstance(widget, TabManager):
                # Если добавляем TabManager, встраиваем его в сплиттер
                self.main_splitter.addWidget(widget)
            else:
                # Обычное добавление вкладки
                index = self.addTab(widget, title or f"Вкладка {self.count() + 1}")
                self.setCurrentIndex(index)
                if isinstance(widget, CryptoTradingApp):
                    self.setTabText(self.indexOf(widget), widget.strat_input.currentText())
                    widget.update_tab_title_signal.connect(
                        lambda new_title, tab=widget: 
                        self.setTabText(self.indexOf(tab), new_title)
                    )
                    widget.theme_changed_signal.connect(self.apply_theme_to_all_tabs)

    def handle_tab_selection(self, tab_type):
        if self.count() > 0:
            current_index = self.currentIndex()
            current_widget = self.widget(current_index)
            if isinstance(current_widget, TabSelectorWindow):
                self.removeTab(current_index)

        if tab_type == "strategy":
            new_tab = self.create_tab_callback()
            self.add_new_tab(new_tab)
            if isinstance(new_tab, CryptoTradingApp):
                new_tab.add_tab_signal.connect(lambda w, t: self.add_new_tab(w, t))
                new_tab.load_external_strategies()
            return new_tab
        elif tab_type == "optimization":
            # Получаем существующий trading tab для использования его strategy_manager
            trading_tab = self.get_trading_tab()
            if trading_tab:
                from lib.windows.parameter_optimization_window import ParameterOptimizationWindow
                optimizer = ParameterOptimizationWindow(trading_tab.strategy_manager, parent=trading_tab, theme=self.widget(0).current_theme)
                self.add_new_tab(optimizer, "Оптимизация параметров")
            else:
                self.show_toast('error', "Ошибка", "Сначала создайте вкладку тестирования")
        elif tab_type == "code":
            editor = PythonEditorWindow("", theme=self.widget(0).current_theme)
            self.add_new_tab(editor, "Новый скрипт")
        elif tab_type == "visual":
            visual_editor = VisualStrategyEditor(theme=self.widget(0).current_theme)
            self.add_new_tab(visual_editor, "Конструктор стратегий")
        
        return None

    def get_trading_tab(self):
        """Получает первую найденную вкладку CryptoTradingApp"""
        for i in range(self.count()):
            widget = self.widget(i)
            if isinstance(widget, CryptoTradingApp):
                return widget
        return None

    def close_tab(self, index):
        """Закрывает вкладку."""
        if self.count() <= 1:
            # Если это последняя вкладка в TabManager и есть сплиттер
            if isinstance(self.parent(), SplitView):
                # Удаляем этот TabManager из сплиттера
                splitter = self.parent()
                self.deleteLater()
                
                # Если в сплиттере остался один виджет, заменяем сплиттер на этот виджет
                if splitter.count() == 1:
                    remaining_widget = splitter.widget(0)
                    if splitter.parent() and splitter.parent().layout():
                        layout = splitter.parent().layout()
                        layout.replaceWidget(splitter, remaining_widget)
                        splitter.deleteLater()
            else:
                # Если это последняя вкладка и нет разделения, закрываем приложение
                self.parent().close()
        else:
            # Просто закрываем вкладку
            widget = self.widget(index)
            if widget:
                self.removeTab(index)
                widget.deleteLater()

    def update_menubar(self, index):
        """Обновляет menubar в зависимости от активной вкладки."""
        current_widget = self.widget(index)
        
        # Если текущий виджет - CryptoTradingApp, обновляем последнюю активную вкладку
        if isinstance(current_widget, CryptoTradingApp):
            self.last_active_trading_tab = current_widget
            self.menubar_changed.emit(current_widget.menubar)
        # Если текущий виджет не CryptoTradingApp, используем последнюю активную trading вкладку
        elif self.last_active_trading_tab and hasattr(self.last_active_trading_tab, "menubar"):
            self.menubar_changed.emit(self.last_active_trading_tab.menubar)
        # Если нет активной trading вкладки, используем menubar текущего виджета если он есть
        elif hasattr(current_widget, "menubar"):
            self.menubar_changed.emit(current_widget.menubar)

    def apply_theme(self, theme):
        if theme == "dark":
            self.setStyleSheet("""
                QTabWidget::tab-bar {
                    left: 0;
                }
                QTabBar::tab {
                    background: #151924;
                    margin: 0;
                    padding: 5px 10px;
                    border: 0;
                }
                QTabBar::tab:selected {
                    background: #3d3d3d;
                }
                QTabBar::tab:hover {
                    background: #4d4d4d;
                }
                QTabWidget {
                    background-color: #151924;
                }
            """)
        else:  
            self.setStyleSheet("""
                QTabWidget::tab-bar {
                    left: 0;
                }
                QTabBar::tab {
                    background: #e0e0e0;
                    margin: 0;
                    padding: 5px 10px;
                    border: 0;
                }
                QTabBar::tab:selected {
                    background: #fafafa;
                }
                QTabBar::tab:hover {
                    background: #c0c0c0;
                }
            """)

    def handle_theme_change(self, theme):
        """Handle theme changes and propagate them."""
        self.current_theme = theme
        self.apply_theme_to_all_tabs(theme)
        self.theme_changed.emit(theme)

    def apply_theme_to_all_tabs(self, theme):
        """Apply the theme to all tabs and TabManager."""
        self.current_theme = theme  # Update current theme
        self.apply_theme(theme)
        for index in range(self.count()):
            widget = self.widget(index)
            if hasattr(widget, "apply_theme"):
                widget.apply_theme(theme)

    def get_trading_editors(self):
        """Возвращает список всех открытых CryptoTradingApp."""
        editors = []
        for i in range(self.count()):
            widget = self.widget(i)
            if isinstance(widget, CryptoTradingApp):
                editors.append(widget)
        return editors

    def emit_editors_list(self):
        """Отправляет список редакторов через сигнал."""
        editors = self.get_trading_editors()
        self.editors_requested.emit(editors)
