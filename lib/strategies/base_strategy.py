from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class StrategyParameter:
    name: str
    value: Any
    description: str
    type: type
    min_value: float = None
    max_value: float = None

class BaseStrategy:
    def __init__(self):
        self.parameters: Dict[str, StrategyParameter] = {}
        self.name = "Base Strategy"
        self.description = "Base strategy description"
        self.manager = None
        self._setup_parameters()

    def set_manager(self, manager):
        """Set reference to strategy manager"""
        self.manager = manager

    def _setup_parameters(self):
        """Override this method to define strategy parameters"""
        pass

    def add_parameter(self, key: str, value: Any, description: str, param_type: type, 
                     min_value: float = None, max_value: float = None):
        self.parameters[key] = StrategyParameter(
            name=key,
            value=value,
            description=description,
            type=param_type,
            min_value=min_value,
            max_value=max_value
        )

    def get_parameters(self) -> Dict[str, StrategyParameter]:
        return self.parameters

    def set_parameter(self, key: str, value: Any):
        if key in self.parameters:
            self.parameters[key].value = value

    def run(self, df, initial_balance, position_size, position_type, profit_factor):
        """Override this method to implement strategy logic"""
        raise NotImplementedError

    def to_dict(self) -> dict:
        """Convert strategy to dictionary for export"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                k: {
                    "value": v.value,
                    "description": v.description,
                    "type": str(v.type),
                    "min_value": v.min_value,
                    "max_value": v.max_value
                } for k, v in self.parameters.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BaseStrategy':
        """Create strategy instance from dictionary"""
        strategy = cls()
        strategy.name = data["name"]
        strategy.description = data["description"]
        for key, param_data in data["parameters"].items():
            if key in strategy.parameters:
                strategy.parameters[key].value = param_data["value"]
        return strategy


"""

