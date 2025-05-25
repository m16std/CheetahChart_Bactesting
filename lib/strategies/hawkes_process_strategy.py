from .base_strategy import BaseStrategy
import ta
import numpy as np

class HawkesProcessStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "Hawkes Process Strategy"
        self.description = "Strategy based on Hawkes process and ATR"

    def _setup_parameters(self):
        self.add_parameter(
            "lookback", 
            168, 
            "ATR and quantile lookback period",
            int,
            min_value=50,
            max_value=500
        )
        self.add_parameter(
            "kappa", 
            0.1, 
            "Hawkes process decay factor",
            float,
            min_value=0.01,
            max_value=1.0
        )
        self.add_parameter(
            "lower_quantile", 
            0.05, 
            "Lower quantile threshold",
            float,
            min_value=0.01,
            max_value=0.2
        )
        self.add_parameter(
            "upper_quantile", 
            0.95, 
            "Upper quantile threshold",
            float,
            min_value=0.8,
            max_value=0.99
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
        lookback = self.parameters["lookback"].value
        kappa = self.parameters["kappa"].value
        lower_quantile = self.parameters["lower_quantile"].value
        upper_quantile = self.parameters["upper_quantile"].value
        lookback_period = self.parameters["lookback_period"].value

        df['atr'] = ta.volatility.AverageTrueRange(
            df['high'], df['low'], df['close'], 
            window=lookback, 
            fillna=False
        ).average_true_range()
        
        df['norm_range'] = (df['high'] - df['low']) / df['atr']
        alpha = np.exp(-kappa)
        df['hawkes'] = df['norm_range']

        for i in range(lookback, len(df)):
            df['hawkes'].iloc[i] += df['hawkes'].iloc[i-1] * alpha
        df['hawkes'] *= kappa

        df['q05'] = df['hawkes'].rolling(lookback).quantile(lower_quantile)
        df['q95'] = df['hawkes'].rolling(lookback).quantile(upper_quantile)
        
        self.manager.indicators = ['hawkes', 'q05', 'q95']

        current_balance = initial_balance
        qty = position_size
        if position_type == "percent":
            qty = position_size / 100 * current_balance
        percent = int(len(df) / 100)
        position_open = False
        was_below = 0

        for i in range(len(df)):
            if i % percent == 0:
                self.manager.progress_changed.emit(int(i / len(df) * 100))

            if position_open:
                if self.manager.check_tp_sl(posId, tpTriggerPx, slTriggerPx, df.index[i]):
                    position_open = False
                    was_below = 0
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance

            else:
                if was_below > 0:
                    if df['hawkes'].iloc[i] >= df['q95'].iloc[i] and df['close'].iloc[was_below] < df['close'].iloc[i]:
                        tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', lookback_period)
                        posId = self.manager.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                        position_open = True
                    elif df['hawkes'].iloc[i] >= df['q95'].iloc[i] and df['close'].iloc[was_below] > df['close'].iloc[i]:
                        tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', lookback_period)
                        posId = self.manager.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                        position_open = True

                if not position_open and df['hawkes'].iloc[i] < df['q05'].iloc[i]:
                    was_below = i
