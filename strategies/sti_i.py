def supertrend_strategy_imp(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):
    period = 10
    multiplier = 1

    sti = self.Supertrend(df, period, multiplier)
    df['Final Lowerband'] = sti['Final Lowerband']
    df['Final Upperband'] = sti['Final Upperband']
    df['Supertrend'] = sti['Supertrend']
    indicators = ['Final Lowerband', 'Final Upperband']

    current_balance = initial_balance
    transactions = []
    percent = int(len(df) / 100)
    trade_open = False
    ordType = 'market'

    for i in range(len(df)):
        if i % percent == 0:
            self.progress_changed.emit(int(i / len(df) * 100))
        if trade_open:
            if df['Supertrend'].iloc[i-1] != df['Supertrend'].iloc[i]:
                transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, df['close'].iloc[i], df.index[i], type, 0, 0, commission)
                trade_open = False

        if not trade_open:
            if df['Supertrend'].iloc[i-1] < df['Supertrend'].iloc[i]:
                if position_type == "percent":
                    position_size = position_size / 100 * current_balance
                open_price = df['close'].iloc[i]
                open_time = df.index[i]
                posSide = 'long'
                trade_open = True
            elif df['Supertrend'].iloc[i-1] > df['Supertrend'].iloc[i]:
                if position_type == "percent":
                    position_size = position_size / 100 * current_balance
                open_price = df['close'].iloc[i]
                open_time = df.index[i]
                posSide = 'short'
                trade_open = True

    return indicators
