from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
from pyqtgraph import TextItem, PlotDataItem, mkPen, mkBrush
from PyQt5.QtWidgets import QGraphicsRectItem, QGridLayout, QLabel, QWidget, QFrame
from datetime import datetime as dt
from PyQt5.QtGui import QFont, QColor, QLinearGradient, QBrush
from PyQt5.QtCore import QMargins

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

        super(PGCanvas, self).__init__(self.widget)

    def get_canvas(self):
        return self.widget

    def init_canvas(self, facecolor, textcolor):
        pg.setConfigOption('background', facecolor)
        pg.setConfigOption('foreground', textcolor)
        self.textcolor = textcolor
        self.facecolor = facecolor
        self.candlestick_plot.setBackground(facecolor)
        self.balance_plot.setBackground(facecolor)
        
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

    def plot_candlestick(self, ohlc_data):
        times = ohlc_data.index.astype('int64') // 10**9  # Преобразование в UNIX-время (секунды)
        
        for i, (index, row) in enumerate(ohlc_data.iterrows()):
            open = row['open']
            high = row['high']
            low = row['low']
            close = row['close']
            date = times[i]

            clr = '#089981' if close >= open else '#F23645'
            candle_width = 0.7 * (times[1] - times[0])
            shadow_width = candle_width / 10

            candle_item = QGraphicsRectItem(date - candle_width/2, open if close >= open else close,
                                                    candle_width, abs(open - close))
            candle_item.setPen(pg.mkPen(color = clr, width=1.5))
            candle_item.setBrush(pg.mkBrush(color = clr))
            self.candlestick_plot.addItem(candle_item)
            
            shadow_item = QGraphicsRectItem(date - shadow_width/2, low,
                                                    shadow_width, abs(high - low))
            shadow_item.setPen(pg.mkPen(color = clr, width=1.5))
            shadow_item.setBrush(pg.mkBrush(color = clr))
            self.candlestick_plot.addItem(shadow_item)

    def plot_balance(self, data):
        init = data['value'].iloc[0]
        cm = pg.ColorMap([0.0, 1.0], ['#089981', '#F23645'])
        pen = cm.getPen( span=(init+0.05,init-0.05), width=2 )
        level = (init - data['value'].min())/(data['value'].max() - data['value'].min())
        grad = QtGui.QLinearGradient(0, data['value'].min(), 0, data['value'].max())
        grad.setColorAt(0.0, pg.mkColor('#F23645'))
        grad.setColorAt(level, QColor(0, 0, 0, 0))
        grad.setColorAt(1, pg.mkColor('#089981'))
        brush = QtGui.QBrush(grad)
        self.balance_plot.plot(data['ts'].astype('int64') // 10**9, data['value'], fillLevel=init, brush=brush, pen=pen, name="Balance")

    def plot_indicators(self, ohlc_data, indicator_names):
        colors = ['#00FF10', '#FF0010', '#0505F0', '#A010A0']
        for i, ind_name in enumerate(indicator_names):
            if ind_name in ohlc_data.columns:
                if ohlc_data[ind_name].iloc[-1] > ohlc_data['close'].iloc[-1] * 0.7 and ohlc_data[ind_name].iloc[-1] < ohlc_data['close'].iloc[-1] * 1.3: 
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
                
                    # Надпись pnl
                    if position['pnl'] > 0:
                        pnl_text = TextItem(f"+{position['pnl']:.1f}\nclose", color=(150, 150, 150))
                    else:
                        pnl_text = TextItem(f"{position['pnl']:.2f}", color=(150, 150, 150))
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
                
                    # Надпись pnl
                    pnl_text = TextItem(f"{position['pnl']:.1f}", color=(150, 150, 150))
                    pnl_text.setFont(bold_font)
                    pnl_text.setAnchor((0.5, 1))
                    self.candlestick_plot.addItem(pnl_text)
                    pnl_text.setPos(xsc[-1], close_candle['high'] + padding)
                    
                    # Надпись close
                    close_text = TextItem("close", color=(150, 150, 150))
                    close_text.setFont(bold_font)
                    close_text.setAnchor((0.5, 1))
                    self.candlestick_plot.addItem(close_text)
                    close_text.setPos(xsc[-1], close_candle['high'] + padding*2)

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
            if position['pnl'] >= 0:
                gradient.setColorAt(0, QColor(8, 153, 129, 100))
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
            else:
                gradient.setColorAt(1, QColor(242, 54, 69, 100))
                gradient.setColorAt(0, QColor(0, 0, 0, 0))
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



