def ma50200_cross_strategy(self, df, initial_balance, position_size, position_type, profit_factor, leverage, commission):

    df['ma50'] = df['close'].rolling(window=50).mean()
    df['ma200'] = df['close'].rolling(window=200).mean()
    indicators = ['ma50', 'ma200']

    current_balance = initial_balance
    transactions = []
    percent = int(len(df) / 100)
    trade_open = False

    for i in range(len(df)):
        if i % percent == 0:
            self.progress_changed.emit(int(i / len(df) * 100))

        if trade_open:
            if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, tp, df.index[i], type, tp, sl, commission)
                trade_open = False           
            elif (df['low'].iloc[i] <= sl and type == 1) or (df['high'].iloc[i] >= sl and type == -1):
                transactions, current_balance = self.close(transactions, current_balance, position_size, leverage, open_price, open_time, sl, df.index[i], type, tp, sl, commission)
                trade_open = False

        if not trade_open:
            if df['ma50'].iloc[i-1] < df['ma200'].iloc[i-1] and df['ma50'].iloc[i] >= df['ma200'].iloc[i]:
                if position_type == "percent":
                    position_size = position_size / 100 * current_balance
                open_price = df['close'].iloc[i]
                open_time = df.index[i]
                type = 1
                tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                trade_open = True
            if df['ma50'].iloc[i-1] > df['ma200'].iloc[i-1] and df['ma50'].iloc[i] <= df['ma200'].iloc[i]:
                if position_type == "percent":
                    position_size = position_size / 100 * current_balance
                open_price = df['close'].iloc[i]
                open_time = df.index[i]
                type = -1
                tp, sl = self.get_tp_sl(df, i, open_price, profit_factor, type, 15)
                trade_open = True

    balance = self.calculate_balance(df, transactions, initial_balance, leverage)
    return transactions, balance, indicators
