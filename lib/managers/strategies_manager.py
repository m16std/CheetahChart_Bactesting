from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from pyqttoast import ToastPreset
from PyQt5.QtGui import *
import importlib.util
import pandas as pd
import numpy as np
import textwrap
import hashlib
import inspect
import os
import ta


class StrategyManager(QThread):
    calculation_complete = pyqtSignal(object, object, object)
    progress_changed = pyqtSignal(int)
    import_complete = pyqtSignal(object, object)
    create_toast = pyqtSignal(object, object, object)
    update_chart_signal = pyqtSignal()
    load_external_strategies_complete = pyqtSignal(object)
 
    def __init__(self, parent=None):
        super(StrategyManager, self).__init__(parent)
        self.strategy_directory = ''
        self.profit_factor = 0
        self.leverage = 0
        self.initial_balance = 0
        self.position_type = ''
        self.position_size = 0
        self.df = []
        self.strat_name = ''
        self.commission = 0
    
        self.strategy_dict = {
            'MACD Strategy': self.macd_strategy,
            'MACD v2': self.macd_v2_strategy,
            'Bollinger + VWAP': self.bollinger_vwap_strategy,
            'Bollinger v2': self.bollinger_v2,
            'Supertrend': self.supertrend_strategy,
            'Triple Supertrend': self.triple_supertrend,
            'MACD v3': self.macd_v3_strategy,
            'MACD VWAP': self.macd_vwap_strategy,
            'Hawkes Process': self.hawkes_process_strategy,
            'Supertrend v3 SOLANA 1H SETUP': self.supertrend_v3,
            'DCA': self.dca_strategy,
            'RSI': self.rsi_strategy,
            'MA-50 cross MA-200': self.ma50200_cross_strategy,
        }

        self.positions = []  # Список сделок
        self.balance = []  # Хронология баланса
        self.posId_prev = 1  # Для генерации уникальных ID сделок
        self.current_balance = 0

    def run(self, mode="run"):
        
        if mode == "run":
            self.run_strategy()
        elif mode == "export":
            self.export_strategy()
        elif mode == "import":
            self.import_strategy()
        elif mode == "trade":
            self.trade()
        else:
            print("Неверный режим")

        return

    def run_strategy(self):
        current_strategy = self.strategy_dict.get(self.strat_name)
        self.current_balance = self.initial_balance    
        self.positions = []
        self.balance = []
        self.posId_counter = 1
        indicators = current_strategy(self.df, self.initial_balance, self.position_size, self.position_type, self.profit_factor)
        self.balance = self.calculate_balance(self.df, self.positions, self.initial_balance, self.leverage)
        self.calculation_complete.emit(self.positions, self.balance, indicators)
        


