from .base_strategy import BaseStrategy
import ta

class MACrossStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "MA 50/200 Cross Strategy"
        self.description = "Strategy based on Moving Average 50 and 200 crossovers"

    def _setup_parameters(self):
        self.add_parameter(
            "fast_ma", 
            50, 
            "Fast Moving Average period",
            int,
            min_value=10,
            max_value=100
        )
        self.add_parameter(
            "slow_ma", 
            200, 
            "Slow Moving Average period",
            int,
            min_value=50,
            max_value=500
        )
        self.add_parameter(
            "lookback_period",
            15,
            "TP/SL lookback period",
            int,
            min_value=5,
            max_value=50
        )

    def run(self, df, initial_balance, position_size, position_type, profit_factor):
        fast_ma = self.parameters["fast_ma"].value
        slow_ma = self.parameters["slow_ma"].value
        lookback_period = self.parameters["lookback_period"].value

        df['ma_fast'] = df['close'].rolling(window=fast_ma).mean()
        df['ma_slow'] = df['close'].rolling(window=slow_ma).mean()
        
        self.manager.indicators = ['ma_fast', 'ma_slow']

        current_balance = initial_balance
        qty = position_size
        if position_type == "percent":
            qty = position_size / 100 * current_balance
        percent = int(len(df) / 100)
        position_open = False

        for i in range(len(df)):
            if i % percent == 0:
                self.manager.progress_changed.emit(int(i / len(df) * 100))

            if position_open:
                if self.manager.check_tp_sl(posId, tpTriggerPx, slTriggerPx, df.index[i]):
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance

            if not position_open:
                if df['ma_fast'].iloc[i-1] < df['ma_slow'].iloc[i-1] and df['ma_fast'].iloc[i] >= df['ma_slow'].iloc[i]:
                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', lookback_period)
                    posId = self.manager.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                if df['ma_fast'].iloc[i-1] > df['ma_slow'].iloc[i-1] and df['ma_fast'].iloc[i] <= df['ma_slow'].iloc[i]:
                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', lookback_period)
                    posId = self.manager.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
