from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from pyqttoast import ToastPreset
from PyQt5.QtGui import *

from ..strategies.base_strategy import BaseStrategy
from ..strategies.macd_strategy import MACDStrategy
from ..strategies.macd_v2_strategy import MACDv2Strategy
from ..strategies.macd_v3_strategy import MACDv3Strategy
from ..strategies.macd_vwap_strategy import MACDVWAPStrategy
from ..strategies.bollinger_vwap_strategy import BollingerVWAPStrategy
from ..strategies.bollinger_v2_strategy import BollingerV2Strategy
from ..strategies.supertrend_strategy import SupertrendStrategy
from ..strategies.triple_supertrend_strategy import TripleSupertrendStrategy
from ..strategies.supertrend_v3_strategy import SupertrendV3Strategy
from ..strategies.hawkes_process_strategy import HawkesProcessStrategy
from ..strategies.dca_strategy import DCAStrategy
from ..strategies.rsi_strategy import RSIStrategy
from ..strategies.ma_cross_strategy import MACrossStrategy

import importlib.util
import pandas as pd
import numpy as np
import textwrap
import hashlib
import inspect
import json
import os
import ta


class StrategyManager(QThread):
    calculation_complete = pyqtSignal(object, object, object)
    progress_changed = pyqtSignal(int)
    import_complete = pyqtSignal(object, object)
    create_toast = pyqtSignal(object, object, object)
    update_chart_signal = pyqtSignal()
    load_external_strategies_complete = pyqtSignal(object)
    strategy_config_requested = pyqtSignal(object)  # New signal for config dialog
 
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

        # Initialize all strategies
        self.strategy_dict = {}
        strategies = [
            MACDStrategy(),
            MACDv2Strategy(),
            MACDv3Strategy(),
            MACDVWAPStrategy(),
            BollingerVWAPStrategy(),
            BollingerV2Strategy(),
            SupertrendStrategy(), 
            TripleSupertrendStrategy(),
            SupertrendV3Strategy(),
            HawkesProcessStrategy(),
            DCAStrategy(),
            RSIStrategy(),
            MACrossStrategy()
        ]
        
        for strategy in strategies:
            strategy.set_manager(self)
            self.strategy_dict[strategy.name] = strategy

        self.positions = []
        self.balance = []
        self.posId_prev = 1
        self.current_balance = 0

    def run(self, mode="test"):
        
        if mode == "test":
            self.run_strategy()
        elif mode == "export":
            self.export_strategy()
        elif mode == "import":
            self.import_strategy()
        elif mode == "trade":
            self.run_strategy(is_trade=True)
        else:
            print("Неверный режим")

        return

    def run_strategy(self, is_trade=False):
        current_strategy = self.strategy_dict.get(self.strat_name)
        self.current_balance = self.initial_balance    
        self.positions = []
        self.balance = []
        self.indicators = []
        self.posId_counter = 1
        current_strategy.run(self.df, self.initial_balance, self.position_size, self.position_type, self.profit_factor)
        self.balance = self.calculate_balance(self.df, self.positions, self.initial_balance, self.leverage, is_trade)
        self.calculation_complete.emit(self.positions, self.balance, self.indicators)
        
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
            'commission': 0,
            'syncStatus': 'unsynced'  # Статус синхронизации с биржей
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

    def calculate_balance(self, df, positions, initial_balance, leverage, is_trade=False):
        """Рассчитывает баланс с учетом режима торговли"""
        self.current_balance = initial_balance
        balance = []

        # Фильтруем позиции в зависимости от режима
        if is_trade:
            filtered_positions = [pos for pos in positions if pos.get('syncStatus', '') == 'synced']
        else:
            filtered_positions = positions

        i = 0
        for position in filtered_positions:
            if position['status'] == 'closed':
                while df.index[i] < position['closeTimestamp'] and df.index[i] < df.index[-1]:
                    balance.append([df.index[i].to_pydatetime(), self.current_balance])
                    i += 1
            else:
                while df.index[i] < df.index[-1]:
                    balance.append([df.index[i].to_pydatetime(), self.current_balance])
                    i += 1

            self.current_balance += position['pnl']
        while df.index[i] < df.index[-1]:
            balance.append([df.index[i].to_pydatetime(), self.current_balance])
            i += 1
        
        self.balance = pd.DataFrame(balance, columns=['ts', 'value'])
        
        for position in filtered_positions:
            i = 0
            while df.index[i] < position['openTimestamp']:
                i += 1
            if position['status'] == 'closed':
                while df.index[i] < position['closeTimestamp'] and df.index[i] < df.index[-1]:
                    if position['posSide'] == 'long':
                        self.balance['value'].iloc[i] += (position['qty']*(df['close'].iloc[i]/position['openPrice']-1)*leverage)
                    else:
                        self.balance['value'].iloc[i] -= (position['qty']*(df['close'].iloc[i]/position['openPrice']-1)*leverage)
                    i += 1
            else:
                while df.index[i] < df.index[-1]:
                    if position['posSide'] == 'long':
                        self.balance['value'].iloc[i] += (position['qty']*(df['close'].iloc[i]/position['openPrice']-1)*leverage)
                    else:
                        self.balance['value'].iloc[i] -= (position['qty']*(df['close'].iloc[i]/position['openPrice']-1)*leverage)
                    i += 1

        return self.balance

    def get_tp_sl(self, df, i, open_price, profit_factor, order_type, lookback):
        lookback = int(lookback)
        
        if order_type == 'long':
            sl = 1000000
            for j in range(lookback):
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
        if not os.path.exists(self.strategy_directory):
            QMessageBox.warning(self, 'Error', 'Директория со внешними стратегиями не найдена')
            return

        strategy_files = [f for f in os.listdir(self.strategy_directory) if f.endswith(".py")]

        for file in strategy_files:
            try:
                # Load strategy class from file
                strategy_class = self._load_strategy_class(file)
                if strategy_class and issubclass(strategy_class, BaseStrategy):
                    strategy = strategy_class()
                    strategy.set_manager(self)  # Set manager reference
                    self.strategy_dict[strategy.name] = strategy
                    self.create_toast.emit(
                        ToastPreset.SUCCESS, 
                        "Стратегия добавлена", 
                        f"Стратегия {strategy.name} загружена"
                    )
            except Exception as e:
                print(f'Ошибка загрузки стратегии "{file}": {str(e)}')

    def _load_strategy_class(self, file_path):
        # Implementation of strategy class loading
        pass

    def export_strategy(self):
        strategy = self.strategy_dict.get(self.strat_name)
        if not strategy:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            None, "Save Strategy", "", "JSON Files (*.json)"
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(strategy.to_dict(), f, indent=4)

    def import_strategy(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Import Strategy", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                strategy = BaseStrategy.from_dict(data)
                self.strategy_dict[strategy.name] = strategy
                self.import_complete.emit(strategy.name, strategy)
            except Exception as e:
                QMessageBox.critical(None, 'Error', f'Failed to import strategy: {str(e)}')

    def request_strategy_config(self, strategy_name):
        """Request to open configuration dialog for strategy"""
        strategy = self.strategy_dict.get(strategy_name)
        if strategy:
            self.strategy_config_requested.emit(strategy)

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
