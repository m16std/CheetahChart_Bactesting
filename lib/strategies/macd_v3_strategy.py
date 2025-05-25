from .base_strategy import BaseStrategy
import ta

class MACDv3Strategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "MACD V3 Strategy"
        self.description = "Strategy based on MACD directional changes without TP/SL"

    def _setup_parameters(self):
        self.add_parameter(
            "fast_period", 
            12, 
            "Fast EMA period",
            int,
            min_value=2,
            max_value=100
        )
        self.add_parameter(
            "slow_period", 
            26, 
            "Slow EMA period",
            int,
            min_value=5,
            max_value=200
        )
        self.add_parameter(
            "signal_period", 
            9, 
            "Signal line period",
            int,
            min_value=2,
            max_value=50
        )

    def run(self, df, initial_balance, position_size, position_type, profit_factor):
        fast_period = self.parameters["fast_period"].value
        slow_period = self.parameters["slow_period"].value
        signal_period = self.parameters["signal_period"].value

        macd = ta.trend.MACD(
            df['close'],
            window_fast=fast_period,
            window_slow=slow_period,
            window_sign=signal_period
        )
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        self.manager.indicators = ['macd', 'macd_signal']

        current_balance = initial_balance
        qty = position_size
        if position_type == "percent":
            qty = position_size / 100 * current_balance
        percent = int(len(df) / 100)
        position_open = False
        side = 0

        for i in range(len(df)):
            if i % percent == 0:
                self.manager.progress_changed.emit(int(i / len(df) * 100))

            if position_open:
                if df['macd'].iloc[i-1] > df['macd'].iloc[i-2] and df['macd'].iloc[i] < df['macd'].iloc[i-1] and side == 1:
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance     
                elif df['macd'].iloc[i-1] < df['macd'].iloc[i-2] and df['macd'].iloc[i] > df['macd'].iloc[i-1] and side == -1:
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance  

            if not position_open:
                if df['macd'].iloc[i-1] < df['macd'].iloc[i-2] and df['macd'].iloc[i] > df['macd'].iloc[i-1]:
                    posId = self.manager.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                    side = 1
                if df['macd'].iloc[i-1] > df['macd'].iloc[i-2] and df['macd'].iloc[i] < df['macd'].iloc[i-1]:               
                    posId = self.manager.open_position('short', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                    side = -1
        return
