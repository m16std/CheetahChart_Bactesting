from lib.strategies.base_strategy import BaseStrategy
import ta
import numpy as np

class New_Strategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "New_Strategy"
        self.description = "Strategy generated from visual constructor"

    def _setup_parameters(self):
        self.add_parameter(
            "rsi_period",
            14,
            "RSI Period",
            int,
            min_value=2,
            max_value=50
        )
        self.add_parameter(
            "const_0x17d777ac0",
            15,
            "Constant Value",
            float,
            min_value=0,
            max_value=100
        )
        self.add_parameter(
            "const_0x17d777c40",
            30,
            "Constant Value",
            float,
            min_value=0,
            max_value=100
        )
        self.add_parameter(
            "const_0x17d777ee0",
            70,
            "Constant Value",
            float,
            min_value=0,
            max_value=100
        )

    def run(self, df, initial_balance, position_size, position_type, profit_factor):
        # Initialize parameters
        rsi_period = self.parameters['rsi_period'].value
        const_0x17d777ac0 = self.parameters['const_0x17d777ac0'].value
        const_0x17d777c40 = self.parameters['const_0x17d777c40'].value
        const_0x17d777ee0 = self.parameters['const_0x17d777ee0'].value
        df['rsi_0x17d776ce0'] = ta.momentum.RSIIndicator(df["close"], window=rsi_period).rsi()
        self.manager.indicators = ['rsi_0x17d776ce0']

        current_balance = initial_balance
        qty = position_size
        if position_type == "percent":
            qty = position_size / 100 * current_balance
        percent = int(len(df) / 100)
        position_open = False
        posId = None

        for i in range(len(df)):
            if i % percent == 0:
                self.manager.progress_changed.emit(int(i / len(df) * 100))

            if not position_open:
                if df['rsi_0x17d776ce0'].iloc[i] < const_0x17d777c40:
                    posId = self.manager.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
            else:
                if df['rsi_0x17d776ce0'].iloc[i] > const_0x17d777ee0:
                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    if position_type == "percent":
                        qty = position_size / 100 * current_balance