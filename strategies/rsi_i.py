import ta
def rsi_strategy_imp(self, df, initial_balance, position_size, position_type, profit_factor):

    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['70'] = 70
    df['30'] = 30
    indicators = ['rsi', '70', '30']

    current_balance = qty = initial_balance
    if position_type == "percent":
        qty = position_size / 100 * current_balance
    percent = int(len(df) / 100)
    position_open = False

    for i in range(len(df)):
        if i % percent == 0:
            self.progress_changed.emit(int(i / len(df) * 100))

        if position_open:
            if self.check_tp_sl(posId, tpTriggerPx, slTriggerPx, df.index[i]):
                position_open = False
                current_balance = self.get_current_balance()
                if position_type == "percent":
                    qty = position_size / 100 * current_balance

        if not position_open:
            if df['rsi'].iloc[i-1] < 30 and df['rsi'].iloc[i] >= 30:              
                tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'long', 15)
                posId = self.open_position('long', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                position_open = True
            if df['rsi'].iloc[i-1] > 70 and df['rsi'].iloc[i] <= 70:
                tpTriggerPx, slTriggerPx = self.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, 'short', 15)
                posId = self.open_position('short', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])
                position_open = True

    return indicators