# Встроенные стратегии

    def macd_strategy(self, df, initial_balance, position_size, position_type, profit_factor):
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        self.indicators = ['macd', 'macd_signal']

        current_balance = initial_balance
        qty = position_size
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
        return

    def macd_v2_strategy(self, df, initial_balance, position_size, position_type, profit_factor):
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        self.indicators = ['macd', 'macd_signal']

        current_balance = qty = initial_balance
        qty = position_size
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
                if df['macd_signal'].iloc[i-1] < df['macd_signal'].iloc[i-2] and df['macd_signal'].iloc[i] > df['macd_signal'].iloc[i-1]:  
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', 15)
                    posId = self.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                if df['macd_signal'].iloc[i-1] > df['macd_signal'].iloc[i-2] and df['macd_signal'].iloc[i] < df['macd_signal'].iloc[i-1]:
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', 15)
                    posId = self.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
        return

    def macd_v3_strategy(self, df, initial_balance, position_size, position_type, profit_factor):
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        self.indicators = ['macd', 'macd_signal']

        current_balance = initial_balance
        qty = position_size
        if position_type == "percent":
            qty = position_size / 100 * current_balance
        percent = int(len(df) / 100)
        position_open = False
        side = 0

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if position_open:
                if df['macd'].iloc[i-1] > df['macd'].iloc[i-2] and df['macd'].iloc[i] < df['macd'].iloc[i-1] and side == 1:
                    self.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance     
                elif df['macd'].iloc[i-1] < df['macd'].iloc[i-2] and df['macd'].iloc[i] > df['macd'].iloc[i-1] and side == -1:
                    self.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance  

            if not position_open:
                if df['macd'].iloc[i-1] < df['macd'].iloc[i-2] and df['macd'].iloc[i] > df['macd'].iloc[i-1]:
                    posId = self.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                    side = 1
                if df['macd'].iloc[i-1] > df['macd'].iloc[i-2] and df['macd'].iloc[i] < df['macd'].iloc[i-1]:               
                    posId = self.open_position('short', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                    side = -1
        return 

    def macd_vwap_strategy(self, df, initial_balance, position_size, position_type, profit_factor):
        
        vwap = ta.volume.VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'], window = 200)
        df['vwap'] = vwap.vwap
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        self.indicators = ['macd', 'macd_signal', 'vwap']

        current_balance = initial_balance
        qty = position_size
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
                if (df['close'].iloc[i] > df['vwap'].iloc[i]) and df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', 15)
                    posId = self.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                if (df['close'].iloc[i] < df['vwap'].iloc[i]) and df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] < df['macd_signal'].iloc[i]:
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', 15)
                    posId = self.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
        return 

    def bollinger_vwap_strategy(self, df, initial_balance, position_size, position_type, profit_factor):
                
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        vwap = ta.volume.VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'], window = 200)
        df['vwap'] = vwap.vwap
        self.indicators = ['bollinger_high', 'bollinger_low', 'vwap']

        current_balance = initial_balance
        qty = position_size
        percent = int(len(df) / 100)
        if position_type == "percent":
            qty = position_size / 100 * current_balance 
        position_open = False
        side = 0

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if position_open:
                if df['high'].iloc[i] >= df['bollinger_high'].iloc[i] and side == 1:
                    self.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance    
                elif df['low'].iloc[i] <= df['bollinger_low'].iloc[i] and side == -1:
                    self.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance    
                elif (df['low'].iloc[i] <= slTriggerPx and side == 1) or (df['high'].iloc[i] >= slTriggerPx and side == -1):
                    self.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance  

            else:
                if (df['close'].iloc[i] < df['bollinger_low'].iloc[i]) and \
                (df['close'].iloc[i-15:i+1] > df['vwap'].iloc[i-15:i+1]).all():
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', 15)
                    posId = self.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                    side = 1
                elif (df['close'].iloc[i] > df['bollinger_high'].iloc[i]) and \
                    (df['close'].iloc[i-15:i+1] < df['vwap'].iloc[i-15:i+1]).all():
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', 15)
                    posId = self.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                    side = -1

        return 

    def bollinger_v2(self, df, initial_balance, position_size, position_type, profit_factor):
        
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        self.indicators = ['bollinger_high', 'bollinger_low']

        current_balance = initial_balance
        qty = position_size
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

            else:
                if (df['low'].iloc[i] < df['bollinger_low'].iloc[i]) and (df['close'].iloc[i] > df['open'].iloc[i]):
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', 15)
                    posId = self.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                if (df['high'].iloc[i] > df['bollinger_high'].iloc[i]) and (df['close'].iloc[i] < df['open'].iloc[i]):
                    itpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', 15)
                    posId = self.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
        return 
    
    def supertrend_strategy(self, df, initial_balance, position_size, position_type, profit_factor):
        period = 10
        multiplier = 1

        sti = self.Supertrend(df, period, multiplier)
        df['Final Lowerband'] = sti['Final Lowerband']
        df['Final Upperband'] = sti['Final Upperband']
        df['Supertrend'] = sti['Supertrend']
        self.indicators = ['Final Lowerband', 'Final Upperband']

        current_balance = initial_balance
        qty = position_size
        if position_type == "percent":
            qty = position_size / 100 * current_balance
        percent = int(len(df) / 100)
        position_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))

            if position_open:
                if df['Supertrend'].iloc[i-1] != df['Supertrend'].iloc[i]:
                    self.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance

            if not position_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:              
                    posId = self.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                if df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    posId = self.open_position('short', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True

        return

    def triple_supertrend(self, df, initial_balance, position_size, position_type, profit_factor):

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
        self.indicators = ['Final Lowerband', 'Final Upperband', 'Final Lowerband 2', 'Final Upperband 2', 'Final Lowerband 3', 'Final Upperband 3']
        
        current_balance = initial_balance
        percent = int(len(df) / 100)
        position_open = False
        qty = position_size
        if position_type == "percent":
            qty = position_size / 100 * current_balance 

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if position_open:
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
                    self.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance 
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:
                    self.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance 
            else:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    posId = self.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    posId = self.open_position('short', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
        return 
    
    def supertrend_v3(self, df, initial_balance, position_size, position_type, profit_factor):
        good_deal = 3.3
        antishtraf = 0.09
        shtraf = 1
        period = 10
        multiplier = 2

        sti = self.Supertrend(df, period, multiplier)
        df['Final Lowerband'] = sti['Final Lowerband']
        df['Final Upperband'] = sti['Final Upperband']
        df['Supertrend'] = sti['Supertrend']
        self.indicators = ['Final Lowerband', 'Final Upperband']

        current_balance = initial_balance
        percent = int(len(df) / 100)
        position_open = False
        qty = position_size
        if position_type == "percent":
            qty = position_size / 100 * current_balance 

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if position_open:
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
                    close_price = df['Final Upperband'].iloc[i]
                    self.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance 
                    if shtraf < 1:
                        shtraf += antishtraf
                    if close_price / open_price > (1+good_deal/100) and type == 1 or close_price / open_price < (1-good_deal/100) and type == -1:
                        shtraf = 0
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:
                    close_price = df['Final Upperband'].iloc[i]
                    self.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance 
                    if shtraf < 1:
                        shtraf += antishtraf
                    if close_price / open_price > (1+good_deal/100) and type == 1 or close_price / open_price < (1-good_deal/100) and type == -1:
                        shtraf = 0
            else:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    posId = self.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty * shtraf, df.index[i])
                    open_price = df['close'].iloc[i]
                    position_open = True
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    posId = self.open_position('short', 'market', 0, 0, df['close'].iloc[i], qty * shtraf, df.index[i])
                    open_price = df['close'].iloc[i]
                    position_open = True      
        return 

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

    def find_mid_open_price(self, open_prices, positions_count):
        mid_open_price = 0
        print(len(open_prices), positions_count)
        for j in range (0, positions_count):
            mid_open_price += open_prices[j] 
        mid_open_price /= positions_count
        return mid_open_price 

    def dca_strategy(self, df, initial_balance, position_size, position_type, profit_factor):

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        self.indicators = ['macd', 'macd_signal']
        
        current_balance = initial_balance

        current_balance = initial_balance
        percent = int(len(df) / 100)
        position_open = False
        qty = position_size
        if position_type == "percent":
            qty = position_size / 100 * current_balance 
        open_prices = []
        posId = []

        orders = 20
        gap = 0.03
        tp_gap = 0.03
        mid_open_price = 0

        for i in range(len(df)):
            if i % percent == 0:
                self.progress_changed.emit(int(i / len(df) * 100))
            if position_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    for j in range (len(posId)):
                        self.close_position(posId[j], tp, df.index[i])
                    position_open = False
                    current_balance = self.get_current_balance()
                    open_prices = []
                    posId = []
                    mid_open_price = 0

            if not position_open:
                if df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                    posId.append(self.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty/orders, df.index[i]))
                    open_prices.append(df['close'].iloc[i])
                    for j in range (1, orders):
                        open_prices.append(open_prices[-1]*(1.0 - gap))
                    mid_open_price = df['close'].iloc[i]
                    type = 1
                    tp = mid_open_price * (1.0 + tp_gap)
                    position_open = True
                
                elif df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] < df['macd_signal'].iloc[i]:
                    posId.append(self.open_position('short', 'market', 0, 0, df['close'].iloc[i], qty/orders, df.index[i]))
                    open_prices.append(df['close'].iloc[i])
                    for j in range (1, orders):
                        open_prices.append(open_prices[-1]*(1.0 + gap))
                    mid_open_price = df['close'].iloc[i]
                    type = -1
                    tp = mid_open_price * (1.0 - tp_gap)
                    position_open = True

            if len(posId) < orders - 1 and position_open:
                if df['low'].iloc[i] < open_prices[len(posId)] and type == 1:
                    posId.append(self.open_position('long', 'market', 0, 0, open_prices[len(posId)], qty/orders, df.index[i]))
                    mid_open_price = self.find_mid_open_price(open_prices, len(posId))
                    tp = mid_open_price * (1.0 + gap)
                elif df['high'].iloc[i] > open_prices[len(posId)] and type == -1:
                    posId.append(self.open_position('short', 'market', 0, 0, open_prices[len(posId)], qty/orders, df.index[i]))
                    mid_open_price = self.find_mid_open_price(open_prices, len(posId))
                    tp = mid_open_price * (1.0 - gap)            

            if len(posId) == orders - 1:
                for j in range (len(posId)):
                    self.close_position(posId[j], df['close'].iloc[i], df.index[i])
                position_open = False
                open_prices = []
                posId = []
                mid_open_price = 0
        
        return 
        
    def rsi_strategy(self, df, initial_balance, position_size, position_type, profit_factor):

        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['70'] = 70
        df['30'] = 30
        self.indicators = ['rsi','70', '30']
        
        current_balance = initial_balance
        qty = position_size
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

            else:
                if df['rsi'].iloc[i-1] < 30 and df['rsi'].iloc[i] >= 30:
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', 15)
                    posId = self.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                if df['rsi'].iloc[i-1] > 70 and df['rsi'].iloc[i] <= 70:
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', 15)
                    posId = self.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
        return

    def ma50200_cross_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):

        df['ma50'] = df['close'].rolling(window=50).mean()
        df['ma200'] = df['close'].rolling(window=200).mean()
        indicators = ['ma50', 'ma200']

        current_balance = initial_balance
        qty = position_size
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
                if df['ma50'].iloc[i-1] < df['ma200'].iloc[i-1] and df['ma50'].iloc[i] >= df['ma200'].iloc[i]:
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', 15)
                    posId = self.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                if df['ma50'].iloc[i-1] > df['ma200'].iloc[i-1] and df['ma50'].iloc[i] <= df['ma200'].iloc[i]:
                    tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', 15)
                    posId = self.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True

        balance = self.calculate_balance(df, transactions, initial_balance, leverage)
        return transactions, balance, indicators




"""