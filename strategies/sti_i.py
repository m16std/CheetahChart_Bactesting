def supertrend_strategy_imp(self, df, initial_balance, position_size, position_type, profit_factor):
    period = 10
    multiplier = 1

    sti = self.Supertrend(df, period, multiplier)
    df['Final Lowerband'] = sti['Final Lowerband']
    df['Final Upperband'] = sti['Final Upperband']
    df['Supertrend'] = sti['Supertrend']
    indicators = ['Final Lowerband', 'Final Upperband']

    current_balance = qty = initial_balance
    if position_type == "percent":
        qty = position_size / 100 * current_balance
    percent = int(len(df) / 100)
    position_open = False

    for i in range(len(df)):
        if i % percent == 0:
            self.progress_changed.emit(int(i / len(df) * 100))

        if position_open:
            if df['Supertrend'].iloc[i-1] != df['Supertrend'].iloc[i]:
                self.close_position(posId, df['close'].iloc[i], df.index[i])
                position_open = False
                current_balance = self.get_current_balance()
                if position_type == "percent":
                    qty = position_size / 100 * current_balance

        if not position_open:
            if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:              
                posId = self.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                position_open = True
            if df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                posId = self.open_position('short', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])
                position_open = True

    return indicators