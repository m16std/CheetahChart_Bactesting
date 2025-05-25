from .base_strategy import BaseStrategy
import ta

class TripleSupertrendStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "Triple Supertrend Strategy"
        self.description = "Strategy based on three Supertrend indicators with different parameters"

    def _setup_parameters(self):
        self.add_parameter(
            "st1_period", 
            12, 
            "First Supertrend period",
            int,
            min_value=5,
            max_value=50
        )
        self.add_parameter(
            "st1_multiplier", 
            3.0, 
            "First Supertrend multiplier",
            float,
            min_value=0.5,
            max_value=10.0
        )
        self.add_parameter(
            "st2_period", 
            11, 
            "Second Supertrend period",
            int,
            min_value=5,
            max_value=50
        )
        self.add_parameter(
            "st2_multiplier", 
            2.0, 
            "Second Supertrend multiplier",
            float,
            min_value=0.5,
            max_value=10.0
        )
        self.add_parameter(
            "st3_period", 
            10, 
            "Third Supertrend period",
            int,
            min_value=5,
            max_value=50
        )
        self.add_parameter(
            "st3_multiplier", 
            1.0, 
            "Third Supertrend multiplier",
            float,
            min_value=0.5,
            max_value=10.0
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
        st1_period = self.parameters["st1_period"].value
        st1_multiplier = self.parameters["st1_multiplier"].value
        st2_period = self.parameters["st2_period"].value
        st2_multiplier = self.parameters["st2_multiplier"].value
        st3_period = self.parameters["st3_period"].value
        st3_multiplier = self.parameters["st3_multiplier"].value
        lookback_period = self.parameters["lookback_period"].value

        sti1 = self.manager.Supertrend(df, st1_period, st1_multiplier)
        sti2 = self.manager.Supertrend(df, st2_period, st2_multiplier, 2)
        sti3 = self.manager.Supertrend(df, st3_period, st3_multiplier, 3)

        df['Final Lowerband'] = sti1['Final Lowerband']
        df['Final Upperband'] = sti1['Final Upperband']
        df['Supertrend'] = sti1['Supertrend']
        df['Final Lowerband 2'] = sti2['Final Lowerband 2']
        df['Final Upperband 2'] = sti2['Final Upperband 2']
        df['Supertrend 2'] = sti2['Supertrend 2']
        df['Final Lowerband 3'] = sti3['Final Lowerband 3']
        df['Final Upperband 3'] = sti3['Final Upperband 3']
        df['Supertrend 3'] = sti3['Supertrend 3']
        
        self.manager.indicators = ['Final Lowerband', 'Final Upperband', 'Final Lowerband 2', 
                                 'Final Upperband 2', 'Final Lowerband 3', 'Final Upperband 3']

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
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance

            else:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', lookback_period)
                    posId = self.manager.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', lookback_period)
                    posId = self.manager.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
