from .base_strategy import BaseStrategy
import ta

class SupertrendV3Strategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "Supertrend V3 Strategy"
        self.description = "Advanced Supertrend strategy with adaptive position sizing"

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
            2.0, 
            "ATR Multiplier",
            float,
            min_value=0.5,
            max_value=10.0
        )
        self.add_parameter(
            "good_deal", 
            3.3, 
            "Good deal threshold (%)",
            float,
            min_value=0.1,
            max_value=10.0
        )
        self.add_parameter(
            "antishtraf", 
            0.09, 
            "Position size recovery rate",
            float,
            min_value=0.01,
            max_value=1.0
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
        good_deal = self.parameters["good_deal"].value
        antishtraf = self.parameters["antishtraf"].value
        lookback_period = self.parameters["lookback_period"].value
        
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
        shtraf = 1.0

        for i in range(len(df)):
            if i % percent == 0:
                self.manager.progress_changed.emit(int(i / len(df) * 100))

            if position_open:
                if df['low'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
                    close_price = df['Final Upperband'].iloc[i]
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance 
                    if shtraf < 1:
                        shtraf += antishtraf
                    if close_price / open_price > (1 + good_deal/100) and type == 1 or \
                       close_price / open_price < (1 - good_deal/100) and type == -1:
                        shtraf = 0
                elif df['high'].iloc[i] > df['Final Upperband'].iloc[i-1]:
                    close_price = df['Final Upperband'].iloc[i]
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance 
                    if shtraf < 1:
                        shtraf += antishtraf
                    if close_price / open_price > (1 + good_deal/100) and type == 1 or \
                       close_price / open_price < (1 - good_deal/100) and type == -1:
                        shtraf = 0

            else:
                if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                    posId = self.manager.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty * shtraf, df.index[i])
                    open_price = df['close'].iloc[i]
                    position_open = True
                    type = 1
                elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                    posId = self.manager.open_position('short', 'market', 0, 0, df['close'].iloc[i], qty * shtraf, df.index[i])
                    open_price = df['close'].iloc[i]
                    position_open = True
                    type = -1
