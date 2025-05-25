from .base_strategy import BaseStrategy
import ta

class BollingerV2Strategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "Bollinger V2 Strategy"
        self.description = "Strategy based on Bollinger Bands with candlestick confirmation"

    def _setup_parameters(self):
        self.add_parameter(
            "bb_window", 
            20, 
            "Bollinger Bands period",
            int,
            min_value=5,
            max_value=100
        )
        self.add_parameter(
            "bb_std", 
            2.0, 
            "Number of standard deviations",
            float,
            min_value=0.5,
            max_value=4.0
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
        bb_window = self.parameters["bb_window"].value
        bb_std = self.parameters["bb_std"].value
        lookback_period = self.parameters["lookback_period"].value

        bollinger = ta.volatility.BollingerBands(
            df['close'], 
            window=bb_window, 
            window_dev=bb_std
        )
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        
        self.manager.indicators = ['bollinger_high', 'bollinger_low']

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

            else:
                if (df['low'].iloc[i] < df['bollinger_low'].iloc[i]) and (df['close'].iloc[i] > df['open'].iloc[i]):
                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', lookback_period)
                    posId = self.manager.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                if (df['high'].iloc[i] > df['bollinger_high'].iloc[i]) and (df['close'].iloc[i] < df['open'].iloc[i]):
                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', lookback_period)
                    posId = self.manager.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