# Приспособы для работы стратегий

    def open_position(self, posSide, ordType, tpTriggerPx, slTriggerPx, openPrice, qty, timestamp):
        """
        Открывает позицию и возвращает posId.
        
        :posSide: 'long' или 'short'
        :ordType: Тип ордера ('limit' или 'market')
        :tpTriggerPx: Цена тейкпрофита
        :slTriggerPx: Цена стоп-лосса
        :price: Цена открытия позиции
        :qty: Количество (объем позиции)
        :timestamp: Время открытия позиции
        :leverage: Кредитное плечо
        :return: posId — уникальный ID позиции
        """
        # Генерация уникального ID сделки
        timestamp_str = str(timestamp)
        
        # Создаем строку из всех входных значений
        input_data = f"{timestamp_str}_{posSide}_{openPrice}"

        # Генерируем хэш от строки с использованием SHA-256
        hash_object = hashlib.sha256(input_data.encode())
        
        # Преобразуем результат хэширования в целое число
        posId = int(hash_object.hexdigest(), 16) % (10**10) 

        # Сохранение сделки в список сделок
        position = {
            'posId': posId,
            'posSide': posSide,
            'ordType': ordType,
            'tpTriggerPx': tpTriggerPx,
            'slTriggerPx': slTriggerPx,
            'openPrice': openPrice,
            'qty': qty,
            'openTimestamp': timestamp,
            'leverage': self.leverage,
            'status': 'open',
            'closePrice': 0,
            'closeTimestamp': 0,
            'pnl': 0,
            'commission': 0
        }
        self.positions.append(position)

        # Возврат posId для дальнейшей работы с позицией
        return posId

    def check_tp_sl(self, posId, tpTriggerPx, slTriggerPx, timestamp):
        """
        Проверяет свечи после открытия позиции на достижение стоп-лосса или тейк-профита.
        
        :posId: ID позиции
        :tpTriggerPx: Цена тейкпрофита
        :slTriggerPx: Цена стоп-лосса
        :timestamp: Время
        """

        position = next((t for t in self.positions if t['posId'] == posId), None)
        if position is None:
            raise ValueError(f"Position with ID {posId} not found")

        # Найдем индекс свечи, соответствующей open_timestamp
        df_reset = self.df.reset_index()
        start_index = df_reset[df_reset['ts'] >= timestamp].index[0]

        candle = df_reset.iloc[start_index]
        high = candle['high']
        low = candle['low']
        timestamp = candle['ts']

        # Проверка достижения тейкпрофита и стоплосса для long и short позиций
        if position['posSide'] == 'long':
            # Для long позиции тейкпрофит и стоплосс
            if tpTriggerPx and high >= tpTriggerPx:
                self.close_position(posId, tpTriggerPx, timestamp)
                return 'executed_tp'
            elif slTriggerPx and low <= slTriggerPx:
                self.close_position(posId, slTriggerPx, timestamp)
                return 'executed_sl'
                
        elif position['posSide'] == 'short':
            # Для short позиции тейкпрофит и стоплосс
            if tpTriggerPx and low <= tpTriggerPx:
                self.close_position(posId, tpTriggerPx, timestamp)
                return 'executed_tp'
            elif slTriggerPx and high >= slTriggerPx:
                self.close_position(posId, slTriggerPx, timestamp)
                return 'executed_sl'
            
        return False
                
    def close_position(self, posId, price, timestamp, ordType='market'):
        """
        Закрывает позицию по ID и обновляет баланс.

        :posId: ID позиции
        :price: Цена закрытия
        :timestamp: Время закрытия позиции
        :ordType: Тип ордера ('limit' или 'market')
        """
        # Поиск сделки по posId
        position = next((t for t in self.positions if t['posId'] == posId), None)
        if position is None:
            raise ValueError(f"Position with ID {posId} not found")
        
        if position['posSide'] == 'long':
            pnl = position['qty'] * (price - position['openPrice']) / position['openPrice'] * position['leverage'] 
        else:
            pnl = position['qty'] * (position['openPrice'] - price) / position['openPrice'] * position['leverage'] 

        commission = position['qty'] * self.commission * position['leverage']
        pnl -= commission

        position['status'] = 'closed'
        position['closePrice'] = price
        position['closeTimestamp'] = timestamp
        position['pnl'] = pnl
        position['commission'] = commission

        self.current_balance += pnl 

    def get_current_balance(self):
        return self.current_balance

    def calculate_balance(self, df, positions, initial_balance, leverage):
        current_balance = initial_balance
        balance = []
        i = 0

        for position in positions:
            while df.index[i] <= position['openTimestamp'] and df.index[i] < df.index[-1]:
                balance.append([df.index[i].to_pydatetime(), current_balance])
                i += 1
            if position['status'] == 'closed':
                while df.index[i] < position['closeTimestamp'] and df.index[i] < df.index[-1]:
                    if position['posSide'] == 'long':
                        balance.append([df.index[i].to_pydatetime(), current_balance + position['qty']*(df['close'].iloc[i]/position['openPrice']-1)*leverage])
                    else:
                        balance.append([df.index[i].to_pydatetime(), current_balance - position['qty']*(df['close'].iloc[i]/position['openPrice']-1)*leverage])
                    i += 1
            else:
                while df.index[i] < df.index[-1]:
                    if position['posSide'] == 'long':
                        balance.append([df.index[i].to_pydatetime(), current_balance + position['qty']*(df['close'].iloc[i]/position['openPrice']-1)*leverage])
                    else:
                        balance.append([df.index[i].to_pydatetime(), current_balance - position['qty']*(df['close'].iloc[i]/position['openPrice']-1)*leverage])
                    i += 1
            current_balance += position['pnl']
            
        while df.index[i] < df.index[-1]:
            balance.append([df.index[i].to_pydatetime(), current_balance])
            i += 1

        balance = pd.DataFrame(balance, columns=['ts', 'value'])

        return balance

    def get_tp_sl(self, df, i, open_price, profit_factor, order_type, lookback):
        if order_type == 'long':
            sl = 1000000
            for j in range (lookback):
                if sl > df['low'].iloc[i-j]:
                    sl = df['low'].iloc[i-j]
            tp = (open_price - sl) * profit_factor + open_price
        if order_type == 'short':
            sl = 0
            for j in range (lookback):
                if sl < df['high'].iloc[i-j]:
                    sl = df['high'].iloc[i-j]
            tp = open_price - (sl - open_price) * profit_factor
        return tp, sl

    def load_strategies_from_directory(self):
        # Проверяем наличие директории стратегий
        if not os.path.exists(self.strategy_directory):
            QMessageBox.warning(self, 'Error', 'Директория со внешними стратегиями не найдена')
            return
        
        # Получаем список файлов с расширением .py в директории стратегий
        strategy_files = [f for f in os.listdir(self.strategy_directory) if f.endswith(".py")]

        for file in strategy_files:
            file_path = os.path.join(self.strategy_directory, file)
            module_name = os.path.splitext(file)[0]

            try:
                # Импортируем стратегию с помощью importlib
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                strategy_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(strategy_module)

                # Ищем функцию в модуле
                strategy_function = None
                for name in dir(strategy_module):
                    obj = getattr(strategy_module, name)
                    if callable(obj):
                        strategy_function = obj
                        break

                if strategy_function:
                    strategy_function = strategy_function.__get__(self, self.__class__)
                    self.strategy_dict[module_name] = strategy_function
                    self.create_toast.emit(ToastPreset.SUCCESS, "Стратегия добавлена", f"Стратегия {name} загружена из внешней папки")

            except Exception as e:
                print(f'Ошибка загрузки стратегии "{module_name}": {str(e)}')

        self.load_external_strategies_complete.emit(self.strategy_dict)

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

    def import_strategy(self):
        # Открываем диалоговое окно для выбора файла стратегии
        file_path, _ = QFileDialog.getOpenFileName(None, "Import Strategy", "", "Python Files (*.py);;All Files (*)")
        
        if file_path:
            # Открываем диалоговое окно для ввода имени новой стратегии
            strategy_name, ok = QInputDialog.getText(None, 'Strategy Name', 'Enter a name for the imported strategy:')
            
            if ok:
                # Проверяем, что имя стратегии уникально
                if strategy_name in self.strategy_dict:
                    QMessageBox.warning(None, 'Error', f'Strategy "{strategy_name}" already exists. Choose another name.')
                    return

                # Импортируем стратегию с помощью importlib
                try:
                    module_name = os.path.splitext(os.path.basename(file_path))[0]  # Название модуля из имени файла
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    strategy_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(strategy_module)

                    # Ищем функцию в модуле
                    strategy_function = None
                    for name in dir(strategy_module):
                        obj = getattr(strategy_module, name)
                        if callable(obj):
                            strategy_function = obj
                            break

                    strategy_function = strategy_function.__get__(self, self.__class__)

                    if strategy_function is None:
                        raise Exception('No valid strategy function found in the imported file.')

                    # Сохраняем функцию как обычную
                    self.strategy_dict[strategy_name] = strategy_function

                    # Обновляем выпадающий список в главном окне
                    self.import_complete.emit(strategy_name, strategy_function)

                except Exception as e:
                    QMessageBox.critical(None, 'Error', f'Failed to import strategy: {str(e)}')
        else:
            print("Import cancelled.")

    def load_strategy(self, file_path):
        """Загружает стратегию из .py файла и добавляет её в список доступных стратегий"""
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

# Расчет супертренда для стратегий с супертрендом  

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

# Встроенные стратегии

    def macd_strategy(self, df, initial_balance, position_size, position_type, profit_factor):
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        indicators = ['macd', 'macd_signal']

        current_balance = qty = initial_balance
        if position_type == "percent":
            qty = position_size / 100 * current_balance
        percent = int(len(df) / 100)
        position_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))

            if position_open:
                if self.check_tp_sl(posId, tpTriggerPx, slTriggerPx, df.index[i]):
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance

            if not position_open:
                if df['macd_signal'].iloc[i-1] < df['macd'].iloc[i] and df['macd_signal'].iloc[i] > df['macd'].iloc[i-1]:  
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', 15)
                    posId = self.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                if df['macd_signal'].iloc[i-1] > df['macd'].iloc[i] and df['macd_signal'].iloc[i] < df['macd'].iloc[i-1]:
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', 15)
                    posId = self.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True

        return indicators

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
        df['70'] = 70
        df['30'] = 30
        indicators = ['rsi','70', '30']
        
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



