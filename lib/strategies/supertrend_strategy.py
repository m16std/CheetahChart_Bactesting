from .base_strategy import BaseStrategy
import ta

class SupertrendStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "Supertrend Strategy"
        self.description = "Strategy based on Supertrend indicator"

    def _setup_parameters(self):
        self.add_parameter(
            "period", 
            10, 
            "ATR Period",
            int,
            min_value=5,
            max_value=50
        )
        self.add_parameter(
            "multiplier", 
            1.0, 
            "ATR Multiplier",
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
        period = self.parameters["period"].value
        multiplier = self.parameters["multiplier"].value
        
        sti = self.manager.Supertrend(df, period, multiplier)
        df['Final Lowerband'] = sti['Final Lowerband']
        df['Final Upperband'] = sti['Final Upperband']
        df['Supertrend'] = sti['Supertrend']
        
        self.manager.indicators = ['Final Lowerband', 'Final Upperband']

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
                if df['Supertrend'].iloc[i-1] != df['Supertrend'].iloc[i]:
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance

            if not position_open:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:              
                    posId = self.manager.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    posId = self.manager.open_position('short', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
