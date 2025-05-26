from lib.strategies.base_strategy import BaseStrategy  # Changed to absolute import
import ta

class RSI_Strategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "RSI Strategy"
        self.description = "Strategy based on RSI indicator overbought/oversold levels"

    def _setup_parameters(self):
        self.add_parameter(
            "rsi_period", 
            14, 
            "RSI calculation period",
            int,
            min_value=5,
            max_value=50
        )
        self.add_parameter(
            "overbought", 
            70, 
            "Overbought level",
            int,
            min_value=50,
            max_value=90
        )
        self.add_parameter(
            "oversold", 
            30, 
            "Oversold level",
            int,
            min_value=10,
            max_value=50
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
        rsi_period = self.parameters["rsi_period"].value
        overbought = self.parameters["overbought"].value
        oversold = self.parameters["oversold"].value
        lookback_period = self.parameters["lookback_period"].value

        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=rsi_period).rsi()
        df['overbought'] = overbought
        df['oversold'] = oversold
        
        self.manager.indicators = ['rsi', 'overbought', 'oversold']

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
                if df['rsi'].iloc[i-1] < oversold and df['rsi'].iloc[i] >= oversold:
                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', lookback_period)
                    posId = self.manager.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
                if df['rsi'].iloc[i-1] > overbought and df['rsi'].iloc[i] <= overbought:
                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', lookback_period)
                    posId = self.manager.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                    position_open = True
