import inspect
from PyQt5.QtGui import *  # type: ignore
import pandas as pd # type: ignore
import numpy as np # type: ignore
import ta # type: ignore
from PyQt5.QtCore import QThread, pyqtSignal # type: ignore
import pickle
from PyQt5.QtWidgets import QFileDialog
import textwrap


class StrategyManager(QThread):
    # Сигнал завершения расчета
    calculation_complete = pyqtSignal(object, object, object)
    # Сигнал обновления прогресс-бара
    progress_changed = pyqtSignal(int)

    export_complete = pyqtSignal()

    def __init__(self, parent=None):
        super(StrategyManager, self).__init__(parent)
 
    def __init__(self, strat_name, df, initial_balance, position_size, position_type, profit_factor, leverage, commission, parent=None):
        super(StrategyManager, self).__init__(parent)
        self.profit_factor = float(profit_factor)
        self.leverage = leverage
        self.initial_balance = initial_balance
        self.position_type = position_type
        self.position_size = position_size
        self.df = df
        self.strat_name = strat_name
        self.commission = commission

    def run(self, mode="run"):
        if mode == "run":
            self.run_strategy()
        elif mode == "export":
            self.export_strategy()
        elif mode == "import":
            self.import_strategy()
        else:
            print("Неверный режим")

    def find(self, strat_name):
        current_strategy = self.macd_strategy
        if strat_name == "MACD":
            current_strategy = self.macd_strategy
        elif strat_name == "MACD v2":
            current_strategy = self.macd_v2_strategy
        elif strat_name == "Bollinger + VWAP":
            current_strategy = self.bollinger_vwap_strategy
        elif strat_name == "Bollinger v2":
            current_strategy = self.bollinger_v2
        elif strat_name == "Supertrend":
            current_strategy = self.supertrend_strategy
        elif strat_name == "Triple Supertrend":
            current_strategy = self.triple_supertrend
        elif strat_name == "MACD v3":
            current_strategy = self.macd_v3_strategy
        elif strat_name == "MACD VWAP":
            current_strategy = self.macd_vwap_strategy
        elif strat_name == "Hawkes Process":
            current_strategy = self.hawkes_process_strategy
        elif strat_name == "Supertrend v3 SOLANA 1H SETUP":
            current_strategy = self.supertrend_v3
        elif strat_name == "DCA":
            current_strategy = self.dca_strategy
        elif strat_name == "RSI":
            current_strategy = self.rsi_strategy
        elif strat_name == "MA-50 cross MA-200":
            current_strategy = self.ma50200_cross_strategy

        return current_strategy

    def run_strategy(self):
        current_strategy = self.find(self.strat_name)

        if self.position_type == "percent":
            self.position_size = self.position_size / 100 * self.initial_balance
        else:
            self.position_size = self.position_size

        transactions, balance, indicators = current_strategy(self.df, self.initial_balance, self.position_size, self.position_type, self.profit_factor, self.leverage, self.commission)
        self.calculation_complete.emit(transactions, balance, indicators)


    def export_strategy(self):
        current_strategy = self.find(self.strat_name)
        file_path, _ = QFileDialog.getSaveFileName(None, "Save Strategy as Text", "", "Python Files (*.py);;All Files (*)")

        if file_path:
            strategy_code = inspect.getsource(current_strategy)
            dedented_code = textwrap.dedent(strategy_code)
            # Сохраняем текст стратегии
            with open(file_path, 'w') as file:
                file.write(dedented_code)
            print(f"Strategy saved to {file_path}")
        else:
            print("Saving cancelled")

    def load_strategy(self, file_path):
        with open(file_path, 'r') as file:
            strategy_code = file.read()
        # Компилируем код стратегии
        compiled_code = compile(strategy_code, filename=file_path, mode='exec')
        # Локальное пространство имен для выполнения кода
        local_namespace = {}
        # Выполняем код стратегии в локальном пространстве имен
        exec(compiled_code, globals(), local_namespace)

        return local_namespace



    def import_strategy(self):
        """Импортирует стратегию из файла и запускает её"""
        file_path, _ = QFileDialog.getOpenFileName(None, "Open Strategy", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            strategy_namespace = self.load_strategy(file_path)
            # Ищем первую функцию в загруженном коде
            strategy_function = self.get_first_function(strategy_namespace)
            if strategy_function:
                self.strategy = strategy_function
                self.run_strategy()  # Запускаем импортированную стратегию
            else:
                print("Функция стратегии не найдена в файле")
        else:
            print("Открытие отменено")

    def load_strategy(self, file_path):
        """Загружает стратегию из .py файла"""
        strategy_namespace = {}
        with open(file_path, 'r') as file:
            strategy_code = file.read()
            compiled_code = compile(strategy_code, filename=file_path, mode='exec')
            exec(compiled_code, strategy_namespace)
        return strategy_namespace

    def get_first_function(self, namespace):
        """Возвращает первую функцию из загруженного пространства имён"""
        for name, obj in namespace.items():
            if callable(obj):  # Ищем первую функцию
                return obj
        return None



    def close(self, transactions, current_balance, position_size, leverage, open_price, open_time, close_price, close_time, type, tp, sl, commission):

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
    
    def get_tp_sl(self, df, i, open_price, profit_factor, order_type, lookback):
        if order_type == 1:
            sl = 1000000
            for j in range (lookback):
                if sl > df['low'].iloc[i-j]:
                    sl = df['low'].iloc[i-j]
            tp = (open_price - sl) * profit_factor + open_price
        if order_type == -1:
            sl = 0
            for j in range (lookback):
                if sl < df['high'].iloc[i-j]:
                    sl = df['high'].iloc[i-j]
            tp = open_price - (sl - open_price) * profit_factor
        return tp, sl

    def Supertrend(self, df, atr_period, multiplier, additional_index = 0):
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

        print(f'Final Lowerband {additional_index}' == 'Final Lowerband 0')

        if additional_index == 0:
            return pd.DataFrame({
                'Supertrend': supertrend,
                'Final Lowerband': final_lowerband,
                'Final Upperband': final_upperband
            }, index=df.index)
        else:
            return pd.DataFrame({
                f'Supertrend {additional_index}': supertrend,
                f'Final Lowerband {additional_index}': final_lowerband,
                f'Final Upperband {additional_index}': final_upperband
            }, index=df.index)

    def calculate_balance(self, df, transactions, initial_balance, leverage):
        current_balance = initial_balance
        balance = []
        i = 0

        for tp, sl, position_size, open_price, open_time, close_time, close_price, type, result, pnl in transactions:
            while df.index[i] <= open_time and df.index[i] < df.index[-1]:
                balance.append([df.index[i].to_pydatetime(), current_balance])
                i += 1
            while df.index[i] < close_time and df.index[i] < df.index[-1]:
                balance.append([df.index[i].to_pydatetime(), current_balance+position_size*(df['close'].iloc[i]/open_price-1)*type*leverage])
                i += 1
            current_balance += pnl
            
        while df.index[i] < df.index[-1]:
            balance.append([df.index[i].to_pydatetime(), current_balance])
            i += 1

        balance = pd.DataFrame(balance, columns=['ts', 'value'])

        return balance



    def macd_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):
        # Получаем индикаторы
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        indicators = ['macd', 'macd_signal']

        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, commission)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, commission) 
                    trade_open = False
            if not trade_open:
                if df['macd_signal'].iloc[i-1] < df['macd'].iloc[i] and df['macd_signal'].iloc[i] > df['macd'].iloc[i-1]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if df['macd_signal'].iloc[i-1] > df['macd'].iloc[i] and df['macd_signal'].iloc[i] < df['macd'].iloc[i-1]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators

    def macd_v2_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):
        # Рисуем индикаторы
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        indicators = ['macd', 'macd_signal']

        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, commission)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, commission)
                    trade_open = False

            if not trade_open:
                if df['macd_signal'].iloc[i-1] < df['macd_signal'].iloc[i-2] and df['macd_signal'].iloc[i] > df['macd_signal'].iloc[i-1]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if df['macd_signal'].iloc[i-1] > df['macd_signal'].iloc[i-2] and df['macd_signal'].iloc[i] < df['macd_signal'].iloc[i-1]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators

    def macd_v3_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):
        # Рисуем индикаторы
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        indicators = ['macd', 'macd_signal']

        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if df['macd'].iloc[i-1] > df['macd'].iloc[i-2] and df['macd'].iloc[i] < df['macd'].iloc[i-1] and type == 1:
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['close'].iloc[i], df.index[i], type, 0, 0, commission) 
                    trade_open = False       
                elif df['macd'].iloc[i-1] < df['macd'].iloc[i-2] and df['macd'].iloc[i] > df['macd'].iloc[i-1] and type == -1:
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['close'].iloc[i], df.index[i], type, 0, 0, commission)  
                    trade_open = False

            if not trade_open:
                if df['macd'].iloc[i-1] < df['macd'].iloc[i-2] and df['macd'].iloc[i] > df['macd'].iloc[i-1]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                if df['macd'].iloc[i-1] > df['macd'].iloc[i-2] and df['macd'].iloc[i] < df['macd'].iloc[i-1]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators

    def macd_vwap_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        vwap = ta.volume.VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'], window = 200)
        df['vwap'] = vwap.vwap
        indicators = ['macd', 'macd_signal', 'vwap']

        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, commission)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, commission)
                    trade_open = False

            if not trade_open:
                if (df['close'].iloc[i] > df['vwap'].iloc[i]) and df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if (df['close'].iloc[i] < df['vwap'].iloc[i]) and df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] < df['macd_signal'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators

    def bollinger_vwap_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):
                
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        vwap = ta.volume.VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'], window = 200)
        df['vwap'] = vwap.vwap
        indicators = ['bollinger_high', 'bollinger_low', 'vwap']

        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if df['high'].iloc[i] >= df['bollinger_high'].iloc[i] and type == 1:
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['bollinger_high'].iloc[i], df.index[i], type, df['bollinger_high'].iloc[i], sl, commission)
                    trade_open = False
                elif df['low'].iloc[i] <= df['bollinger_low'].iloc[i] and type == -1:
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['bollinger_low'].iloc[i], df.index[i], type, df['bollinger_low'].iloc[i], sl, commission)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, open_price, sl, commission)
                    trade_open = False

            else:
                if (df['close'].iloc[i] < df['bollinger_low'].iloc[i]) and \
                (df['close'].iloc[i-15:i+1] > df['vwap'].iloc[i-15:i+1]).all():
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1  # long
                    sl = open_price/1.01
                    trade_open = True
                elif (df['close'].iloc[i] > df['bollinger_high'].iloc[i]) and \
                    (df['close'].iloc[i-15:i+1] < df['vwap'].iloc[i-15:i+1]).all():
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1  # short
                    sl = open_price*1.01
                    trade_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators

    def bollinger_v2(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):
        
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        indicators = ['bollinger_high', 'bollinger_low']

        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, commission)
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, commission)
                    trade_open = False

            else:
                if (df['low'].iloc[i] < df['bollinger_low'].iloc[i]) and (df['close'].iloc[i] > df['open'].iloc[i]):
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1  # long
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if (df['high'].iloc[i] > df['bollinger_high'].iloc[i]) and (df['close'].iloc[i] < df['open'].iloc[i]):
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1  # short
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    
        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators  
    
    def supertrend_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):
        period = 10
        multiplier = 1

        sti = self.Supertrend(df, period, multiplier)
        df['Final Lowerband'] = sti['Final Lowerband']
        df['Final Upperband'] = sti['Final Upperband']
        df['Supertrend'] = sti['Supertrend']
        indicators = ['Final Lowerband', 'Final Upperband']

        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if df['Supertrend'].iloc[i-1] != df['Supertrend'].iloc[i]:
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['close'].iloc[i], df.index[i], type, 0, 0, commission)
                    trade_open = False

            if not trade_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)

        return transactions, balance, indicators

    def triple_supertrend(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):

        sti1 = self.Supertrend(df, 12, 3)
        sti2 = self.Supertrend(df, 11, 2, 2)
        sti3 = self.Supertrend(df, 10, 1, 3)
        df['Final Lowerband'] = sti1['Final Lowerband']
        df['Final Upperband'] = sti1['Final Upperband']
        df['Supertrend'] = sti1['Supertrend']
        df['Final Lowerband 2'] = sti2['Final Lowerband 2']
        df['Final Upperband 2'] = sti2['Final Upperband 2']
        df['Supertrend 2'] = sti2['Supertrend 2']
        df['Final Lowerband 3'] = sti3['Final Lowerband 3']
        df['Final Upperband 3'] = sti3['Final Upperband 3']
        df['Supertrend 3'] = sti3['Supertrend 3']
        indicators = ['Final Lowerband', 'Final Upperband', 'Final Lowerband 2', 'Final Upperband 2', 'Final Lowerband 3', 'Final Upperband 3']
        
        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
                    close_price = df['Final Lowerband'].iloc[i-1]
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0, commission)
                    trade_open = False
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:
                    close_price = df['Final Upperband'].iloc[i-1]
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0, commission)
                    trade_open = False

            if not trade_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators
    
    def supertrend_v3(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):
        good_deal = 3.3
        antishtraf = 0.09
        shtraf = 1
        period = 10
        multiplier = 2

        sti = self.Supertrend(df, period, multiplier)
        df['Final Lowerband'] = sti['Final Lowerband']
        df['Final Upperband'] = sti['Final Upperband']
        df['Supertrend'] = sti['Supertrend']
        indicators = ['Final Lowerband', 'Final Upperband']

        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
                    close_price = df['Final Lowerband'].iloc[i-1]
                    transactions, current_balance = self.close(transactions, current_balance, position_size * shtraf, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0, commission)
                    trade_open = False
                    if shtraf < 1:
                        shtraf += antishtraf
                    if close_price / open_price > (1+good_deal/100) and type == 1 or close_price / open_price < (1-good_deal/100) and type == -1:
                        shtraf = 0
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:
                    close_price = df['Final Upperband'].iloc[i-1]
                    transactions, current_balance = self.close(transactions, current_balance, position_size * shtraf, leverage, open_price, open_time, close_price, df.index[i], type,  0, 0, commission)
                    trade_open = False
                    if shtraf < 1:
                        shtraf += antishtraf
                    if close_price / open_price > (1+good_deal/100) and type == 1 or close_price / open_price < (1-good_deal/100) and type == -1:
                        shtraf = 0

            if not trade_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    trade_open = True
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    trade_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)         
        return transactions, balance, indicators

    def hawkes_process_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):

        lookback = 168
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=lookback, fillna=False).average_true_range()
        df['norm_range'] = (df['high'] - df['low']) / df['atr']
        #canvas.ax2.plot(df.index, df['norm_range'], label='norm_range', color='white', alpha=0.5)

        kappa = 0.1
        alpha = np.exp(-kappa)
        df['hawkes'] = df['norm_range']

        for i in range(lookback, len(df)):
            df['hawkes'].iloc[i] += df['hawkes'].iloc[i-1] * alpha
        df['hawkes'] *= kappa
    
        df['q05'] = df['hawkes'].rolling(lookback).quantile(0.05)
        df['q95'] = df['hawkes'].rolling(lookback).quantile(0.95)

        indicators = ['hawkes', 'q05', 'q95']

        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False
        was_below = 0 
        
        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, commission)
                    was_below = 0
                    trade_open = False
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, commission)
                    was_below = 0
                    trade_open = False

            if was_below > 0 and not trade_open:
                if df['hawkes'].iloc[i] >= df['q95'].iloc[i] and df['close'].iloc[was_below] < df['close'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if df['hawkes'].iloc[i] >= df['q95'].iloc[i] and df['close'].iloc[was_below] > df['close'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                    
            if not trade_open:
                if df['hawkes'].iloc[i] < df['q05'].iloc[i]:
                   was_below = i

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators

    def dca_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        indicators = ['macd', 'macd_signal']
        
        current_balance = initial_balance

        transactions = []
        percent = int(len(df) / 100)
        open_price = []
        position_sizes = []
        open_time = []

        orders = 20
        order_num = 0
        mid_open_price = 0
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    for j in range (0, order_num):
                        transactions, current_balance = self.close(transactions, current_balance, position_sizes[j], leverage, open_price[j], open_time[j], tp, df.index[i], type, 0, 0, commission)
                    trade_open = False
                    open_price = []
                    position_sizes = []
                    open_time = []
                    mid_open_price = 0
                    order_num = 0

            if not trade_open:
                if df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
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
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
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
                        mid_open_price += open_price[j] 
                    mid_open_price /= order_num
                    open_time.append(df.index[i])
                    tp = mid_open_price * 1.01
                elif df['close'].iloc[i] > open_price[order_num] and type == -1:
                    order_num += 1
                    mid_open_price = 0
                    for j in range (0, order_num):
                        mid_open_price += open_price[j]
                    mid_open_price /= order_num
                    open_time.append(df.index[i])
                    tp = mid_open_price * 0.99               

            if order_num == orders - 1:
                for j in range (0, order_num):
                    transactions, current_balance = self.close(transactions, current_balance, position_sizes[j], leverage, open_price[j], open_time[j], df['close'].iloc[i], df.index[i], type, 0, 0, commission)
                trade_open = False
                open_price = []
                position_sizes = []
                open_time = []
                mid_open_price = 0
                order_num = 0
        
        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators
        
    def rsi_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):

        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        indicators = ['rsi']
        
        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, commission)
                    trade_open = False       
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, commission)
                    trade_open = False

            if not trade_open:
                if df['rsi'].iloc[i-1] < 30 and df['rsi'].iloc[i] >= 30:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if df['rsi'].iloc[i-1] > 70 and df['rsi'].iloc[i] <= 70:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators

    def ma50200_cross_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):

        df['ma50'] = df['close'].rolling(window=50).mean()
        df['ma200'] = df['close'].rolling(window=200).mean()
        indicators = ['ma50', 'ma200']

        current_balance = initial_balance
        transactions = []
        percent = int(len(df) / 100)
        trade_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
                
            if trade_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, commission)
                    trade_open = False           
                elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                    transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, commission)
                    trade_open = False

            if not trade_open:
                if df['ma50'].iloc[i-1] < df['ma200'].iloc[i-1] and df['ma50'].iloc[i] >= df['ma200'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = 1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True
                if df['ma50'].iloc[i-1] > df['ma200'].iloc[i-1] and df['ma50'].iloc[i] <= df['ma200'].iloc[i]:
                    if position_type == "percent":
                        position_size = position_size / 100 * current_balance
                    open_price = df['close'].iloc[i]
                    open_time = df.index[i]
                    type = -1
                    tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                    trade_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators



