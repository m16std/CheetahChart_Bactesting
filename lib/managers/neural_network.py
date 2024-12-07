from PyQt5.QtGui import *  
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import numpy as np # type: ignore
import ta # type: ignore
from sklearn.model_selection import train_test_split # type: ignore
from tensorflow.keras.models import Sequential  # type: ignore
from PyQt5.QtCore import QThread, pyqtSignal
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input, Dropout
from tensorflow.keras.callbacks import Callback


class AIManager(QThread):
    training_complete = pyqtSignal(object)
    plot_some = pyqtSignal(object, object, object, object)

    def __init__(self, parent=None):
        super(AIManager, self).__init__(parent)
        self.df = [] 

    def run(self):
        # Запускаем метод скачивания данных с переданными параметрами
        self.train_model()
        self.training_complete.emit(self.model)
    
    def calculate_best_trades(self, df, lookahead):
        df = df.copy()  # создаем копию, чтобы не изменять оригинальный DataFrame
        
        # Проверяем, что DataFrame не пустой
        if df.empty:
            raise ValueError("DataFrame пустой. Проверьте загрузку данных.")
        
        df['order'] = df['close'] * 0
        df['upward_movement'] = df['close'] * 0
        df['downward_movement'] = df['close'] * 0

        for i in range(len(df) - lookahead):
            current_close = df['close'].iloc[i]
            max_future_price = df['high'].iloc[i:i + lookahead].max()
            min_future_price = df['low'].iloc[i:i + lookahead].min()
            
            upward_movement = (max_future_price - current_close) / current_close * 100
            downward_movement = (current_close - min_future_price) / current_close * 100
            """
            if upward_movement > downward_movement*2:
                df.loc[i, 'order'] = 1
            elif upward_movement*2 < downward_movement:
                df.loc[i, 'order'] = -1
            else:
                df.loc[i, 'order'] = 0
            
            """
            
            df['order'].iloc[i] = upward_movement - downward_movement

            df['upward_movement'].iloc[i] = upward_movement 
            df['downward_movement'].iloc[i] = downward_movement


        srednee = 0
        mse = 0

        for i in range (len(df)):
            srednee += df['order'].iloc[i]
        srednee/=len(df)

        for i in range (len(df)):
            mse += (srednee-df['order'].iloc[i])**2
        mse/=len(df)

        print('Если loss order: '+str(mse)+' то нейронка не работает')

        srednee_1 = 0
        srednee_2 = 0
        mse_1 = 0
        mse_2 = 0

        for i in range (len(df)):
            srednee_1 += df['upward_movement'].iloc[i]
            srednee_2 += df['downward_movement'].iloc[i]
        srednee_1/=len(df)
        srednee_2/=len(df)

        for i in range (len(df)):
            mse_1 += (srednee_1-df['upward_movement'].iloc[i])**2
        mse_1/=len(df)
        for i in range (len(df)):
            mse_2 += (srednee_2-df['downward_movement'].iloc[i])**2
        mse_2/=len(df)

        print('Если loss up/down: '+str(mse_1 + mse_2)+' то нейронка не работает')
        
        return df

    def create_lstm_model(self, input_shape):
        model = Sequential()
        model.add(Input(shape=input_shape))
        #model.add(Dropout(0.5))
        #model.add(Dense(16, activation='relu'))
        #model.add(Dropout(0.5))
        model.add(Dense(8, activation='relu'))
        model.add(Dense(2)) 

        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def train_model(self):
        epochs=10
        batch_size=1
        lookback=1
        lookahead=5

        print('Добавление индикаторов')
        self.df = self.calculate_indicators(self.df)

        print('Рассчет сделок для обучения')
        self.df = self.calculate_best_trades(self.df, lookahead=lookahead)

        print(self.df)
        #self.plot_some.emit(self.df, [], [], ['rsi', 'atr', 'ma_50', 'ma_200', 'ma_div', 'order'])

        print('Группировка данных')
        x, y = self.prepare_training_data(self.df, n_candles=lookback)

        X = []
        for i in range(len(x)):
            X.append(x[0].flatten())

        X = np.array(X)    

   
        input_shape = (lookback*5,) # 5 - число индикаторов
        self.model = self.create_lstm_model(input_shape)     



        app = QtWidgets.QApplication([])

        # Основное окно
        win = pg.GraphicsLayoutWidget()
        win.setWindowTitle('Visualization of Neural Network Weights')
        win.show()

        # Создание графика
        plot = win.addPlot(title="Neural Network Visualization")

        # Параметры нейронной сети
        layer_sizes = [lookback*5, 8, 2]  # Количество нейронов на каждом слое
        neuron_positions = []
        connections = []

        # Расположение нейронов
        x_spacing = 10.0
        y_spacing = 2.0

        for i, layer_size in enumerate(layer_sizes):
            x = i * x_spacing
            positions = [(x, y * y_spacing - (layer_size * y_spacing) / 2) for y in range(layer_size)]
            neuron_positions.append(positions)

        # Создание графических элементов
        for i in range(len(layer_sizes) - 1):
            for src_idx, src_pos in enumerate(neuron_positions[i]):
                for dst_idx, dst_pos in enumerate(neuron_positions[i + 1]):
                    line = pg.LineSegmentROI([src_pos, dst_pos], pen=pg.mkPen((200, 200, 200, 50), width=2))
                    connections.append((line, i, src_idx, dst_idx))
                    plot.addItem(line)

        # Отрисовка нейронов
        for layer in neuron_positions:
            for pos in layer:
                circle = pg.ScatterPlotItem([pos[0]], [pos[1]], size=15, brush=pg.mkBrush(50, 150, 255, 200))
                plot.addItem(circle)

        # Подключение колбэка для визуализации
        class WeightVisualizerCallback(Callback):
            def on_epoch_end(self, epoch, logs=None):
                for line, layer_idx, src_idx, dst_idx in connections:
                    if not isinstance(self.model.layers[layer_idx], Dense):
                        weight = 1
                    else:
                        weights = self.model.layers[layer_idx].get_weights()[0]  # Извлечение весов
                        weight = weights[src_idx, dst_idx]
                    alpha = int(min(255, max(0, abs(weight) * 255)))  # Прозрачность на основе веса
                    if weight > 0: 
                        line.setPen(pg.mkPen((200, 50, 50, alpha), width=2))  # Цветовая шкала
                    else:
                        line.setPen(pg.mkPen((0, 0, 250, alpha), width=2))  # Цветовая шкала
                app.processEvents()  # Обновить PyQt графику

        print('Обучение нейронки')
        x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        history = self.model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(x_test,y_test), verbose=1, callbacks=[WeightVisualizerCallback()])

        #direction= self.predict_next_action(self.df, n_candles = lookback)
        #print(f"Направление сделки: {direction}")


    def predict_next_action(self, df, n_candles):
        # Рассчитываем индикаторы для последних n_candles
        indicators = df[['rsi','atr','ma_50','ma_200', 'ma_div']].iloc[-n_candles:].values
        print(indicators)
        indicators = indicators.reshape(1, n_candles, indicators.shape[1])
        print(indicators)
        # Прогнозируем направление сделки, стоп-лосс и тейк-профит
        prediction = self.model.predict(indicators)

        direction = prediction[0]  # Направление сделки

        return direction
    
    def calculate_indicators(self, df):
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
        df['ma_50'] = (df['close'].rolling(window=50, closed='right').mean() / df['close'].rolling(window=50, closed='left').mean() - 1)  * 50
        df['ma_200'] = (df['close'].rolling(window=200, closed='right').mean() / df['close'].rolling(window=200, closed='left').mean() - 1) * 200
        df['ma_div'] = (df['close'].rolling(window=200).mean() / df['close'].rolling(window=50).mean() - 1)  * 2
        df = df.dropna(subset=['rsi','atr','ma_50','ma_200', 'ma_div'])

        return df
    
    def prepare_training_data(self, df, n_candles):
        X = []
        y = []

        for i in range(n_candles, len(df)):
            # Входные данные: последние n_candles значений индикаторов
            indicators = df[['rsi','atr','ma_50','ma_200', 'ma_div']].iloc[i-n_candles:i].values
            X.append(indicators)

            # Выходные данные: направление сделки (order)
            #y.append(df[['order']].iloc[i].values)
            y.append(df[['upward_movement', 'downward_movement']].iloc[i].values)


        X = np.array(X)
        y = np.array(y)

        return X, y

    def strategy_with_lstm(self):
        """
        self.app.X, self.app.y = self.prepare_data()
        direction, tp, sl = self.predict_with_lstm(self.app.X)
        
        # Логика использования предсказаний (например, нанесение их на график)
        self.df.loc[50:, 'direction'] = direction
        self.df.loc[50:, 'take_profit'] = tp
        self.df.loc[50:, 'stop_loss'] = sl
        
        self.app.canvas.ax1.clear()
        self.app.canvas.ax2.clear()
        self.app.canvas.ax3.clear()
        candlestick_data = zip(mdates.date2num(self.app.df.index.to_pydatetime()), self.app.df['open'], self.app.df['high'], self.app.df['low'], self.app.df['close'])


        self.app.df['predicted_close'] = 0

        #self.app.df.iloc[300:, self.app.df.columns.get_loc('predicted_close')] = predictions
        #self.app.canvas.ax1.plot(np.arange(50, len(predictions)+50), predictions, label='Predicted Price')
        #self.app.canvas.ax1.scatter(self.app.df.index.to_pydatetime(), self.app.df['predicted_close'], label='Predicted Close Price', color='orange', s=8)
        self.app.canvas.draw()
        self.app.show()
        """
        direction= self.predict_next_action(self.calculate_indicators(self.df), n_candles = 30)
        print(f"Направление сделки: {direction}")
  
    def run_ai(self):
        if self.app.file_handler.load_model_dialog():
            if self.app.file_handler.load_candlesticks():
                self.strategy_with_lstm()

    def on_epoch_end(self):
        # Получаем веса из первого слоя модели
        weights = self.model.layers[0].get_weights()[0]
        print(weights)

