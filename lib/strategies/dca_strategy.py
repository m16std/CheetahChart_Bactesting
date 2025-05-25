from .base_strategy import BaseStrategy
import ta

class DCAStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "DCA Strategy"
        self.description = "Dollar Cost Averaging strategy with MACD signals"

    def _setup_parameters(self):
        self.add_parameter(
            "orders_count", 
            20, 
            "DCA orders",
            int,
            min_value=2,
            max_value=50
        )
        self.add_parameter(
            "price_gap", 
            3, 
            "Orders gap (%)",
            float,
            min_value=0.1,
            max_value=20
        )
        self.add_parameter(
            "tp_gap", 
            3, 
            "Take profit gap (%)",
            float,
            min_value=0.1,
            max_value=20
        )
        self.add_parameter(
            "fast_period", 
            12, 
            "MACD fast period",
            int,
            min_value=2,
            max_value=50
        )
        self.add_parameter(
            "slow_period", 
            26, 
            "MACD slow period",
            int,
            min_value=5,
            max_value=100
        )
        self.add_parameter(
            "signal_period", 
            9, 
            "MACD signal period",
            int,
            min_value=2,
            max_value=25
        )

    def find_mid_open_price(self, open_prices, positions_count):
        mid_open_price = sum(open_prices[:positions_count]) / positions_count
        return mid_open_price

    def run(self, df, initial_balance, position_size, position_type, profit_factor):
        orders = int(self.parameters["orders_count"].value)  # Добавлено приведение к int
        gap = self.parameters["price_gap"].value / 100
        tp_gap = self.parameters["tp_gap"].value / 100
        fast_period = self.parameters["fast_period"].value
        slow_period = self.parameters["slow_period"].value
        signal_period = self.parameters["signal_period"].value

        macd = ta.trend.MACD(
            df['close'],
            window_fast=fast_period,
            window_slow=slow_period,
            window_sign=signal_period
        )
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        self.manager.indicators = ['macd', 'macd_signal']
        
        current_balance = initial_balance
        qty = position_size
        if position_type == "percent":
            qty = position_size / 100 * current_balance
        
        percent = int(len(df) / 100)
        position_open = False
        open_prices = []
        posId = []
        mid_open_price = 0

        for i in range(len(df)):
            if i % percent == 0:
                self.manager.progress_changed.emit(int(i / len(df) * 100))

            if position_open:
                if (df['high'].iloc[i] >= tp and type == 1) or (df['low'].iloc[i] <= tp and type == -1):
                    for pos_id in posId:
                        self.manager.close_position(pos_id, tp, df.index[i])
                    position_open = False
                    current_balance = self.manager.get_current_balance()
                    open_prices = []
                    posId = []
                    mid_open_price = 0

            if not position_open:
                if df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                    posId.append(self.manager.open_position('long', 'market', 0, 0, df['close'].iloc[i], qty/orders, df.index[i]))
                    open_prices.append(df['close'].iloc[i])
                    for j in range(1, orders):
                        open_prices.append(open_prices[-1] * (1.0 - gap))
                    mid_open_price = df['close'].iloc[i]
                    type = 1
                    tp = mid_open_price * (1.0 + tp_gap)
                    position_open = True
                
                elif df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and df['macd'].iloc[i] < df['macd_signal'].iloc[i]:
                    posId.append(self.manager.open_position('short', 'market', 0, 0, df['close'].iloc[i], qty/orders, df.index[i]))
                    open_prices.append(df['close'].iloc[i])
                    for j in range(1, orders):
                        open_prices.append(open_prices[-1] * (1.0 + gap))
                    mid_open_price = df['close'].iloc[i]
                    type = -1
                    tp = mid_open_price * (1.0 - tp_gap)
                    position_open = True

            if len(posId) < orders - 1 and position_open:
                if df['low'].iloc[i] < open_prices[len(posId)] and type == 1:
                    posId.append(self.manager.open_position('long', 'market', 0, 0, open_prices[len(posId)], qty/orders, df.index[i]))
                    mid_open_price = self.find_mid_open_price(open_prices, len(posId))
                    tp = mid_open_price * (1.0 + gap)
                elif df['high'].iloc[i] > open_prices[len(posId)] and type == -1:
                    posId.append(self.manager.open_position('short', 'market', 0, 0, open_prices[len(posId)], qty/orders, df.index[i]))
                    mid_open_price = self.find_mid_open_price(open_prices, len(posId))
                    tp = mid_open_price * (1.0 - gap)

            if len(posId) == orders - 1:
                for pos_id in posId:
                    self.manager.close_position(pos_id, df['close'].iloc[i], df.index[i])
                position_open = False
                open_prices = []
                posId = []
                mid_open_price = 0
