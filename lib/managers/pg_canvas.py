from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
from pyqtgraph import TextItem, PlotDataItem, mkPen, mkBrush, BarGraphItem
from PyQt5.QtWidgets import (QGraphicsRectItem, QGridLayout, QLabel, QWidget, 
                           QFrame, QToolBar, QAction, QInputDialog, QColorDialog,
                           QToolButton, QMenu, QScrollArea, QVBoxLayout)
from datetime import datetime as dt
from PyQt5.QtGui import QFont, QColor, QLinearGradient, QBrush
from PyQt5.QtCore import QMargins
import math
import pandas as pd
import numpy as np

class PGCanvas(QWidget):
    def __init__(self, facecolor, textcolor):
        super(PGCanvas, self).__init__()
        self.textcolor= textcolor
        
        # Initialize statistics first
        self.stat_texts = [
            "Winrate", "Profit", "Trades", "Period",
            "Initial balance", "Final balance", "Max drawdown"
        ]
        
        self.stats = {
            'winrate': '0%',
            'profit': '0%',
            'trades': '0',
            'period': '0 days',
            'init': '0 USDT',
            'final': '0 USDT',
            'drawdown': '0%'
        }

        # Create stats layouts before using them
        self.stats_layout = QGridLayout()
        self.values_layout = QGridLayout()
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        self.values_layout.setContentsMargins(0, 0, 0, 0)   
        self.stats_layout.setSpacing(-15)
        self.values_layout.setSpacing(-15)

        # Initialize date axis objects for each plot
        price_date_axis = pg.DateAxisItem(orientation='bottom')
        balance_date_axis = pg.DateAxisItem(orientation='bottom')
        capital_date_axis = pg.DateAxisItem(orientation='bottom')
        daily_income_date_axis = pg.DateAxisItem(orientation='bottom')
        positions_axis = pg.DateAxisItem(orientation='bottom')

        # Create main widget and layout
        self.widget = QWidget()
        main_layout = QVBoxLayout(self.widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll = QScrollArea()
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)

        self.candlestick_plot = pg.PlotWidget(axisItems={'bottom': price_date_axis})
        self.candlestick_plot.showGrid(x=True, y=True, alpha=0.3)
        self.candlestick_plot.addLegend()
        self.candlestick_plot.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.candlestick_plot.setMinimumHeight(600)
        self.scroll_layout.addWidget(self.candlestick_plot)
        self.scroll_layout.addLayout(self.stats_layout)
        self.scroll_layout.addLayout(self.values_layout)

        self.balance_plot = pg.PlotWidget(axisItems={'bottom': balance_date_axis})
        self.balance_plot.showGrid(x=True, y=True, alpha=0.3)
        self.balance_plot.setXLink(self.candlestick_plot)
        self.balance_plot.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.balance_plot.setMinimumHeight(200)
        self.scroll_layout.addWidget(self.balance_plot)

        self.daily_income_plot = pg.PlotWidget(title="Daily Income", axisItems={'bottom': daily_income_date_axis})
        self.daily_income_plot.showGrid(x=True, y=True, alpha=0.3)
        self.daily_income_plot.setXLink(self.candlestick_plot)
        self.daily_income_plot.setMinimumHeight(215)
        self.scroll_layout.addWidget(self.daily_income_plot)

        self.profitability_plot = pg.PlotWidget(title="Positions Profitability")
        self.profitability_plot.showGrid(x=True, y=True, alpha=0.3)
        self.profitability_plot.setMinimumHeight(215)
        self.profitability_plot.getAxis('bottom').setLabel('PnL (USDT)')
        self.profitability_plot.getAxis('left').setLabel('Number of trades')
        self.scroll_layout.addWidget(self.profitability_plot)

        self.positions_plot = pg.PlotWidget(title="Positions PnL", axisItems={'bottom': positions_axis})
        self.positions_plot.showGrid(x=True, y=True, alpha=0.3)
        self.positions_plot.setXLink(self.candlestick_plot)
        self.positions_plot.setMinimumHeight(215)
        self.positions_plot.getAxis('bottom').setLabel('Time')
        self.positions_plot.getAxis('left').setLabel('PnL (USDT)')
        self.positions_plot.setXLink(self.candlestick_plot)  # Связываем с основной осью времени
        self.scroll_layout.addWidget(self.positions_plot)
        
        self.capital_plot = pg.PlotWidget(title="Capital Usage", axisItems={'bottom': capital_date_axis})
        self.capital_plot.showGrid(x=True, y=True, alpha=0.3)
        self.capital_plot.setXLink(self.candlestick_plot)
        self.capital_plot.setMinimumHeight(215)
        self.scroll_layout.addWidget(self.capital_plot)
        


        # Setup scroll area
        self.scroll_content.setLayout(self.scroll_layout)
        scroll.setWidget(self.scroll_content)
        scroll.setWidgetResizable(True)

        # Add scroll area to main layout
        main_layout.addWidget(scroll)

        # Initialize UI components
        self.init_statistic()
        self.init_canvas(facecolor, textcolor)
        self.init_drawing_tools()

        # Add toolbar
        self.toolbar = QToolBar()
        self.init_drawing_toolbar()
        main_layout.addWidget(self.toolbar)

        # Initialize drawing variables
        self.drawing_mode = None
        self.drawing_items = []
        self.current_drawing = None
        self.drawing_start_pos = None
        self.current_color = QtGui.QColor('white')
        self.current_width = 2

        # Set the main widget as the PGCanvas widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget)

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
        for plot in [self.candlestick_plot, self.balance_plot, 
                    self.capital_plot, self.daily_income_plot, 
                    self.profitability_plot, self.positions_plot]:
            plot.setBackground(facecolor)
            plot.getAxis('left').setTextPen('gray')
            plot.getAxis('bottom').setTextPen('gray')
            plot.getAxis('left').setPen('gray')
            plot.getAxis('bottom').setPen('gray')
            plot.getAxis('left').setGrid(100)
            plot.getAxis('bottom').setGrid(100)
        
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
        self.vline1 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.hline1 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.candlestick_plot.addItem(self.vline1, ignoreBounds=True)
        self.candlestick_plot.addItem(self.hline1, ignoreBounds=True)
        self.vline2 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.hline2 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.balance_plot.addItem(self.vline2, ignoreBounds=True)
        self.balance_plot.addItem(self.hline2, ignoreBounds=True)
        self.vline3 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.hline3 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.capital_plot.addItem(self.vline3, ignoreBounds=True)
        self.capital_plot.addItem(self.hline3, ignoreBounds=True)
        self.vline4 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.hline4 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.daily_income_plot.addItem(self.vline4, ignoreBounds=True)
        self.daily_income_plot.addItem(self.hline4, ignoreBounds=True)
        self.vline5 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.hline5 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("gray", style=QtCore.Qt.DotLine))
        self.profitability_plot.addItem(self.vline5, ignoreBounds=True)
        self.profitability_plot.addItem(self.hline5, ignoreBounds=True)

        self.candlestick_plot.scene().sigMouseMoved.connect(self.mouse_moved_candel)
        self.balance_plot.scene().sigMouseMoved.connect(self.mouse_moved_balance)
        self.capital_plot.scene().sigMouseMoved.connect(self.mouse_moved_capital)
        self.daily_income_plot.scene().sigMouseMoved.connect(self.mouse_moved_income)
        self.profitability_plot.scene().sigMouseMoved.connect(self.mouse_moved_profitability)

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
        times = ohlc_data.index.astype('int64') // 10**9
        opens = ohlc_data['open'].values
        highs = ohlc_data['high'].values
        lows = ohlc_data['low'].values
        closes = ohlc_data['close'].values
        
        # Вычисляем параметры отображения свечей
        candle_width = 0.7 * (times[1] - times[0])
        
        # Определяем цвета свечей
        bull_idx = closes >= opens
        bear_idx = ~bull_idx
        
        # Создаем массивы для бычьих свечей
        bull_times = times[bull_idx]
        bull_opens = opens[bull_idx]
        bull_closes = closes[bull_idx]
        bull_highs = highs[bull_idx]
        bull_lows = lows[bull_idx]
        
        # Создаем массивы для медвежьих свечей
        bear_times = times[bear_idx]
        bear_opens = opens[bear_idx]
        bear_closes = closes[bear_idx]
        bear_highs = highs[bear_idx]
        bear_lows = lows[bear_idx]
        
        # Отрисовка бычьих теней
        if len(bull_times) > 0:
            bull_shadows = pg.PlotDataItem(
                x=np.repeat(bull_times, 2),
                y=np.vstack((bull_lows, bull_highs)).T.flatten(),
                connect='pairs',
                pen=pg.mkPen('#089981', width=1)
            )
            self.candlestick_plot.addItem(bull_shadows)
        
        # Отрисовка медвежьих теней
        if len(bear_times) > 0:
            bear_shadows = pg.PlotDataItem(
                x=np.repeat(bear_times, 2),
                y=np.vstack((bear_lows, bear_highs)).T.flatten(),
                connect='pairs',
                pen=pg.mkPen('#F23645', width=1)
            )
            self.candlestick_plot.addItem(bear_shadows)
        
        # Отрисовка бычьих тел
        if len(bull_times) > 0:
            bull_bodies = pg.BarGraphItem(
                x=bull_times,
                height=bull_closes - bull_opens,
                width=candle_width,
                brush=pg.mkBrush('#089981'),
                pen=pg.mkPen('#089981'),
                y0=bull_opens
            )
            self.candlestick_plot.addItem(bull_bodies)
    
        # Отрисовка медвежьих тел одним вызовом
        if len(bear_times) > 0:
            bear_bodies = pg.BarGraphItem(
                x=bear_times,
                height=bear_closes - bear_opens,
                width=candle_width,
                brush=pg.mkBrush('#F23645'),
                pen=pg.mkPen('#F23645'),
                y0=bear_opens
            )
            self.candlestick_plot.addItem(bear_bodies)

    def plot_balance(self, data):
        init = data['value'].iloc[0]
        cm = pg.ColorMap([0.0, 1.0], ['#F23645', '#089981'])
        pen0 = cm.getPen(span=(init-0.5, init+0.0), width=2)
        
        # Fix division by zero by checking if min and max are equal
        value_min = data['value'].min()
        value_max = data['value'].max()
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
                rect_item.setPen(mkPen(None)) 
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
                rect_item.setPen(mkPen(None)) 
                self.candlestick_plot.addItem(rect_item)
        else:
            if position['closePrice'] == 0: 
                position['closePrice'] = last_price 
            
            gradient = QLinearGradient(start_time, position['openPrice'], start_time, position['closePrice'])

            if position['closePrice'] > position['openPrice'] and position['posSide'] == 'long' \
                or position['closePrice'] < position['openPrice'] and position['posSide'] == 'short':
                gradient.setColorAt(0, QColor(8, 153, 129, 100))
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
            else:
                gradient.setColorAt(0, QColor(242, 54, 69, 100))
                gradient.setColorAt(1, QColor(0, 0, 0, 0))

            rect_item = QGraphicsRectItem(start_time, min(position['closePrice'], position['openPrice']), end_time - start_time, abs(position['closePrice'] - position['openPrice']))
            rect_item.setBrush(QBrush(gradient))
            rect_item.setPen(mkPen(None))  # Без обводки
            self.candlestick_plot.addItem(rect_item)

    def mouse_moved_candel(self, evt):
        mouse_point = self.candlestick_plot.plotItem.vb.mapSceneToView(evt)

        self.hline1.setPos(mouse_point.y())
        self.vline1.setPos(mouse_point.x())
        self.vline2.setPos(mouse_point.x())
        self.vline3.setPos(mouse_point.x())
        self.vline4.setPos(mouse_point.x())
        self.vline5.setPos(mouse_point.x())

        # Обновление плашек с ценой и временем
        time_text = dt.utcfromtimestamp(mouse_point.x()).strftime('%H:%M %d-%m-%Y')
        price_text = f"Price: {mouse_point.y():.2f}"
        self.data_label.setText(f"{time_text}")
        self.price_label.setText(f"{price_text}")

    def mouse_moved_balance(self, evt):        
        mouse_point = self.balance_plot.plotItem.vb.mapSceneToView(evt)

        self.hline2.setPos(mouse_point.y())
        self.vline1.setPos(mouse_point.x())
        self.vline2.setPos(mouse_point.x())
        self.vline3.setPos(mouse_point.x())
        self.vline4.setPos(mouse_point.x())
        self.vline5.setPos(mouse_point.x())

        # Обновление плашек с ценой и временем
        time_text = dt.utcfromtimestamp(mouse_point.x()).strftime('%H:%M %d-%m-%Y')
        price_text = f"Price: {mouse_point.y():.2f}"
        self.data_label.setText(f"{time_text}")
        self.price_label.setText(f"{price_text}")

    def mouse_moved_capital(self, evt):        
        mouse_point = self.capital_plot.plotItem.vb.mapSceneToView(evt)
        
        self.hline3.setPos(mouse_point.y())
        self.vline1.setPos(mouse_point.x())
        self.vline2.setPos(mouse_point.x())
        self.vline3.setPos(mouse_point.x())
        self.vline4.setPos(mouse_point.x())
        self.vline5.setPos(mouse_point.x())

        # Обновление плашек с ценой и временем
        time_text = dt.utcfromtimestamp(mouse_point.x()).strftime('%H:%M %d-%m-%Y')
        price_text = f"Price: {mouse_point.y():.2f}"
        self.data_label.setText(f"{time_text}")
        self.price_label.setText(f"{price_text}")

    def mouse_moved_income(self, evt):        
        mouse_point = self.daily_income_plot.plotItem.vb.mapSceneToView(evt)
        
        self.hline4.setPos(mouse_point.y())
        self.vline1.setPos(mouse_point.x())
        self.vline2.setPos(mouse_point.x())
        self.vline3.setPos(mouse_point.x())
        self.vline4.setPos(mouse_point.x())
        self.vline5.setPos(mouse_point.x())

        # Обновление плашек с ценой и временем
        time_text = dt.utcfromtimestamp(mouse_point.x()).strftime('%H:%M %d-%m-%Y')
        price_text = f"Price: {mouse_point.y():.2f}"
        self.data_label.setText(f"{time_text}")
        self.price_label.setText(f"{price_text}")

    def mouse_moved_profitability(self, evt):        
        mouse_point = self.profitability_plot.plotItem.vb.mapSceneToView(evt)
        
        self.hline5.setPos(mouse_point.y())
        self.vline1.setPos(mouse_point.x())
        self.vline2.setPos(mouse_point.x())
        self.vline3.setPos(mouse_point.x())
        self.vline4.setPos(mouse_point.x())
        self.vline5.setPos(mouse_point.x())

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

    def plot(self, df, positions, balance, indicators):
        """Display data on all charts"""
        for plot in [self.candlestick_plot, self.balance_plot, self.capital_plot, 
                    self.daily_income_plot, self.profitability_plot, self.positions_plot]:
            plot.clear()
            plot.plotItem.vb.clear()

        if len(df) < 5001:
            self.plot_candlestick(df)
        if len(indicators) > 0: 
            self.plot_indicators(df, indicators)
        if len(balance) > 0:
            self.plot_balance(balance)
            self.plot_capital_usage(positions, df)  # Изменено на передачу positions
            self.plot_daily_income(balance)

        if len(positions) > 0:
            self.plot_positions(positions, df)
            self.plot_profitability(positions)
            self.plot_positions_pnl(positions)  # Добавляем отрисовку нового графика
            self.get_statistic(balance, positions)
            self.plot_statistic()

        for plot in [self.capital_plot, self.daily_income_plot]: 
            plot.getAxis('bottom').setStyle(tickFont=QFont('Arial', 8))
            plot.getAxis('left').setStyle(tickFont=QFont('Arial', 8))
            plot.showGrid(x=True, y=True, alpha=0.3)
            plot.setXLink(self.candlestick_plot)

        self.add_cursor_line()

    def plot_capital_usage(self, positions, df):
        """Plot total position quantity over time with step style"""
        if not positions:
            return
            
        times = df.index.astype('int64') // 10**9
        qty_by_time = {t: 0 for t in times}
        shadow_color = pg.mkBrush(255, 255, 255, 50) if self.textcolor == 'white' else pg.mkBrush(96, 156, 210, 50)
        line_pen = pg.mkPen(color='white', width=2) if self.textcolor == 'white' else pg.mkPen(color=(96, 156, 210), width=2)
        
        
        for pos in positions:
            open_time = pos['openTimestamp'].value // 10**9
            close_time = pos['closeTimestamp'].value // 10**9 if pos['status'] == 'closed' else times[-1]
            qty = abs(float(pos['qty']))
            
            for t in times:
                if open_time <= t < close_time:
                    qty_by_time[t] += qty
        
        time_points = list(qty_by_time.keys())
        qty_values = list(qty_by_time.values())
        
        # Добавляем дополнительные точки для ступенчатого отображения
        step_x = []
        step_y = []
        
        for i in range(len(time_points)):
            step_x.append(time_points[i])
            step_x.append(time_points[i] if i == len(time_points)-1 else time_points[i+1])
            step_y.append(qty_values[i])
            step_y.append(qty_values[i])
        
        self.capital_plot.plot(step_x, step_y,
                         pen=line_pen,
                         fillLevel=0,
                         brush=shadow_color,
                         name="Total Position Size")

    def plot_profitability(self, positions):
        """Plot positions profitability histogram"""
        if not positions:
            return

        pnls = [float(p['pnl']) for p in positions if p['status'] == 'closed']
        if not pnls:
            return
        
        num_bins = min(40, int(len(pnls) / 2))  # Не более 20 столбцов
        
        max_pnl = max(pnls)
        min_pnl = min(pnls)

        num_loss_bins = max(0, int( round(num_bins * ((0 - min_pnl) / (max_pnl - min_pnl)))))
        num_profit_bins = num_bins - num_loss_bins

        profits = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        
        self.bar_width = 0
        
        if profits:
            y_profits, x_profits = np.histogram(profits, bins=num_profit_bins)
            x_center = (x_profits[:-1] + x_profits[1:]) / 2
            bar_width = (x_profits[1] - x_profits[0]) * 0.99
            
            profit_bars = pg.BarGraphItem(
                x=x_center,
                height=y_profits,
                width=bar_width,
                brush=pg.mkBrush(color=(70, 175, 80, 100)),
                pen=pg.mkPen(color=(70, 175, 80))
            )
            self.profitability_plot.addItem(profit_bars)
        
        if losses:
            y_losses, x_losses = np.histogram(losses, bins=num_loss_bins)
            x_center = (x_losses[:-1] + x_losses[1:]) / 2
            bar_width = (x_losses[1] - x_losses[0]) * 0.99
            
            loss_bars = pg.BarGraphItem(
                x=x_center,
                height=y_losses,
                width=bar_width,
                brush=pg.mkBrush(color=(242, 54, 69, 100)),
                pen=pg.mkPen(color=(242, 54, 69))
            )
            self.profitability_plot.addItem(loss_bars)

        zero_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('gray', style=QtCore.Qt.DotLine))
        self.profitability_plot.addItem(zero_line)
        
        if profits or losses:
            min_pnl = min(x_losses[0] if losses else 0, 0)
            max_pnl = max(x_profits[-1] if profits else 0, 0)
            self.profitability_plot.setXRange(min_pnl * 1.1, max_pnl * 1.1)  # Добавляем отступы
            self.profitability_plot.setYRange(0, max(max(y_profits) if profits else 0, 
                                                   max(y_losses) if losses else 0) * 1.1)

    def plot_daily_income_step_style(self, balance):
        """Plot daily income as a line chart with step style"""
        # Calculate daily changes
        balance['daily_change'] = balance['value'].diff()
        daily_income = balance.groupby(balance['ts'].dt.date)['daily_change'].sum()    
        daily_dates = pd.to_datetime(daily_income.index)
        times = daily_dates.astype('int64') // 10**9

        # Add an extra point for stepMode
        extra_time = times[-1] + (times[1] - times[0])  # Add one more interval
        times = np.append(times, extra_time)

        init = 0
        cm = pg.ColorMap([0.0, 1.0], ['#F23645', '#089981'])
        pen0 = cm.getPen(span=(init-0.5, init+0.0), width=2)
        
        value_min = daily_income.min()
        value_max = daily_income.max()
        level = (init - value_min)/(value_max - value_min)

        grad = QtGui.QLinearGradient(0, value_min, 0, value_max)
        grad.setColorAt(0.0, pg.mkColor('#F23645'))
        grad.setColorAt(level, QColor(0, 0, 0, 0))
        grad.setColorAt(1, pg.mkColor('#089981'))
        brush = QtGui.QBrush(grad)

        self.daily_income_plot.plot(times, daily_income.values, 
                                  fillLevel=init, 
                                  brush=brush, 
                                  pen=pen0, 
                                  stepMode=True,
                                  name="Balance")
        
    def plot_daily_income(self, balance):
        """Plot daily or hourly income as a line chart, depending on timespan"""

        # Вычисляем общее количество дней
        total_duration = (balance['ts'].max() - balance['ts'].min()).total_seconds()

        if total_duration < 2 * 86400:
            # Меньше двух суток — считаем доход по часам
            balance['hour'] = balance['ts'].dt.floor('H')
            balance['change'] = balance['value'].diff()
            income = balance.groupby('hour')['change'].sum()
            x_axis = pd.to_datetime(income.index)
            label = "Hourly Income"
        else:
            # Больше двух суток — считаем доход по дням
            balance['change'] = balance['value'].diff()
            income = balance.groupby(balance['ts'].dt.date)['change'].sum()
            x_axis = pd.to_datetime(income.index)
            label = "Daily Income"

        # Преобразуем даты в секунды для оси X
        times = x_axis.astype('int64') // 10**9
        values = income.values

        # Добавляем фиктивную точку в начало графика со значением 0
        if len(times) > 0:
            times = np.insert(times, 0, times[0])
            values = np.insert(values, 0, 0.0)

        init = 0
        value_min = values.min()
        value_max = values.max()

        # Приводим level к диапазону [0, 1] и обрезаем, если за его пределами
        if value_max != value_min:
            level = (init - value_min) / (value_max - value_min)
            level = max(0.0, min(1.0, level))  # Обрезаем до допустимого диапазона
        else:
            level = 0.5

        # Градиент от value_min до value_max с прозрачностью на уровне 0
        grad = QtGui.QLinearGradient(0, value_min, 0, value_max)
        grad.setColorAt(0.0, pg.mkColor('#F23645'))
        grad.setColorAt(level, QColor(0, 0, 0, 0))
        grad.setColorAt(1.0, pg.mkColor('#089981'))
        brush = QtGui.QBrush(grad)

        # Цвет линии на основе ColorMap
        cm = pg.ColorMap([0.0, 1.0], ['#F23645', '#089981'])
        pen0 = cm.getPen(span=(init - 0.5, init + 0.0), width=2)

        # Очищаем и рисуем
        self.daily_income_plot.clear()
        self.daily_income_plot.plot(times, values, fillLevel=init, brush=brush, pen=pen0, name=label)


    def plot_positions_pnl(self, positions):
        """Plot positions PnL scatter plot"""
        if not positions:
            return
            
        x_values = [] 
        y_values = [] 
        colors = []   
        
        position_number = 1
        for position in positions:
            if position['status'] == 'closed':
                x_values.append(position['closeTimestamp'].value // 10**9)
                pnl = float(position['pnl'])
                y_values.append(pnl)
                colors.append('#089981' if pnl >= 0 else '#F23645')
                position_number += 1
                
        for x, y, color in zip(x_values, y_values, colors):
            self.positions_plot.plot([x], [y],
                                   pen=None,
                                   symbol='o',
                                   symbolSize=8,
                                   symbolBrush=color,
                                   symbolPen=None)
                                   
        zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('gray', style=QtCore.Qt.DotLine))
        self.positions_plot.addItem(zero_line)







