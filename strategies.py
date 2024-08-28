from PyQt5.QtGui import *  # type: ignore
import pandas as pd # type: ignore
import numpy as np # type: ignore
import ta # type: ignore

class StrategyManager:
    def __init__(self, app):
        self.app = app

    def close(self, balance, transactions, current_balance, position_size, leverage, open_price, open_time, close_price, close_time, type, tp, sl, commission):
        
        if (close_price > open_price and type == 1) or (close_price < open_price and type == -1):
            result = 1
        else:
            result = 0

        if tp == sl == 0:
            if result == 1:
                tp = close_price
                sl = open_price
            else:
                tp = open_price
                sl = close_price
        
        if type == 1:
            transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
            current_balance -= current_balance * position_size * commission * leverage
            current_balance += current_balance * position_size * (close_price-open_price)/open_price * leverage
            balance[0].append(current_balance)
            balance[1].append(close_time)
            
        if type == -1:
            transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
            current_balance -= current_balance * position_size * commission * leverage 
            current_balance += current_balance * position_size * (open_price - close_price)/open_price * leverage 
            balance[0].append(current_balance)
            balance[1].append(close_time)

        return transactions, balance, current_balance
    
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

    def macd_strategy(self, df):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        # Рисуем индикаторы
        self.app.canvas.ax2.plot(df.index, df['macd'], label='MACD', color='yellow', linestyle='--', alpha = 0.5)
        self.app.canvas.ax2.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', alpha = 0.5)

        transactions = []
        profit_factor = 1.5
        profit_percent = 3
        open_price = 0
        open_time = 0
        type = 1 # 1 - long, -1 - short
        current_balance = 100
        balance = [[],[]]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 1
        trade_open = False 
        percent = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    close_price = tp
                    close_time = df.index[i]
                    result = 1
                    trade_open = False
                    transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                    current_balance -= current_balance * position_size * 0.0008
                    current_balance += current_balance*position_size*(close_price-open_price)/open_price
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    close_price = sl
                    close_time = df.index[i]
                    result = 0
                    trade_open = False
                    transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                    current_balance -= current_balance * position_size * 0.0008
                    current_balance -= current_balance*position_size*(close_price - open_price)/open_price
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                else:
                    balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type)
                    balance[1].append(df.index[i])  

            if not trade_open:
                if df['macd_signal'].iloc[i-1] < df['macd'].iloc[i] and df['macd_signal'].iloc[i] > df['macd'].iloc[i-1]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i]) 
                if df['macd_signal'].iloc[i-1] > df['macd'].iloc[i] and df['macd_signal'].iloc[i] < df['macd'].iloc[i-1]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
        return transactions, balance

    def macd_v2_strategy(self, df):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        # Рисуем индикаторы
        self.app.canvas.ax2.plot(df.index, df['macd'], label='MACD', color='yellow', linestyle='--', alpha = 0.5)
        self.app.canvas.ax2.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', alpha = 0.5)

        transactions = []
        profit_factor = 1.5
        profit_percent = 3
        open_price = 0
        open_time = 0
        type = 1 # 1 - long, -1 - short
        current_balance = 100
        balance = [[],[]]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 1
        trade_open = False 
        percent = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    close_price = tp
                    close_time = df.index[i]
                    result = 1
                    trade_open = False
                    transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                    current_balance -= current_balance * position_size * 0.0008
                    current_balance += current_balance*position_size*(close_price-open_price)/open_price
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    close_price = sl
                    close_time = df.index[i]
                    result = 0
                    trade_open = False
                    transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                    current_balance -= current_balance * position_size * 0.0008
                    current_balance -= current_balance*position_size*(close_price - open_price)/open_price
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                else:
                    balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type)
                    balance[1].append(df.index[i])  

            if not trade_open:
                if df['macd_signal'].iloc[i-1] < df['macd_signal'].iloc[i-2] and df['macd_signal'].iloc[i] > df['macd_signal'].iloc[i-1]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i]) 
                if df['macd_signal'].iloc[i-1] > df['macd_signal'].iloc[i-2] and df['macd_signal'].iloc[i] < df['macd_signal'].iloc[i-1]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
        return transactions, balance

    def macd_v3_strategy(self, df):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        self.app.canvas.ax2.plot(df.index, df['macd'], label='MACD', color='yellow', linestyle='--', alpha = 0.5)
        self.app.canvas.ax2.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', alpha = 0.5)

        transactions = []
        open_price = 0
        open_time = 0
        type = 1 # 1 - long, -1 - short
        current_balance = 100
        balance = [[],[]]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 1
        trade_open = False 

        percent = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if df['macd'].iloc[i-1] > df['macd'].iloc[i-2] and df['macd'].iloc[i] < df['macd'].iloc[i-1] and type == 1:
                    close_price = df['close'].iloc[i]
                    close_time = df.index[i]
                    if close_price > open_price:
                        result = 1
                        tp = close_price
                        sl = open_price
                    else:
                        result = 0
                        tp = open_price
                        sl = close_price
                    trade_open = False
                    transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                    current_balance -= current_balance * position_size * 0.0008
                    current_balance += current_balance*position_size*(close_price-open_price)/open_price
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                elif df['macd'].iloc[i-1] < df['macd'].iloc[i-2] and df['macd'].iloc[i] > df['macd'].iloc[i-1] and type == -1:
                    close_price = df['close'].iloc[i]
                    close_time = df.index[i]
                    if close_price < open_price:
                        result = 1
                        tp = close_price
                        sl = open_price
                    else:
                        result = 0
                        tp = open_price
                        sl = close_price
                    trade_open = False
                    transactions.append((tp, sl, open_price, open_time, close_time, close_price, type, result))
                    current_balance -= current_balance * position_size * 0.0008
                    current_balance -= current_balance*position_size*(close_price - open_price)/open_price
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                else:
                    balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type)
                    balance[1].append(df.index[i])  

            if not trade_open:
                if df['macd'].iloc[i-1] < df['macd'].iloc[i-2] and df['macd'].iloc[i] > df['macd'].iloc[i-1]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i]) 
                if df['macd'].iloc[i-1] > df['macd'].iloc[i-2] and df['macd'].iloc[i] < df['macd'].iloc[i-1]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
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

        transactions = []
        profit_factor = 1.5
        open_price = 0
        open_time = 0
        type = 1 # 1 - long, -1 - short
        current_balance = 100
        balance = [[],[]]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 1
        leverage = 2
        trade_open = False 
        percent = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, 0.0008)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, 0.0008)
                    trade_open = False
                else:
                    balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type*leverage)
                    balance[1].append(df.index[i])  

            if not trade_open:
                if (df['close'].iloc[i] > df['vwap'].iloc[i]) and df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i]) 
                if (df['close'].iloc[i] < df['vwap'].iloc[i]) and df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] < df['macd_signal'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
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

        transactions = []
        current_balance = 100
        balance = [[], []]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 1
        trade_open = False
        open_price = 0
        open_time = 0
        profit_factor = 1.5
        leverage = 2
        sl = 0
        type = 0  # 1 - long, -1 - short
        percent = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= df['bollinger_high'].iloc[i] and type == 1) or (df['low'].iloc[i] <= df['bollinger_low'].iloc[i] and type == -1):
                    if type == 1:
                        transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, df['bollinger_high'].iloc[i], df.index[i], type, df['bollinger_high'].iloc[i], sl, 0.0008)
                    if type == -1:
                        transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, df['bollinger_low'].iloc[i], df.index[i], type, df['bollinger_low'].iloc[i], sl, 0.0008)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, open_price, sl, 0.0008)
                    trade_open = False
                else:
                    balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type*leverage)
                    balance[1].append(df.index[i])  
            else:
                if (df['close'].iloc[i] < df['bollinger_low'].iloc[i]) and \
                (df['close'].iloc[i-15:i+1] > df['vwap'].iloc[i-15:i+1]).all():
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1  # long
                    sl = open_price/1.01
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                
                elif (df['close'].iloc[i] > df['bollinger_high'].iloc[i]) and \
                    (df['close'].iloc[i-15:i+1] < df['vwap'].iloc[i-15:i+1]).all():
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1  # short
                    sl = open_price*1.01
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
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

        transactions = []
        current_balance = 100
        balance = [[], []]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 1
        trade_open = False
        open_price = 0
        open_time = 0
        profit_factor = 1.5
        leverage = 2
        tp = 0
        sl = 0
        type = 0  # 1 - long, -1 - short
        percent = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, 0.0008)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, 0.0008)
                    trade_open = False
                else:
                    balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type*leverage)
                    balance[1].append(df.index[i])   
            else:
                if (df['low'].iloc[i] < df['bollinger_low'].iloc[i]) and (df['close'].iloc[i] > df['open'].iloc[i]):
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1  # long
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                
                if (df['high'].iloc[i] > df['bollinger_high'].iloc[i]) and (df['close'].iloc[i] < df['open'].iloc[i]):
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1  # short
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
        return transactions, balance
    

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
        self.app.canvas.ax1.plot(df2.index, df2['Final Lowerband'], label='Final Lowerband 2', color='green', linestyle='--', alpha=0.5)
        self.app.canvas.ax1.plot(df2.index, df2['Final Upperband'], label='Final Upperband 2', color='red', linestyle='--', alpha=0.5)
        self.app.canvas.ax1.plot(df3.index, df3['Final Lowerband'], label='Final Lowerband 3', color='green', linestyle='--', alpha=0.5)
        self.app.canvas.ax1.plot(df3.index, df3['Final Upperband'], label='Final Upperband 3', color='red', linestyle='--', alpha=0.5)

        transactions = []
        open_price = 0
        open_time = 0
        type = 1  # 1 - long, -1 - short
        current_balance = 100
        balance = [[], []]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 0.5
        shtraf = 1
        leverage = 5
        trade_open = False
        percent5 = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent5 == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
                    print (shtraf)
                    close_price = df['Final Lowerband'].iloc[i-1]
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size * shtraf, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0, 0.0008)
                    trade_open = False
                    if shtraf < 1:
                        shtraf += 0.2
                    if close_price / open_price > 1.02 and type == 1 or close_price / open_price < 0.98 and type == -1:
                        shtraf = 0
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:
                    close_price = df['Final Upperband'].iloc[i-1]
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0, 0.0008)
                    trade_open = False
                else:
                    balance[0].append(current_balance + current_balance * position_size * ((df['open'].iloc[i] + df['close'].iloc[i]) / 2 / open_price - 1) * type * leverage)
                    balance[1].append(df.index[i])

            if not trade_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])

        
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

        transactions = []
        open_price = 0
        open_time = 0
        type = 1
        current_balance = 100
        position_size = 1
        leverage = 2
        trade_open = False
        balance = [[current_balance], [df.index[0]]]
        percent = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if df['Supertrend'].iloc[i-1] != df['Supertrend'].iloc[i]:
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, df['close'].iloc[i], df.index[i], type, 0, 0, 0.0008)
                    trade_open = False
                else:
                    balance[0].append(current_balance + current_balance * position_size * ((df['open'].iloc[i] + df['close'].iloc[i]) / 2 / open_price - 1) * type * leverage)
                    balance[1].append(df.index[i])

            if not trade_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])

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

        transactions = []
        open_price = 0
        open_time = 0
        type = 1  # 1 - long, -1 - short
        current_balance = 100
        balance = [[], []]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 0.5
        shtraf = 1
        leverage = 5
        trade_open = False
        percent5 = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent5 == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
                    close_price = df['Final Lowerband'].iloc[i-1]
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0, 0.0008)
                    trade_open = False
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:
                    close_price = df['Final Upperband'].iloc[i-1]
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0, 0.0008)
                    trade_open = False
                else:
                    balance[0].append(current_balance + current_balance * position_size * ((df['open'].iloc[i] + df['close'].iloc[i]) / 2 / open_price - 1) * type * leverage)
                    balance[1].append(df.index[i])

            if not trade_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])

        
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
        

        return transactions, balance
    
    def supertrend_v3(self, df):
        good_deal = 3.3
        antishtraf = 0.09
        period = 10
        multiplier = 2

        # Calculate SuperTrend
        sti = self.Supertrend(df, period, multiplier)
        df = df.join(sti)

        transactions = []
        open_price = 0
        open_time = 0
        type = 1  # 1 - long, -1 - short
        current_balance = 100
        balance = [[], []]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 0.5
        shtraf = 1
        leverage = 5
        trade_open = False
        percent5 = int(len(df) / 50)

        self.app.canvas.ax1.plot(df.index, df['close'], label='price', color='white', alpha=0.5)

        for i in range(len(df)):
            if i % percent5 == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:

                    close_price = df['Final Lowerband'].iloc[i-1]
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size * shtraf, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0, 0.0008)
                    trade_open = False
                    if shtraf < 1:
                        shtraf += antishtraf
                    if close_price / open_price > (1+good_deal/100) and type == 1 or close_price / open_price < (1-good_deal/100) and type == -1:
                        shtraf = 0
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:

                    close_price = df['Final Upperband'].iloc[i-1]
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size * shtraf, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0, 0.0008)
                    trade_open = False
                    if shtraf < 1:
                        shtraf += antishtraf
                    if close_price / open_price > (1+good_deal/100) and type == 1 or close_price / open_price < (1-good_deal/100) and type == -1:
                        shtraf = 0
                else:
                    balance[0].append(current_balance + current_balance * position_size * ((df['open'].iloc[i] + df['close'].iloc[i]) / 2 / open_price - 1) * type * leverage)
                    balance[1].append(df.index[i])

            if not trade_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
            
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

        transactions = []
        open_price = 0
        open_time = 0
        type = 1
        current_balance = 100
        position_size = 1
        leverage = 2
        profit_factor = 1.4
        was_below = 0
        trade_open = False
        balance = [[current_balance], [df.index[0]]]
        percent = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, 0.0008)
                    was_below = 0
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, 0.0008)
                    was_below = 0
                    trade_open = False
                else:
                    balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type* leverage)
                    balance[1].append(df.index[i])  

            if was_below > 0 and not trade_open:
                if df['hawkes'].iloc[i] >= df['q95'].iloc[i] and df['close'].iloc[was_below] < df['close'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i]) 
                if df['hawkes'].iloc[i] >= df['q95'].iloc[i] and df['close'].iloc[was_below] > df['close'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])
                    
            if not trade_open:
                if df['hawkes'].iloc[i] < df['q05'].iloc[i]:
                   was_below = i

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

        transactions = []
        profit_factor = 1.5
        open_price = []
        orders = 20
        order_num = 0
        open_time = []
        type = 1 # 1 - long, -1 - short
        current_balance = 100
        balance = [[],[]]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = []
        leverage = 4
        trade_open = False 
        percent = int(len(df) / 50)
        mid_open_price = 0
        tp = 0

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    for j in range (0, order_num):
                        transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size[j], leverage, open_price[j], open_time[j], tp, df.index[i], type, 0, 0, 0.0008)
                    trade_open = False
                    open_price = []
                    position_size = []
                    open_time = []
                    mid_open_price = 0
                    order_num = 0
                else:
                    balance[0].append(current_balance+current_balance*(order_num/orders)*(df['close'].iloc[i]/mid_open_price-1)*type*leverage)
                    balance[1].append(df.index[i])  

            if not trade_open:
                if df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                    open_price.append(df['close'].iloc[i])
                    mid_open_price = df['close'].iloc[i]
                    for j in range (orders-1):
                        open_price.append(open_price[-1]*0.98)
                        position_size.append(1/orders)
                    open_time.append(df.index[i])
                    type = 1
                    tp = mid_open_price * 1.01
                    trade_open = True
                    order_num = 1
                
                elif df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] < df['macd_signal'].iloc[i]:
                    open_price.append(df['close'].iloc[i])
                    mid_open_price = df['close'].iloc[i]
                    for j in range (orders):
                        open_price.append(open_price[-1]*1.01)
                        position_size.append(1/orders)
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
                        mid_open_price += open_price[j] * position_size[j]
                    mid_open_price /= order_num
                    mid_open_price *= orders
                    open_time.append(df.index[i])
                    tp = mid_open_price * 1.01
                elif df['close'].iloc[i] > open_price[order_num] and type == -1:
                    order_num += 1
                    mid_open_price = 0
                    for j in range (0, order_num):
                        mid_open_price += open_price[j] * position_size[j]
                    mid_open_price /= order_num
                    mid_open_price *= orders
                    open_time.append(df.index[i])
                    tp = mid_open_price * 0.99               

            if order_num == orders - 1:
                for j in range (0, order_num):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size[j], leverage, open_price[j], open_time[j], df['close'].iloc[i], df.index[i], type, 0, 0, 0.0008)
                trade_open = False
                open_price = []
                position_size = []
                open_time = []
                mid_open_price = 0
                order_num = 0
        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
        return transactions, balance
    
    def supertrend_v4(self, df):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        # Рисуем индикаторы
        self.app.canvas.ax2.plot(df.index, df['macd'], label='MACD', color='yellow', linestyle='--', alpha = 0.5)
        self.app.canvas.ax2.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', alpha = 0.5)

        transactions = []
        profit_factor = 1.5
        open_price = 0
        open_time = 0
        type = 1 # 1 - long, -1 - short
        current_balance = 100
        balance = [[],[]]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 1
        leverage = 2
        trade_open = False 
        percent = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, 0.0008)
                    trade_open = False
                    
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, 0.0008)
                    trade_open = False

                else:
                    balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type*leverage)
                    balance[1].append(df.index[i])  

            if not trade_open:
                if df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i]) 
                if df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] < df['macd_signal'].iloc[i]:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
        return transactions, balance
    

    def rsi_strategy(self, df):

        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()

        self.app.canvas.ax2.plot(df.index, df['rsi'], label='rsi', color='white', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['atr'], label='atr', color='yellow', alpha=0.5)
        self.app.canvas.draw()
        self.app.show()

        transactions = []
        profit_factor = 1.4
        open_price = 0
        open_time = 0
        type = 1 # 1 - long, -1 - short
        current_balance = 100
        balance = [[],[]]
        balance[0].append(current_balance)
        balance[1].append(df.index[0])
        position_size = 1
        leverage = 2
        trade_open = False 
        percent = int(len(df) / 50)

        for i in range(len(df)):
            if i % percent == 0:
                self.app.bar.setValue(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, 0.0008)
                    trade_open = False
                    
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, balance, current_balance = self.close(balance, transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, 0.0008)
                    trade_open = False

                else:
                    balance[0].append(current_balance+current_balance*position_size*((df['open'].iloc[i]+df['close'].iloc[i])/2/open_price-1)*type*leverage)
                    balance[1].append(df.index[i])  

            if not trade_open:
                if df['rsi'].iloc[i-1] < 30 and df['rsi'].iloc[i] >= 30:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i]) 
                if df['rsi'].iloc[i-1] > 70 and df['rsi'].iloc[i] <= 70:
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    balance[0].append(current_balance)
                    balance[1].append(df.index[i])

        balance[0].append(current_balance)
        balance[1].append(df.index[-1])
        return transactions, balance
