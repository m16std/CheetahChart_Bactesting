from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
import numpy as np
import sys
from PyQt5.QtWidgets import \
    QGraphicsScene, QGraphicsRectItem, QGraphicsView, QMainWindow, QApplication, QGridLayout, QLabel

# Инициализация приложения
app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(show=True, title="Crypto Trading Chart")

# Настройки цветов для светлой и темной тем
theme_colors = {
    "dark": {"background": "#151924", "text": "#ffffff", "grid": "#555555"},
    "light": {"background": "#f0f0f0", "text": "#000000", "grid": "#cccccc"},
}

theme = "dark"  # Выбор темы

# Настройка стилей
pg.setConfigOption('background', theme_colors[theme]["background"])
pg.setConfigOption('foreground', theme_colors[theme]["text"])

# ----- Свечной график и индикаторы -----
candlestick_plot = pg.PlotWidget(title="Price")
candlestick_plot.showGrid(x=True, y=True, alpha=0.3)
candlestick_plot.addLegend()
# ----- График баланса -----
balance_plot = pg.PlotWidget(title="Balance")
balance_plot.showGrid(x=True, y=True, alpha=0.3)
# ----- Общая ось -----
balance_plot.setXLink(candlestick_plot)

# ----- Курсор с линиями -----
vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
hline = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
candlestick_plot.addItem(vline, ignoreBounds=True)
candlestick_plot.addItem(hline, ignoreBounds=True)
vline_ = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
hline_ = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
balance_plot.addItem(vline_, ignoreBounds=True)
balance_plot.addItem(hline_, ignoreBounds=True)

# ----- Генерация данных свечей -----
def generate_candlestick_data():
    num_points = 200  # Количество свечей
    data = []
    timestamps = np.arange(num_points)
    open_prices = np.random.normal(50, 5, size=num_points)
    close_prices = open_prices + np.random.normal(0, 2, size=num_points)
    high_prices = np.maximum(open_prices, close_prices) + np.random.normal(1, 2, size=num_points)
    low_prices = np.minimum(open_prices, close_prices) - np.random.normal(1, 2, size=num_points)

    for i in range(num_points):
        data.append({
            "time": timestamps[i],
            "open": open_prices[i],
            "close": close_prices[i],
            "high": high_prices[i],
            "low": low_prices[i],
        })
    return data

# Создание свечей
def plot_candlestick(data):
    global candle_items
    candle_items = []
    for candle in data:
        open_price = candle['open']
        close_price = candle['close']
        high_price = candle['high']
        low_price = candle['low']
        candle_item = QGraphicsRectItem(candle["time"], open_price,
                                                 1, abs(open_price - close_price))
        candle_item.setPen(pg.mkPen(color='w', width=0.5))
        candle_item.setBrush(pg.mkBrush(color = '#089981' if close_price >= open_price else '#F23645'))
        candlestick_plot.addItem(candle_item)
        
        shadow_item = QGraphicsRectItem(candle["time"], low_price,
                                                 0.2, abs(high_price - low_price))
        shadow_item.setPen(pg.mkPen(color='w', width=0.1))
        shadow_item.setBrush(pg.mkBrush(color = '#089981' if close_price >= open_price else '#F23645'))
        candlestick_plot.addItem(shadow_item)

# Добавление данных свечей
candlestick_data = generate_candlestick_data()
plot_candlestick(candlestick_data)

# ----- Индикаторы на графике -----
indicator_data = np.random.normal(50, 5, size=len(candlestick_data))
indicator_plot = candlestick_plot.plot(indicator_data, pen=pg.mkPen("red", width=1), name="Indicator")

# Создаем область статистики с шестью колонками
stats_layout = QGridLayout()

# Статичная информация в первых пяти колонках
stat_texts = [
    "Stat 1: 100",
    "Stat 2: 200",
    "Stat 3: 300",
    "Stat 4: 400",
    "Stat 5: 500"
]

for i, text in enumerate(stat_texts):
    label = QLabel(text)
    label.setAlignment(QtCore.Qt.AlignCenter)
    label.setStyleSheet("color: white;")
    stats_layout.addWidget(label, 0, i)

# Шестая колонка для динамической информации
dynamic_label = QLabel("Date: N/A | Price: N/A")
dynamic_label.setAlignment(QtCore.Qt.AlignCenter)
dynamic_label.setStyleSheet("color: white;")
stats_layout.addWidget(dynamic_label, 0, 5)




balance_data = np.cumsum(np.random.normal(0, 1, size=1000))
cm = pg.ColorMap([0.0, 1.0], ['#089981', '#F23645'])
pen = cm.getPen( span=(0.05,-0.05), width=2 )
level = (0 - balance_data.min())/(balance_data.max() - balance_data.min())
grad = QtGui.QLinearGradient(0, balance_data.min(), 0, balance_data.max())
grad.setColorAt(0.0, pg.mkColor('#F23645'))
grad.setColorAt(level, pg.mkColor('#151924'))
grad.setColorAt(1, pg.mkColor('#089981'))
brush = QtGui.QBrush(grad)

balance_plot.plot(balance_data, fillLevel=0, brush=brush, pen=pen, name="Balance")


def mouse_moved_candel(evt):
    pos = evt  # position of the mouse

    mouse_point = candlestick_plot.plotItem.vb.mapSceneToView(pos)
    vline.setPos(mouse_point.x())
    vline_.setPos(mouse_point.x())
    hline.setPos(mouse_point.y())

    # Обновление плашек с ценой и временем
    time_text = f"Date: {int(mouse_point.x())}"
    price_text = f"Price: {mouse_point.y():.2f}"
    dynamic_label.setText(f"{time_text} | {price_text}")

def mouse_moved_balance(evt):        
    pos = evt[0]  # position of the mouse

    mouse_point = balance_plot.plotItem.vb.mapSceneToView(pos)
    vline_.setPos(mouse_point.x())
    vline.setPos(mouse_point.x())
    hline_.setPos(mouse_point.y())

    # Обновление плашек с ценой и временем
    time_text = f"Date: {int(mouse_point.x())}"
    price_text = f"Price: {mouse_point.y():.2f}"
    dynamic_label.setText(f"{time_text} | {price_text}")


candlestick_plot.scene().sigMouseMoved.connect(mouse_moved_candel)



l = QtWidgets.QVBoxLayout()
l.addWidget(candlestick_plot, stretch=3)
l.addLayout(stats_layout)
l.addWidget(balance_plot, stretch=1)

w = QtWidgets.QWidget()
w.setLayout(l)

layout = QtWidgets.QVBoxLayout(win)
layout.addWidget(w)

w.show()

app.exec_()