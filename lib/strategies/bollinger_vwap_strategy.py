from .base_strategy import BaseStrategy
import ta

class BollingerVWAPStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "Bollinger VWAP Strategy"
        self.description = "Strategy based on Bollinger Bands and VWAP indicators"

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
            "Bollinger Bands standard deviation",
            float,
            min_value=0.5,
            max_value=4.0
        )
        self.add_parameter(
            "vwap_window",
            200,
            "VWAP window period",
            int,
            min_value=10,
            max_value=500
        )
        self.add_parameter(
            "vwap_lookback",
            15,
            "TP/SL lookback period",
            int,
            min_value=5,
            max_value=50
        )

    def run(self, df, initial_balance, position_size, position_type, profit_factor):
        bb_window = self.parameters["bb_window"].value
        bb_std = self.parameters["bb_std"].value
        vwap_window = self.parameters["vwap_window"].value
        vwap_lookback = self.parameters["vwap_lookback"].value

        bollinger = ta.volatility.BollingerBands(df['close'], window=bb_window, window_dev=bb_std)
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        
        vwap = ta.volume.VolumeWeightedAveragePrice(
            df['high'], 
            df['low'], 
            df['close'], 
            df['volume'], 
            window=vwap_window
        )
        df['vwap'] = vwap.vwap
        
        self.manager.indicators = ['bollinger_high', 'bollinger_low', 'vwap']

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
                if df['high'].iloc[i] >= df['bollinger_high'].iloc[i] and side == 1:
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance    
                elif df['low'].iloc[i] <= df['bollinger_low'].iloc[i] and side == -1:
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance    
                elif (df['low'].iloc[i] <= slTriggerPx and side == 1) or (df['high'].iloc[i] >= slTriggerPx and side == -1):
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance

            else:
                if (df['close'].iloc[i] < df['bollinger_low'].iloc[i]) and \
                (df['close'].iloc[i-vwap_lookback:i+1] > df['vwap'].iloc[i-vwap_lookback:i+1]).all():
                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', vwap_lookback)
                    posId = self.manager.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                    side = 1
                elif (df['close'].iloc[i] > df['bollinger_high'].iloc[i]) and \
                    (df['close'].iloc[i-vwap_lookback:i+1] < df['vwap'].iloc[i-vwap_lookback:i+1]).all():
                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', vwap_lookback)
                    posId = self.manager.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                    side = -1
