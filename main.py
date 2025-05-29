import os
import sys

from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QMenuBar, QFileDialog, QAction, QDesktopWidget
import qdarktheme
from lib.crypto_trading_app import CryptoTradingApp
from lib.widgets.tab_manager import TabManager
from lib.windows.python_editor_window import PythonEditorWindow
from lib.widgets.split_view import SplitView
import pyqtgraph as pg
from os import environ

def main():
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark") 
    app.setApplicationName("CheetahChart Backtesting")  # имя приложения
    app.setOrganizationName("CheetahChart")   # имя организации

    def create_new_tab():
        return CryptoTradingApp()

    # Initialize TabManager
    tab_manager = TabManager(create_tab_callback=create_new_tab)
    
    # Подключаем сигналы для всех вкладок
    def handle_add_tab(widget, title):
        tab_manager.add_new_tab(widget, title)

    tab_manager.add_tab_signal.connect(handle_add_tab)

    # Connect the add_tab_signal of the first tab
    initial_tab = tab_manager.widget(0)
    if isinstance(initial_tab, CryptoTradingApp):
        initial_tab.add_tab_signal.connect(handle_add_tab)

    main_window = QWidget()
    main_window.setWindowTitle("CheetahChart Backtesting")
    main_layout = QVBoxLayout(main_window)
    main_layout.setContentsMargins(0, 0, 0, 0) 

    # Создаем корневой сплиттер
    root_splitter = SplitView(main_window)  # Указываем родителя
    root_splitter.setObjectName("root_splitter")  # Устанавливаем имя для поиска
    root_splitter.addWidget(tab_manager)
    
    main_layout.addWidget(root_splitter)
    main_menubar = QMenuBar()
    main_layout.setMenuBar(main_menubar)

    def update_main_menubar(new_menubar):
        main_layout.setMenuBar(new_menubar)

    tab_manager.menubar_changed.connect(update_main_menubar)

    # Center window on screen
    screen = QDesktopWidget().screenGeometry()
    main_window.resize(1300, 752)  # Set initial size
    size = main_window.frameSize()
    x = (screen.width() - size.width()) // 2
    y = (screen.height() - size.height()) // 2
    main_window.move(x, y)

    main_window.show()
    app.exec_()

def suppress_qt_warnings():
    environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    environ["QT_SCALE_FACTOR"] = "1"

if __name__ == '__main__':
    suppress_qt_warnings()
    main()


