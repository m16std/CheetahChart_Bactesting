import sys
from PyQt5.QtWidgets import  QApplication # type: ignore
import qdarktheme # type: ignore
from lib.crypto_trading_app import CryptoTradingApp
from os import environ

def main():
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")  # Начальная тема
    ex = CryptoTradingApp()
    ex.show()
    sys.exit(app.exec_())

def suppress_qt_warnings():
    environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    environ["QT_SCALE_FACTOR"] = "1"

if __name__ == '__main__':
    suppress_qt_warnings()
    main()
