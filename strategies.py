from PyQt5.QtGui import *  # type: ignore
import pandas as pd # type: ignore
import numpy as np # type: ignore
import ta # type: ignore

class StrategyManager:
    def __init__(self, app):
        self.app = app

    def plot_macd(self, df):
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        self.app.canvas.ax2.plot(df.index, df['macd'], label='MACD', color='yellow', linestyle='--', alpha = 0.5)
        self.app.canvas.ax2.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', alpha = 0.5)

    def set_bar_value(self, value):
        self.app.bar.setValue(value)

    def close(self, transactions, current_balance, position_size, leverage, open_price, open_time, close_price, close_time, type, tp, sl):
        commission = self.app.commission

        if (close_price > open_price and type == 1) or (close_price < open_price and type == -1):
            result = 1
        else:
            result = 0

        if tp == sl == 0:  #режим когда тейкпрофита и стоплосса не было, а вместо этого сделка закрылась по значению какого-то индикатора
            if result == 1:
                tp = close_price
                sl = open_price
            else:
                tp = open_price
                sl = close_price

        pnl = position_size * (close_price-open_price)/open_price * leverage * type - position_size * commission * leverage
        transactions.append((tp, sl, position_size, open_price, open_time, close_time, close_price, type, result, pnl))
        current_balance += pnl            

        return transactions, current_balance
    
    def get_tp_sl(self, df, i, open_price, profit_factor, type, lookback):
        if type == 1:
            sl = 1000000
            for j in range (lookback):
                if sl > df['low'].iloc[i-j]:
                    sl = df['low'].iloc[i-j]
            tp = (open_price - sl) * profit_factor + open_price
        if type == -1:
            sl = 0
            for j in range (lookback):
                if sl < df['high'].iloc[i-j]:
                    sl = df['high'].iloc[i-j]
            tp = open_price - (sl - open_price) * profit_factor
        return tp, sl

    def Supertrend(self, df, atr_period, multiplier):
        high = df['high']
        low = df['low']
        close = df['close']
        
        # calculate ATR
        price_diffs = [high - low, 
                    high - close.shift(), 
                    close.shift() - low]
        true_range = pd.concat(price_diffs, axis=1)
        true_range = true_range.abs().max(axis=1)
        atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean() 

        hl2 = (high + low) / 2
        final_upperband = hl2 + (multiplier * atr)
        final_lowerband = hl2 - (multiplier * atr)
        
        # initialize Supertrend column to True
        supertrend = [True] * len(df)
        
        for i in range(1, len(df.index)):
            
            # if current close price crosses above upperband
            if close.iloc[i] > final_upperband.iloc[i-1]:
                supertrend[i] = True
            # if current close price crosses below lowerband
            elif close.iloc[i] < final_lowerband.iloc[i-1]: 
                supertrend[i] = False
            # else, the trend continues
            else:
                supertrend[i] = supertrend[i-1]
                
                # adjustment to the final bands
                if supertrend[i] == True and final_lowerband.iloc[i] < final_lowerband.iloc[i-1]:
                    final_lowerband.iloc[i] = final_lowerband.iloc[i-1]
                if supertrend[i] == False and final_upperband.iloc[i] > final_upperband.iloc[i-1]:
                    final_upperband.iloc[i] = final_upperband.iloc[i-1]

            # to remove bands according to the trend direction
            if supertrend[i] == True:
                final_upperband.iloc[i] = np.nan
            else:
                final_lowerband.iloc[i] = np.nan
        
        return pd.DataFrame({
            'Supertrend': supertrend,
            'Final Lowerband': final_lowerband,
            'Final Upperband': final_upperband
        }, index=df.index)

    def calculate_balance(self, df, transactions):
        current_balance = int(self.app.initial_balance)
        leverage = self.app.leverage
        balance = [[], []]
        i = 0
        for tp, sl, position_size, open_price, open_time, close_time, close_price, type, result, pnl in transactions:
            while df.index[i] <= open_time and df.index[i] < df.index[-1]:
                balance[0].append(current_balance)
                balance[1].append(df.index[i]) 
                i += 1
            while df.index[i] < close_time and df.index[i] < df.index[-1]:
                balance[0].append(current_balance+position_size*(df['close'].iloc[i]/open_price-1)*type*leverage)
                balance[1].append(df.index[i])  
                i += 1
            current_balance += pnl
            
        while df.index[i] < df.index[-1]:
            balance[0].append(current_balance)
            balance[1].append(df.index[i])  
            i += 1
        return balance

    def macd_strategy(self, df):
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        # Рисуем индикаторы
        self.plot_macd(df)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        profit_factor = self.app.profit_factor
        leverage = self.app.leverage
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl)
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl) 

            if not trade_open:
                if df['macd_signal'].iloc[i-1] < df['macd'].iloc[i] and df['macd_signal'].iloc[i] > df['macd'].iloc[i-1]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if df['macd_signal'].iloc[i-1] > df['macd'].iloc[i] and df['macd_signal'].iloc[i] < df['macd'].iloc[i-1]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True

        balance = self.calculate_balance(df, transactions)
        return transactions, balance

    def macd_v2_strategy(self, df):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        # Рисуем индикаторы
        self.plot_macd(df)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        profit_factor = self.app.profit_factor
        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl)
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl)

            if not trade_open:
                if df['macd_signal'].iloc[i-1] < df['macd_signal'].iloc[i-2] and df['macd_signal'].iloc[i] > df['macd_signal'].iloc[i-1]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if df['macd_signal'].iloc[i-1] > df['macd_signal'].iloc[i-2] and df['macd_signal'].iloc[i] < df['macd_signal'].iloc[i-1]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True

        balance = self.calculate_balance(df, transactions)
        return transactions, balance

    def macd_v3_strategy(self, df):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        # Рисуем индикаторы
        self.plot_macd(df)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if df['macd'].iloc[i-1] > df['macd'].iloc[i-2] and df['macd'].iloc[i] < df['macd'].iloc[i-1] and type == 1:
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['close'].iloc[i], df.index[i], type, 0, 0)        
                elif df['macd'].iloc[i-1] < df['macd'].iloc[i-2] and df['macd'].iloc[i] > df['macd'].iloc[i-1] and type == -1:
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['close'].iloc[i], df.index[i], type, 0, 0)  

            if not trade_open:
                if df['macd'].iloc[i-1] < df['macd'].iloc[i-2] and df['macd'].iloc[i] > df['macd'].iloc[i-1]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                if df['macd'].iloc[i-1] > df['macd'].iloc[i-2] and df['macd'].iloc[i] < df['macd'].iloc[i-1]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True

        balance = self.calculate_balance(df, transactions)
        return transactions, balance

    def macd_vwap_strategy(self, df):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        vwap = ta.volume.VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'], window = 200)
        df['vwap'] = vwap.vwap

        # Рисуем индикаторы
        self.app.canvas.ax2.plot(df.index, df['macd'], label='MACD', color='yellow', linestyle='--', alpha = 0.5)
        self.app.canvas.ax2.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', alpha = 0.5)
        self.app.canvas.ax1.plot(df.index, df['vwap'], label='VWAP', color='white', linestyle='--', alpha = 0.5)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        profit_factor = self.app.profit_factor
        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl)
                    trade_open = False

            if not trade_open:
                if (df['close'].iloc[i] > df['vwap'].iloc[i]) and df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if (df['close'].iloc[i] < df['vwap'].iloc[i]) and df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] < df['macd_signal'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True

        balance = self.calculate_balance(df, transactions)
        return transactions, balance

    def bollinger_vwap_strategy(self, df):
                
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        vwap = ta.volume.VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'], window = 200)
        df['vwap'] = vwap.vwap
        
        # Рисуем индикаторы
        self.app.canvas.ax1.plot(df.index, df['bollinger_high'], label='BB High', color='red', alpha = 0.5)
        self.app.canvas.ax1.plot(df.index, df['bollinger_low'], label='BB Low', color='green', alpha = 0.5)
        self.app.canvas.ax1.plot(df.index, df['vwap'], label='VWAP', color='orange', linestyle='--', alpha = 0.5)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if df['high'].iloc[i] >= df['bollinger_high'].iloc[i] and type == 1:
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['bollinger_high'].iloc[i], df.index[i], type, df['bollinger_high'].iloc[i], sl)
                    trade_open = False
                elif df['low'].iloc[i] <= df['bollinger_low'].iloc[i] and type == -1:
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['bollinger_low'].iloc[i], df.index[i], type, df['bollinger_low'].iloc[i], sl)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, open_price, sl)
                    trade_open = False

            else:
                if (df['close'].iloc[i] < df['bollinger_low'].iloc[i]) and \
                (df['close'].iloc[i-15:i+1] > df['vwap'].iloc[i-15:i+1]).all():
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1  # long
                    sl = open_price/1.01
                    trade_open = True
                elif (df['close'].iloc[i] > df['bollinger_high'].iloc[i]) and \
                    (df['close'].iloc[i-15:i+1] < df['vwap'].iloc[i-15:i+1]).all():
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1  # short
                    sl = open_price*1.01
                    trade_open = True

        balance = self.calculate_balance(df, transactions)
        return transactions, balance

    def bollinger_v2(self, df):
        # Убедиться, что все данные числовые
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

        # Расчитываем индикаторы
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()

        # Рисуем индикаторы
        self.app.canvas.ax1.plot(df.index, df['bollinger_high'], label='BB High', color='red', alpha = 0.5)
        self.app.canvas.ax1.plot(df.index, df['bollinger_low'], label='BB Low', color='green', alpha = 0.5)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        profit_factor = self.app.profit_factor
        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl)
                    trade_open = False

            else:
                if (df['low'].iloc[i] < df['bollinger_low'].iloc[i]) and (df['close'].iloc[i] > df['open'].iloc[i]):
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1  # long
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if (df['high'].iloc[i] > df['bollinger_high'].iloc[i]) and (df['close'].iloc[i] < df['open'].iloc[i]):
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1  # short
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    
        balance = self.calculate_balance(df, transactions)
        return transactions, balance  
    
    def supertrend_strategy(self, df):
        period = 10
        multiplier = 1

        # Calculate SuperTrend
        sti = self.Supertrend(df, period, multiplier)
        df = df.join(sti)
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        vwap = ta.volume.VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'], window = 500)
        df['vwap'] = vwap.vwap
        
        # Рисуем индикаторы
        #self.app.canvas.ax2.plot(df.index, df['Supertrend'], label='SuperTrend', color='yellow', linestyle='--', alpha=0.5)
        self.app.canvas.ax1.plot(df.index, df['Final Lowerband'], label='Final Lowerband', color='green', linestyle='--', alpha=0.5)
        self.app.canvas.ax1.plot(df.index, df['Final Upperband'], label='Final Upperband', color='red', linestyle='--', alpha=0.5)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if df['Supertrend'].iloc[i-1] != df['Supertrend'].iloc[i]:
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['close'].iloc[i], df.index[i], type, 0, 0)
                    trade_open = False

            if not trade_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True

        balance = self.calculate_balance(df, transactions)

        """
        wins = 0
        losses = 0
        winrate = 0
        for tp, sl, open_price, open_time, close_time, close_price, type, result in transactions:
            if result == 1:
                wins += 1
            else:
                losses += 1
        if wins+losses == 0:
            winrate = 0
        else:
            winrate = round(wins/(wins+losses)*100, ndigits=2)
        profit = round((balance[0][-1]-balance[0][0])/balance[0][0]*100, ndigits=2)

        
        print(str('period: ' + str(period)))
        print(str('multiplier: ' + str(multiplier)))

        print(str('Profit: ' + str(profit)))
        print(str('Winrate: ' + str(winrate)))
        print(str('Trades: ' + str(wins+losses)+'\n'))
        """

        return transactions, balance

    def supertrend_v2(self, df):
        period = 12
        multiplier = 3

        # Calculate SuperTrend
        sti = self.Supertrend(df, period, multiplier)
        sti2 = self.Supertrend(df, 11, 2)
        sti3 = self.Supertrend(df, 10, 1)

        df2 = df
        df3 = df
        
        df = df.join(sti)
        df2 = df2.join(sti2)
        df3 = df3.join(sti3)

        """
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        vwap = ta.volume.VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'], window = 500)
        df['vwap'] = vwap.vwap
        
        # Рисуем индикаторы
        self.app.canvas.ax1.plot(df.index, df['bollinger_high'], label='BB High', color='white', alpha = 0.5)
        self.app.canvas.ax1.plot(df.index, df['bollinger_low'], label='BB Low', color='white', alpha = 0.5)
        self.app.canvas.ax1.plot(df.index, df['vwap'], label='VWAP', color='orange', linestyle='--', alpha = 0.5)
        self.app.canvas.ax2.plot(df.index, df['macd'], label='Macd', color='white', alpha = 0.5)
        self.app.canvas.ax2.plot(df.index, df['macd_signal'], label='Macd signal', color='blue', alpha = 0.5)
        self.app.canvas.ax2.plot(df.index, df['Supertrend'], label='SuperTrend', color='yellow', linestyle='--', alpha=0.5)        
        """
        self.app.canvas.ax1.plot(df.index, df['Final Lowerband'], label='Final Lowerband 1', color='green', linestyle='--', alpha=0.5)
        self.app.canvas.ax1.plot(df.index, df['Final Upperband'], label='Final Upperband 1', color='red', linestyle='--', alpha=0.5)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
                    close_price = df['Final Lowerband'].iloc[i-1]
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0)
                    trade_open = False
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:
                    close_price = df['Final Upperband'].iloc[i-1]
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0)
                    trade_open = False

            if not trade_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True

        balance = self.calculate_balance(df, transactions)
        return transactions, balance
    
    def supertrend_v3(self, df):
        good_deal = 3.3
        antishtraf = 0.09
        period = 10
        multiplier = 2

        # Calculate SuperTrend
        sti = self.Supertrend(df, period, multiplier)
        df = df.join(sti)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        self.app.canvas.ax1.plot(df.index, df['close'], label='price', color='white', alpha=0.5)

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
                    close_price = df['Final Lowerband'].iloc[i-1]
                    transactions, current_balance = self.close(balance, transactions, current_balance, position_size * shtraf, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0)
                    trade_open = False
                    if shtraf < 1:
                        shtraf += antishtraf
                    if close_price / open_price > (1+good_deal/100) and type == 1 or close_price / open_price < (1-good_deal/100) and type == -1:
                        shtraf = 0
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:
                    close_price = df['Final Upperband'].iloc[i-1]
                    transactions, current_balance = self.close(balance, transactions, current_balance, position_size * shtraf, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0)
                    trade_open = False
                    if shtraf < 1:
                        shtraf += antishtraf
                    if close_price / open_price > (1+good_deal/100) and type == 1 or close_price / open_price < (1-good_deal/100) and type == -1:
                        shtraf = 0

            if not trade_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True

        balance = self.calculate_balance(df, transactions)         
        return transactions, balance

    def hawkes_process_strategy(self, df):

        lookback = 168
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=lookback, fillna=False).average_true_range()
        df['norm_range'] = (df['high'] - df['low']) / df['atr']
        #self.app.canvas.ax2.plot(df.index, df['norm_range'], label='norm_range', color='white', alpha=0.5)

        kappa = 0.1
        alpha = np.exp(-kappa)
        df['hawkes'] = df['norm_range']

        for i in range(lookback, len(df)):
            df['hawkes'].iloc[i] += df['hawkes'].iloc[i-1] * alpha
        df['hawkes'] *= kappa

        #self.app.canvas.ax2.plot(df.index, df['norm_range'], label='norm_range', color='white', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['hawkes'], label='hawkes', color='yellow', alpha=0.5)
        
        df['q05'] = df['hawkes'].rolling(lookback).quantile(0.05)
        df['q95'] = df['hawkes'].rolling(lookback).quantile(0.95)

        vwap = ta.volume.VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'], window = 200)
        df['vwap'] = vwap.vwap
        
        self.app.canvas.ax1.plot(df.index, df['vwap'], label='VWAP', color='orange', linestyle='--', alpha = 0.5)

        self.app.canvas.ax2.plot(df.index, df['q05'], label='q05', color='red', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['q95'], label='q95', color='green', alpha=0.5)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        profit_factor = self.app.profit_factor
        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl)
                    was_below = 0
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl)
                    was_below = 0
                    trade_open = False

            if was_below > 0 and not trade_open:
                if df['hawkes'].iloc[i] >= df['q95'].iloc[i] and df['close'].iloc[was_below] < df['close'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if df['hawkes'].iloc[i] >= df['q95'].iloc[i] and df['close'].iloc[was_below] > df['close'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    
            if not trade_open:
                if df['hawkes'].iloc[i] < df['q05'].iloc[i]:
                   was_below = i

        balance = self.calculate_balance(df, transactions)
        return transactions, balance

    def dca_strategy(self, df):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        period = 12
        multiplier = 3
        sti = self.Supertrend(df, period, multiplier)
        df = df.join(sti)

        self.app.canvas.ax1.plot(df.index, df['Final Lowerband'], label='Final Lowerband', color='green', linestyle='--', alpha=0.5)
        self.app.canvas.ax1.plot(df.index, df['Final Upperband'], label='Final Upperband', color='red', linestyle='--', alpha=0.5)

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        open_price = []
        orders = 20
        order_num = 0
        mid_open_price = 0
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    for j in range (0, order_num):
                        transactions, current_balance = self.close(balance, transactions, current_balance, position_sizes[j], leverage, open_price[j], open_time[j], tp, df.index[i], type, 0, 0)
                    trade_open = False
                    open_price = []
                    position_size = []
                    open_time = []
                    mid_open_price = 0
                    order_num = 0

            if not trade_open:
                if df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price.append(df['close'].iloc[i])
                    mid_open_price = df['close'].iloc[i]
                    for j in range (orders-1):
                        open_price.append(open_price[-1]*0.98)
                        position_sizes.append(position_size/orders)
                    open_time.append(df.index[i])
                    type = 1
                    tp = mid_open_price * 1.01
                    trade_open = True
                    order_num = 1
                
                elif df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] < df['macd_signal'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price.append(df['close'].iloc[i])
                    mid_open_price = df['close'].iloc[i]
                    for j in range (orders):
                        open_price.append(open_price[-1]*1.01)
                        position_sizes.append(position_size/orders)
                    open_time.append(df.index[i]) 
                    type = -1
                    tp = mid_open_price * 0.99
                    trade_open = True
                    order_num = 1

            if order_num < orders - 1 and trade_open:
                if df['close'].iloc[i] < open_price[order_num] and type == 1:
                    order_num += 1   
                    mid_open_price = 0
                    for j in range (0, order_num):
                        mid_open_price += open_price[j] * position_sizes[j]
                    mid_open_price /= order_num
                    mid_open_price *= orders
                    open_time.append(df.index[i])
                    tp = mid_open_price * 1.01
                elif df['close'].iloc[i] > open_price[order_num] and type == -1:
                    order_num += 1
                    mid_open_price = 0
                    for j in range (0, order_num):
                        mid_open_price += open_price[j] * position_sizes[j]
                    mid_open_price /= order_num
                    mid_open_price *= orders
                    open_time.append(df.index[i])
                    tp = mid_open_price * 0.99               

            if order_num == orders - 1:
                for j in range (0, order_num):
                    transactions, current_balance = self.close(balance, transactions, current_balance, position_sizes[j], leverage, open_price[j], open_time[j], df['close'].iloc[i], df.index[i], type, 0, 0)
                trade_open = False
                open_price = []
                position_sizes = []
                open_time = []
                mid_open_price = 0
                order_num = 0
        
        balance = self.calculate_balance(df, transactions)
        return transactions, balance
        
    def rsi_strategy(self, df):

        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()

        self.app.canvas.ax2.plot(df.index, df['rsi'], label='rsi', color='white', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['atr'], label='atr', color='yellow', alpha=0.5)
        self.app.canvas.draw()
        self.app.show()

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        profit_factor = self.app.profit_factor
        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl)
                    trade_open = False       
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl)
                    trade_open = False

            if not trade_open:
                if df['rsi'].iloc[i-1] < 30 and df['rsi'].iloc[i] >= 30:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if df['rsi'].iloc[i-1] > 70 and df['rsi'].iloc[i] <= 70:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True

        balance = self.calculate_balance(df, transactions)
        return transactions, balance

    def ma50200_cross_strategy(self, df):

        #df['ma50'] = (df['close'].rolling(window=50, closed='right').mean() / df['close'].rolling(window=50, closed='left').mean() - 1)  * 50
        #df['ma200'] = (df['close'].rolling(window=200, closed='right').mean() / df['close'].rolling(window=200, closed='left').mean() - 1) * 200

        df['ma50'] = df['close'].rolling(window=50).mean()
        df['ma200'] = df['close'].rolling(window=200).mean()

        self.app.canvas.ax1.plot(df.index, df['ma50'], label='ma 50', color='green', alpha=0.5)
        self.app.canvas.ax1.plot(df.index, df['ma200'], label='ma 200', color='red', alpha=0.5)
        self.app.canvas.draw()
        self.app.show()

        if self.app.position_type == "percent":
            position_size = self.app.position_size / 100 * current_balance
        else:
            position_size = self.app.position_size

        profit_factor = self.app.profit_factor
        leverage = self.app.leverage
        current_balance = self.app.initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.set_bar_value(int(i / len(df) * 100))
                
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl)
                    trade_open = False           
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl)
                    trade_open = False

            if not trade_open:
                if df['ma50'].iloc[i-1] < df['ma200'].iloc[i-1] and df['ma50'].iloc[i] >= df['ma200'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if df['ma50'].iloc[i-1] > df['ma200'].iloc[i-1] and df['ma50'].iloc[i] <= df['ma200'].iloc[i]:
                    if self.app.position_type == "percent":
                        position_size = self.app.position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True

        balance = self.calculate_balance(df, transactions)
        return transactions, balance


