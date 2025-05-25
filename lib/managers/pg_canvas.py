from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
from pyqtgraph import TextItem, PlotDataItem, mkPen, mkBrush
from PyQt5.QtWidgets import (QGraphicsRectItem, QGridLayout, QLabel, QWidget, 
                           QFrame, QToolBar, QAction, QInputDialog, QColorDialog,
                           QToolButton, QMenu)
from datetime import datetime as dt
from PyQt5.QtGui import QFont, QColor, QLinearGradient, QBrush
from PyQt5.QtCore import QMargins
import math

class PGCanvas(QWidget):

    def __init__(self, facecolor, textcolor):
        self.price_date_axis = pg.DateAxisItem(orientation='bottom')
        self.balance_date_axis = pg.DateAxisItem(orientation='bottom')

        # ----- Свечной график и индикаторы -----
        self.candlestick_plot = pg.PlotWidget()
        self.candlestick_plot.setAxisItems({'bottom': self.price_date_axis})
        self.candlestick_plot.showGrid(x=True, y=True, alpha=0.3)
        self.candlestick_plot.addLegend()
        # ----- График баланса -----
        self.balance_plot = pg.PlotWidget()
        self.balance_plot.setAxisItems({'bottom': self.balance_date_axis})
        self.balance_plot.showGrid(x=True, y=True, alpha=0.3)
        # ----- Общая ось -----
        self.balance_plot.setXLink(self.candlestick_plot)

        self.stat_texts = [
            "Winrate",
            "Profit",
            "Trades",
            "Period",
            "Initial balance",
            "Final balance",
            "Max drawdown"
        ]

        self.stats = {'winrate': '0%', \
            'profit': '0%', \
            'trades': '0', \
            'period': '0 days', \
            'init': '0 USDT', \
            'final': '0 USDT', \
            'drawdown': '0%'}

        # Создаем область статистики с шестью колонками
        self.stats_layout = QGridLayout()
        self.values_layout = QGridLayout()
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        self.values_layout.setContentsMargins(0, 0, 0, 0)   
        self.stats_layout.setSpacing(-15)
        self.values_layout.setSpacing(-15)

        self.init_statistic()

        # Настройка стилей
        self.init_canvas(facecolor, textcolor)

        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.candlestick_plot, stretch=3)
        l.addLayout(self.stats_layout)
        l.addLayout(self.values_layout)
        l.addWidget(self.balance_plot, stretch=1)

        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)

        self.widget = QWidget()
        self.widget.setLayout(l)

        self.drawing_mode = None
        self.drawing_items = []
        self.current_drawing = None
        self.drawing_start_pos = None

        super(PGCanvas, self).__init__(self.widget)

        self.init_drawing_tools()
        
        # Добавляем панель инструментов
        self.toolbar = QToolBar()
        self.init_drawing_toolbar()
        l.addWidget(self.toolbar)
        
        # Инициализация переменных для рисования
        self.drawing_mode = None
        self.drawing_items = []
        self.current_drawing = None
        self.drawing_start_pos = None
        self.current_color = QtGui.QColor('white')
        self.current_width = 2

    def get_canvas(self):
        return self.widget

    def init_canvas(self, facecolor, textcolor):
        """Метод для инициализации или обновления цветов"""
        # Удаляем глобальные настройки
        # pg.setConfigOption('background', facecolor)
        # pg.setConfigOption('foreground', textcolor)
        
        self.textcolor = textcolor
        self.facecolor = facecolor
        
        # Устанавливаем цвета напрямую для каждого элемента графика
        self.candlestick_plot.setBackground(facecolor)
        self.balance_plot.setBackground(facecolor)
        
        # Настройка цветов осей и подписей для candlestick_plot
        self.candlestick_plot.getAxis('left').setTextPen('gray')
        self.candlestick_plot.getAxis('bottom').setTextPen('gray')
        self.candlestick_plot.getAxis('left').setPen('gray')
        self.candlestick_plot.getAxis('bottom').setPen('gray')
        
        # Настройка цветов осей и подписей для balance_plot
        self.balance_plot.getAxis('left').setTextPen('gray')
        self.balance_plot.getAxis('bottom').setTextPen('gray')
        self.balance_plot.getAxis('left').setPen('gray')
        self.balance_plot.getAxis('bottom').setPen('gray')
        
        # Настройка цвета сетки
        self.candlestick_plot.getAxis('left').setGrid(100)
        self.candlestick_plot.getAxis('bottom').setGrid(100)
        self.balance_plot.getAxis('left').setGrid(100)
        self.balance_plot.getAxis('bottom').setGrid(100)
        
        self.winrate_label.setStyleSheet(f"color: #089981; font: 12pt;")
        self.profit_label.setStyleSheet(f"color: #089981; font: 12pt;")
        self.trades_label.setStyleSheet(f"color: {self.textcolor}; font: 12pt;")
        self.period_label.setStyleSheet(f"color: {self.textcolor}; font: 12pt;")
        self.init_label.setStyleSheet(f"color: #089981; font: 12pt;")
        self.final_label.setStyleSheet(f"color: #089981; font: 12pt;")
        self.drawdown_label.setStyleSheet(f"color: #F23645; font: 12pt;")

        self.data_label.setStyleSheet(f"color: {self.textcolor};")
        self.price_label.setStyleSheet(f"color: {self.textcolor};")

        for i, text in enumerate(self.stat_texts):
            self.stats_layout.itemAt(i).widget().setStyleSheet(f"color: {self.textcolor};")
        

    def update_colors(self, facecolor, textcolor):
        """Метод для обновления цветов и перерисовки"""
        self.init_canvas(facecolor, textcolor)

    def add_cursor_line(self):
        # ----- Курсор с линиями -----
        self.vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.hline = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.candlestick_plot.addItem(self.vline, ignoreBounds=True)
        self.candlestick_plot.addItem(self.hline, ignoreBounds=True)
        self.vline_ = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.hline_ = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.balance_plot.addItem(self.vline_, ignoreBounds=True)
        self.balance_plot.addItem(self.hline_, ignoreBounds=True)
        self.candlestick_plot.scene().sigMouseMoved.connect(self.mouse_moved_candel)
        self.balance_plot.scene().sigMouseMoved.connect(self.mouse_moved_balance)

    def init_statistic(self):

        for i, text in enumerate(self.stat_texts):
            label = QLabel(text)
            label.setAlignment(QtCore.Qt.AlignLeft)
            self.stats_layout.addWidget(label, 0, i)

        self.data_label = QLabel("Date: N/A")
        self.data_label.setAlignment(QtCore.Qt.AlignCenter)
        self.stats_layout.addWidget(self.data_label, 0, 7)

        self.price_label = QLabel("Price: N/A")
        self.price_label.setAlignment(QtCore.Qt.AlignCenter)
        self.values_layout.addWidget(self.price_label, 0, 7)
        
        self.winrate_label = QLabel(self.stats['winrate'])
        self.profit_label = QLabel(self.stats['profit'])
        self.trades_label = QLabel(self.stats['trades'])
        self.period_label = QLabel(self.stats['period'])
        self.init_label = QLabel(self.stats['init'])
        self.final_label = QLabel(self.stats['final'])
        self.drawdown_label = QLabel(self.stats['drawdown'])
        self.winrate_label.setAlignment(QtCore.Qt.AlignLeft)
        self.profit_label.setAlignment(QtCore.Qt.AlignLeft)
        self.trades_label.setAlignment(QtCore.Qt.AlignLeft)
        self.period_label.setAlignment(QtCore.Qt.AlignLeft)
        self.init_label.setAlignment(QtCore.Qt.AlignLeft)
        self.final_label.setAlignment(QtCore.Qt.AlignLeft)
        self.drawdown_label.setAlignment(QtCore.Qt.AlignLeft)
        self.values_layout.addWidget(self.winrate_label, 0, 0)
        self.values_layout.addWidget(self.profit_label, 0, 1)
        self.values_layout.addWidget(self.trades_label, 0, 2)
        self.values_layout.addWidget(self.period_label, 0, 3)
        self.values_layout.addWidget(self.init_label, 0, 4)
        self.values_layout.addWidget(self.final_label, 0, 5)
        self.values_layout.addWidget(self.drawdown_label, 0, 6)

    def plot_statistic(self):        
        self.winrate_label.setText(self.stats['winrate'])
        self.profit_label.setText(self.stats['profit'])
        self.trades_label.setText(self.stats['trades'])
        self.period_label.setText(self.stats['period'])
        self.init_label.setText(self.stats['init'])
        self.final_label.setText(self.stats['final'])
        self.drawdown_label.setText(self.stats['drawdown'])

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
        
        self.stats = stats

        self.winrate_label.setStyleSheet(f"color: #089981; font: 12pt;") if winrate >= 0 else self.drawdown_label.setStyleSheet(f"color: #F23645; font: 12pt;")
        self.profit_label.setStyleSheet(f"color: #089981; font: 12pt;") if profit >= 0 else self.profit_label.setStyleSheet(f"color: #F23645; font: 12pt;")
        self.final_label.setStyleSheet(f"color: #089981; font: 12pt;") if balance['value'].iloc[-1] >= balance['value'].iloc[0] else self.final_label.setStyleSheet(f"color: #F23645; font: 12pt;")

    def plot_candlestick(self, ohlc_data):
        times = ohlc_data.index.astype('int64') // 10**9  # Преобразование в UNIX-время (секунды)
        candle_width = 0.7 * (times[1] - times[0])
        shadow_width = candle_width / 10
        
        for i, (index, row) in enumerate(ohlc_data.iterrows()):
            open = row['open']
            high = row['high']
            low = row['low']
            close = row['close']
            date = times[i]

            clr = '#089981' if close >= open else '#F23645'
            
            candle_item = QGraphicsRectItem(date - candle_width/2, open if close >= open else close,
                                                    candle_width, abs(open - close))
            candle_item.setPen(pg.mkPen(color = clr, width=1.5))
            candle_item.setBrush(pg.mkBrush(color = clr))
            self.candlestick_plot.addItem(candle_item)
            
        for i, (index, row) in enumerate(ohlc_data.iterrows()):
            open = row['open']
            high = row['high']
            low = row['low']
            close = row['close']
            date = times[i]

            clr = '#089981' if close >= open else '#F23645'
            
            shadow_item = QGraphicsRectItem(date - shadow_width/2, low,
                                                    shadow_width, abs(high - low))
            shadow_item.setPen(pg.mkPen(color = clr, width=1.5))
            shadow_item.setBrush(pg.mkBrush(color = clr))
            self.candlestick_plot.addItem(shadow_item)

    def plot_balance(self, data):
        init = data['value'].iloc[0]
        cm = pg.ColorMap([0.0, 1.0], ['#F23645', '#089981'])
        pen0 = cm.getPen(span=(init-0.5, init+0.0), width=2)
        
        # Fix division by zero by checking if min and max are equal
        value_min = data['value'].min()
        value_max = data['value'].max()
        if value_max == value_min:
            level = 0.5  # Use middle value if range is 0
        else:
            level = (init - value_min)/(value_max - value_min)

        grad = QtGui.QLinearGradient(0, value_min, 0, value_max)
        grad.setColorAt(0.0, pg.mkColor('#F23645'))
        grad.setColorAt(level, QColor(0, 0, 0, 0))
        grad.setColorAt(1, pg.mkColor('#089981'))
        brush = QtGui.QBrush(grad)
        self.balance_plot.plot(data['ts'].astype('int64') // 10**9, data['value'], fillLevel=init, brush=brush, pen=pen0, name="Balance")

    def plot_indicators(self, ohlc_data, indicator_names):
        colors = ['#00FF10', '#FF0010', '#0505F0', '#A010A0', '#10F0F0', '#FFFFFF', '#F01060']
        for i, ind_name in enumerate(indicator_names):
            if ind_name in ohlc_data.columns:
                j = len(ohlc_data) - 1
                while j > 0 and math.isnan(ohlc_data[ind_name].iloc[j]):
                    j -= 1
                if ohlc_data[ind_name].iloc[j] > ohlc_data['close'].iloc[j] * 0.5 and ohlc_data[ind_name].iloc[j] < ohlc_data['close'].iloc[j] * 2: 
                    indicator_data = ohlc_data[ind_name]
                    color = colors[i % len(colors)]
                    plot_item = self.candlestick_plot.plot(
                        ohlc_data.index.astype('int64') // 10**9, indicator_data,
                        pen=pg.mkPen(color=color, width=2),
                        name=ind_name, alpha=0.5
                    )
                    plot_item.setAlpha(0.5, False)
                    
                else:
                    price_min, price_max = ohlc_data[['low', 'high']].min().min(), ohlc_data[['low', 'high']].max().max()
                    indicator_data = ohlc_data[ind_name]
                    ind_min, ind_max = indicator_data.min(), indicator_data.max()
                    scaled_indicator = ((indicator_data - ind_min) / (ind_max - ind_min)) * (price_max - price_min) + price_min
                    color = colors[i % len(colors)]
                    plot_item = self.candlestick_plot.plot(
                        ohlc_data.index.astype('int64') // 10**9, scaled_indicator,
                        pen=pg.mkPen(color=color, width=2),
                        name=ind_name, alpha=0.5
                    )
                    plot_item.setAlpha(0.5, False)

    def plot_positions(self, positions, ohlc_data):
        times = ohlc_data.index.astype('int64') // 10**9
        padding = (ohlc_data['high'] - ohlc_data['low']).mean() / 2
        bold_font = QFont()
        bold_font.setBold(True)
        xlo=[]
        ylo=[]
        xlc=[]
        ylc=[]
        xso=[]
        yso=[]
        xsc=[]
        ysc=[]

        for position in positions:

            open_ts = position['openTimestamp']
            close_ts = position['closeTimestamp'] if position['status'] == 'closed' else None
            
            # Поиск соответствующей свечи по метке времени
            open_candle = ohlc_data.loc[open_ts] if open_ts in ohlc_data.index else None
            close_candle = ohlc_data.loc[close_ts] if close_ts and close_ts in ohlc_data.index else None
            
            if position['posSide'] == 'long':
                xlo.append(position['openTimestamp'].value // 10**9)
                ylo.append(position['openPrice'])
                if open_candle is not None:
                    buy_text = TextItem("buy", color=(150, 150, 150))
                    buy_text.setFont(bold_font)
                    buy_text.setAnchor((0.5, 0))  # Центрирование под свечой
                    self.candlestick_plot.addItem(buy_text)
                    buy_text.setPos(xlo[-1], open_candle['low'] - padding)  

                if position['status'] == 'closed':
                    xlc.append(position['closeTimestamp'].value // 10**9)
                    ylc.append(position['closePrice'])
                
                    if position['pnl'] > 0:
                        pnl_text = TextItem(f"+{position['pnl']:.1f}\nclose", color=(150, 150, 150))
                    else:
                        pnl_text = TextItem(f"{position['pnl']:.2f}\nclose", color=(150, 150, 150))
                    pnl_text.setFont(bold_font)
                    pnl_text.setAnchor((0.5, 1))
                    self.candlestick_plot.addItem(pnl_text)
                    pnl_text.setPos(xlc[-1], close_candle['high'] + padding)                   

                    self.add_tp_sl_rectangles(position, open_ts.value // 10**9, close_ts.value // 10**9, ohlc_data['close'].iloc[-1])
                else:
                    self.add_tp_sl_rectangles(position, open_ts.value // 10**9, times[-1], ohlc_data['close'].iloc[-1])

                        
            if position['posSide'] == 'short':
                xso.append(position['openTimestamp'].value // 10**9)
                yso.append(position['openPrice'])
                if open_candle is not None:
                    sell_text = TextItem("sell", color=(150, 150, 150))
                    sell_text.setFont(bold_font)
                    sell_text.setAnchor((0.5, 1))  # Центрирование под свечой
                    self.candlestick_plot.addItem(sell_text)
                    sell_text.setPos(xso[-1], open_candle['low'] - padding)
                if position['status'] == 'closed':
                    xsc.append(position['closeTimestamp'].value // 10**9)
                    ysc.append(position['closePrice'])
                
                    if position['pnl'] > 0:
                        pnl_text = TextItem(f"+{position['pnl']:.1f}\nclose", color=(150, 150, 150))
                    else:
                        pnl_text = TextItem(f"{position['pnl']:.2f}\nclose", color=(150, 150, 150))
                    pnl_text.setFont(bold_font)
                    pnl_text.setAnchor((0.5, 1))
                    self.candlestick_plot.addItem(pnl_text)
                    pnl_text.setPos(xsc[-1], close_candle['high'] + padding)

                    self.add_tp_sl_rectangles(position, open_ts.value // 10**9, close_ts.value // 10**9, ohlc_data['close'].iloc[-1])
                else:
                    self.add_tp_sl_rectangles(position, open_ts.value // 10**9, times[-1], ohlc_data['close'].iloc[-1])
                        
        self.candlestick_plot.plot(xlo, ylo, symbol='t1', symbolBrush=(70, 175, 80), symbolSize=13, pen = None)
        self.candlestick_plot.plot(xlc, ylc, symbol='x', symbolBrush=(242, 54, 69), symbolSize=13, pen = None)
        self.candlestick_plot.plot(xso, yso, symbol='t', symbolBrush=(242, 54, 69), symbolSize=13, pen = None)
        self.candlestick_plot.plot(xsc, ysc, symbol='x', symbolBrush=(70, 175, 80), symbolSize=13, pen = None)
        
    def add_tp_sl_rectangles(self, position, open_ts, close_ts, last_price):
        # Вычисляем координаты прямоугольника
        start_time = open_ts
        end_time = close_ts
        if position['tpTriggerPx'] > 0 and position['slTriggerPx'] > 0:
            if position['status'] == 'closed':
                top, bottom = max(position['openPrice'], position['tpTriggerPx']), min(position['openPrice'], position['tpTriggerPx'])
                if position['posSide'] == 'long':
                    gradient = QLinearGradient(start_time, top, start_time, bottom)
                else:
                    gradient = QLinearGradient(start_time, bottom, start_time, top)
                gradient.setColorAt(0, QColor(8, 153, 129, 100))
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
                rect_item = QGraphicsRectItem(start_time, bottom, end_time - start_time, top - bottom)
                rect_item.setBrush(QBrush(gradient))
                rect_item.setPen(mkPen(None))  # Без обводки
                self.candlestick_plot.addItem(rect_item)

                top, bottom = max(position['openPrice'], position['slTriggerPx']), min(position['openPrice'], position['slTriggerPx'])
                if position['posSide'] == 'long':
                    gradient = QLinearGradient(start_time, bottom, start_time, top)
                else:
                    gradient = QLinearGradient(start_time, top, start_time, bottom)
                gradient.setColorAt(0, QColor(242, 54, 69, 100))
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
                rect_item = QGraphicsRectItem(start_time, bottom, end_time - start_time, top - bottom)
                rect_item.setBrush(QBrush(gradient))
                rect_item.setPen(mkPen(None))  # Без обводки
                self.candlestick_plot.addItem(rect_item)
        else:
            if position['closePrice'] > 0:
                top, bottom = max(position['openPrice'], position['closePrice']), min(position['openPrice'], position['closePrice'])
            else:
                top, bottom = max(position['openPrice'], last_price), min(position['openPrice'], last_price)
            if position['posSide'] == 'long':
                gradient = QLinearGradient(start_time, bottom, start_time, top)
            else:
                gradient = QLinearGradient(start_time, top, start_time, bottom)

            if last_price > position['openPrice'] and position['posSide'] == 'long' or last_price < position['openPrice'] and position['posSide'] == 'short':
                gradient.setColorAt(0, QColor(8, 153, 129, 100))
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
            else:
                gradient.setColorAt(0, QColor(242, 54, 69, 100))
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
            rect_item = QGraphicsRectItem(start_time, bottom, end_time - start_time, top - bottom)
            rect_item.setBrush(QBrush(gradient))
            rect_item.setPen(mkPen(None))  # Без обводки
            self.candlestick_plot.addItem(rect_item)

    def mouse_moved_candel(self, evt):
        mouse_point = self.candlestick_plot.plotItem.vb.mapSceneToView(evt)
        self.vline.setPos(mouse_point.x())
        self.vline_.setPos(mouse_point.x())
        self.hline.setPos(mouse_point.y())

        # Обновление плашек с ценой и временем
        time_text = dt.utcfromtimestamp(mouse_point.x()).strftime('%H:%M %d-%m-%Y')
        price_text = f"Price: {mouse_point.y():.2f}"
        self.data_label.setText(f"{time_text}")
        self.price_label.setText(f"{price_text}")

    def mouse_moved_balance(self, evt):        
        mouse_point = self.balance_plot.plotItem.vb.mapSceneToView(evt)
        self.vline_.setPos(mouse_point.x())
        self.vline.setPos(mouse_point.x())
        self.hline_.setPos(mouse_point.y())

        # Обновление плашек с ценой и временем
        time_text = dt.utcfromtimestamp(mouse_point.x()).strftime('%H:%M %d-%m-%Y')
        price_text = f"Price: {mouse_point.y():.2f}"
        self.data_label.setText(f"{time_text}")
        self.price_label.setText(f"{price_text}")

    def init_drawing_tools(self):
        """Initialize drawing tools functionality"""
        self.candlestick_plot.scene().sigMouseClicked.connect(self.on_plot_click)
        self.candlestick_plot.scene().sigMouseMoved.connect(self.on_plot_mouse_moved)

    def set_drawing_mode(self, mode):
        """Set current drawing mode (line, rectangle, etc.)"""
        self.drawing_mode = mode
        if mode is None:
            self.drawing_start_pos = None
            if self.current_drawing:
                self.candlestick_plot.removeItem(self.current_drawing)
                self.current_drawing = None

    def on_plot_click(self, event):
        if self.drawing_mode:
            pos = self.candlestick_plot.plotItem.vb.mapSceneToView(event.scenePos())
            
            if not self.drawing_start_pos:
                self.drawing_start_pos = (pos.x(), pos.y())
                if self.drawing_mode == 'line':
                    self.current_drawing = pg.PlotDataItem(pen=pg.mkPen('w', width=2))
                    self.candlestick_plot.addItem(self.current_drawing)
            else:
                end_pos = (pos.x(), pos.y())
                if self.drawing_mode == 'line':
                    line_item = pg.PlotDataItem(
                        [self.drawing_start_pos[0], end_pos[0]],
                        [self.drawing_start_pos[1], end_pos[1]],
                        pen=pg.mkPen('w', width=2)
                    )
                    self.candlestick_plot.addItem(line_item)
                    self.drawing_items.append(line_item)
                
                self.drawing_start_pos = None
                if self.current_drawing:
                    self.candlestick_plot.removeItem(self.current_drawing)
                    self.current_drawing = None

    def on_plot_mouse_moved(self, evt):
        """Handle mouse movement while drawing"""
        if not self.drawing_mode or (not self.drawing_start_pos and self.drawing_mode != 'freehand'):
            return
            
        pos = self.candlestick_plot.plotItem.vb.mapSceneToView(evt)
        
        if self.drawing_mode == 'freehand':
            if evt.buttons() == QtCore.Qt.LeftButton:  # Проверяем нажатие левой кнопки мыши
                if self.current_drawing is None:
                    self.current_drawing = pg.PlotDataItem(pen=pg.mkPen(color=self.current_color, width=self.current_width))
                    self.candlestick_plot.addItem(self.current_drawing)
                    self.current_drawing.setData([pos.x()], [pos.y()])
                else:
                    xdata = list(self.current_drawing.xData)
                    ydata = list(self.current_drawing.yData)
                    xdata.append(pos.x())
                    ydata.append(pos.y())
                    self.current_drawing.setData(xdata, ydata)
            else:
                if self.current_drawing is not None:
                    self.drawing_items.append(self.current_drawing)
                    self.current_drawing = None
        elif self.current_drawing:
            if self.drawing_mode in ['line', 'arrow']:
                self.current_drawing.setData(
                    [self.drawing_start_pos[0], pos.x()],
                    [self.drawing_start_pos[1], pos.y()]
                )
            elif self.drawing_mode == 'rectangle':
                x = [self.drawing_start_pos[0], pos.x(), pos.x(), 
                     self.drawing_start_pos[0], self.drawing_start_pos[0]]
                y = [self.drawing_start_pos[1], self.drawing_start_pos[1], 
                     pos.y(), pos.y(), self.drawing_start_pos[1]]
                self.current_drawing.setData(x, y)

    def clear_drawings(self):
        """Remove all drawings from the plot"""
        for item in self.drawing_items:
            self.candlestick_plot.removeItem(item)
        self.drawing_items = []
        
    def undo_last_drawing(self):
        """Remove the last drawing from the plot"""
        if self.drawing_items:
            item = self.drawing_items.pop()
            self.candlestick_plot.removeItem(item)

    def init_drawing_toolbar(self):
        """Initialize the drawing toolbar with all drawing tools"""
        # Установка прозрачного фона для панели инструментов
        self.toolbar.setStyleSheet("""
            QToolBar {
                background: rgba(0, 0, 0, 0);
                border-radius: 10px;
                spacing: 5px;
                padding: 2px;
            }
            QToolBar QToolButton {
                background: transparent;
                border: 1px solid rgba(100, 100, 100, 255);
                border-radius: 7px;
            }
            QToolBar QToolButton:hover {
                background-color: rgba(255, 255, 255, 20);
                border-radius: 7px;
            }
        """)
        
        # Кнопка выбора цвета
        color_action = QAction('Цвет', self)
        color_action.triggered.connect(self.choose_color)
        self.toolbar.addAction(color_action)
        
        # Кнопка выбора толщины линии
        width_action = QAction('Толщина', self)
        width_action.triggered.connect(self.choose_width)
        self.toolbar.addAction(width_action)
        
        self.toolbar.addSeparator()
        
        # Кнопка линии
        line_action = QAction('Линия', self)
        line_action.triggered.connect(lambda: self.set_drawing_mode('line'))
        self.toolbar.addAction(line_action)
        
        # Кнопка стрелки
        arrow_action = QAction('Стрелка', self)
        arrow_action.triggered.connect(lambda: self.set_drawing_mode('arrow'))
        self.toolbar.addAction(arrow_action)
        
        # Кнопка прямоугольника
        rect_action = QAction('Прямоугольник', self)
        rect_action.triggered.connect(lambda: self.set_drawing_mode('rectangle'))
        self.toolbar.addAction(rect_action)
        
        # Кнопка текста
        text_action = QAction('Текст', self)
        text_action.triggered.connect(lambda: self.set_drawing_mode('text'))
        self.toolbar.addAction(text_action)
        
        # Кнопка рисования от руки
        freehand_action = QAction('От руки', self)
        freehand_action.triggered.connect(lambda: self.set_drawing_mode('freehand'))
        self.toolbar.addAction(freehand_action)
        
        self.toolbar.addSeparator()
        
        # Кнопка ластика
        eraser_action = QAction('Ластик', self)
        eraser_action.triggered.connect(lambda: self.set_drawing_mode('eraser'))
        self.toolbar.addAction(eraser_action)
        
        # Кнопка отмены
        undo_action = QAction('Отменить', self)
        undo_action.triggered.connect(self.undo_last_drawing)
        self.toolbar.addAction(undo_action)
        
        # Кнопка очистки
        clear_action = QAction('Очистить всё', self)
        clear_action.triggered.connect(self.clear_drawings)
        self.toolbar.addAction(clear_action)

    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color

    def choose_width(self):
        width, ok = QInputDialog.getInt(self, 'Толщина линии', 
                                      'Выберите толщину линии:', 
                                      self.current_width, 1, 10)
        if ok:
            self.current_width = width

    def set_drawing_mode(self, mode):
        """Set current drawing mode and update cursor"""
        if self.drawing_mode == mode:
            self.drawing_mode = None
            self.candlestick_plot.unsetCursor()
        else:
            self.drawing_mode = mode
            if mode == 'eraser':
                self.candlestick_plot.setCursor(QtCore.Qt.CrossCursor)
            else:
                self.candlestick_plot.setCursor(QtCore.Qt.CrossCursor)

    def on_plot_click(self, event):
        if not self.drawing_mode:
            return
            
        pos = self.candlestick_plot.plotItem.vb.mapSceneToView(event.scenePos())
        
        if self.drawing_mode == 'eraser':
            self.handle_eraser_click(pos)
        elif self.drawing_mode == 'text':
            self.handle_text_click(pos)
        else:
            if not self.drawing_start_pos:
                self.start_drawing(pos)
            else:
                self.finish_drawing(pos)

    def start_drawing(self, pos):
        """Start drawing at the given position"""
        self.drawing_start_pos = (pos.x(), pos.y())
        pen = pg.mkPen(color=self.current_color, width=self.current_width)
        
        if self.drawing_mode == 'freehand':
            self.current_drawing = pg.PlotDataItem(pen=pen)
            self.current_drawing.setData([pos.x()], [pos.y()])
        elif self.drawing_mode in ['line', 'arrow']:
            self.current_drawing = pg.PlotDataItem(pen=pen)
        elif self.drawing_mode == 'rectangle':
            self.current_drawing = pg.PlotDataItem(pen=pen)
            
        if self.current_drawing:
            self.candlestick_plot.addItem(self.current_drawing)

    def finish_drawing(self, pos):
        """Finish drawing at the given position"""
        end_pos = (pos.x(), pos.y())
        pen = pg.mkPen(color=self.current_color, width=self.current_width)
        
        if self.drawing_mode == 'line':
            line = pg.PlotDataItem(
                [self.drawing_start_pos[0], end_pos[0]],
                [self.drawing_start_pos[1], end_pos[1]],
                pen=pen
            )
            self.candlestick_plot.addItem(line)
            self.drawing_items.append(line)
            
        elif self.drawing_mode == 'arrow':
            # Create arrow with arrowhead
            arrow = self.create_arrow(self.drawing_start_pos, end_pos)
            self.candlestick_plot.addItem(arrow)
            self.drawing_items.append(arrow)
            
        elif self.drawing_mode == 'rectangle':
            rect = self.create_rectangle(self.drawing_start_pos, end_pos)
            self.candlestick_plot.addItem(rect)
            self.drawing_items.append(rect)
            
        self.drawing_start_pos = None
        if self.current_drawing:
            self.candlestick_plot.removeItem(self.current_drawing)
            self.current_drawing = None

    def handle_text_click(self, pos):
        """Handle click when in text mode"""
        text, ok = QInputDialog.getText(self, 'Добавить текст', 'Введите текст:')
        if ok and text:
            text_item = pg.TextItem(text, color=self.current_color)
            text_item.setPos(pos.x(), pos.y())
            self.candlestick_plot.addItem(text_item)
            self.drawing_items.append(text_item)

    def handle_eraser_click(self, pos):
        """Handle click when in eraser mode"""
        items_to_remove = []
        for item in self.drawing_items:
            if isinstance(item, pg.PlotDataItem):
                # Для линий и фигур проверяем каждый сегмент
                xdata = item.xData
                ydata = item.yData
                if xdata is not None and ydata is not None:
                    for i in range(len(xdata)-1):
                        if self.is_point_near_line(pos, 
                                                 (xdata[i], ydata[i]), 
                                                 (xdata[i+1], ydata[i+1])):
                            self.candlestick_plot.removeItem(item)
                            items_to_remove.append(item)
                            break
            elif isinstance(item, pg.TextItem):
                # Для текста проверяем позицию
                item_pos = item.pos()
                if abs(item_pos.x() - pos.x()) < 20 and abs(item_pos.y() - pos.y()) < 20:
                    self.candlestick_plot.removeItem(item)
                    items_to_remove.append(item)
        
        for item in items_to_remove:
            self.drawing_items.remove(item)

    def is_point_near_line(self, point, line_start, line_end, threshold=10):
        """Check if point is near line segment"""
        x, y = point.x(), point.y()
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Вычисляем длину линии
        line_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if line_length == 0:
            return False
        
        # Вычисляем расстояние от точки до линии
        distance = abs((x2 - x1) * (y1 - y) - (x1 - x) * (y2 - y1)) / line_length
        
        # Проверяем, находится ли проекция точки на линии между концами отрезка
        dot_product = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / line_length ** 2
        return distance < threshold and 0 <= dot_product <= 1

    def create_arrow(self, start_pos, end_pos):
        """Create an arrow with arrowhead"""
        # Create the main line
        arrow = pg.PlotDataItem(
            [start_pos[0], end_pos[0]],
            [start_pos[1], end_pos[1]],
            pen=pg.mkPen(color=self.current_color, width=self.current_width)
        )
        return arrow

    def create_rectangle(self, start_pos, end_pos):
        """Create a rectangle"""
        x = [start_pos[0], end_pos[0], end_pos[0], start_pos[0], start_pos[0]]
        y = [start_pos[1], start_pos[1], end_pos[1], end_pos[1], start_pos[1]]
        rect = pg.PlotDataItem(x, y, pen=pg.mkPen(color=self.current_color, width=self.current_width))
        return rect

    def on_plot_mouse_moved(self, evt):
        """Handle mouse movement while drawing"""
        if not self.drawing_mode or not self.drawing_start_pos:
            return
            
        pos = self.candlestick_plot.plotItem.vb.mapSceneToView(evt)
        
        if self.drawing_mode == 'freehand' and self.current_drawing:
            xdata = list(self.current_drawing.xData)
            ydata = list(self.current_drawing.yData)
            xdata.append(pos.x())
            ydata.append(pos.y())
            self.current_drawing.setData(xdata, ydata)
        elif self.current_drawing:
            if self.drawing_mode in ['line', 'arrow']:
                self.current_drawing.setData(
                    [self.drawing_start_pos[0], pos.x()],
                    [self.drawing_start_pos[1], pos.y()]
                )
            elif self.drawing_mode == 'rectangle':
                x = [self.drawing_start_pos[0], pos.x(), pos.x(), 
                     self.drawing_start_pos[0], self.drawing_start_pos[0]]
                y = [self.drawing_start_pos[1], self.drawing_start_pos[1], 
                     pos.y(), pos.y(), self.drawing_start_pos[1]]
                self.current_drawing.setData(x, y)



