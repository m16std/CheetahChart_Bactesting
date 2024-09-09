from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtWidgets import QFileDialog  # type: ignore
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import pandas as pd # type: ignore
import numpy as np # type: ignore
import ta # type: ignore
from sklearn.preprocessing import MinMaxScaler  # type: ignore
import tensorflow as tf  # type: ignore
from tensorflow.keras.models import Sequential  # type: ignore
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input # type: ignore
import matplotlib.dates as mdates # type: ignore
import matplotlib.pyplot as plt
from tensorflow.keras.losses import MeanSquaredError # type: ignore
from sklearn.model_selection import train_test_split # type: ignore
from tensorflow.keras.callbacks import EarlyStopping # type: ignore
from sklearn.preprocessing import MinMaxScaler  # type: ignore
from tensorflow.keras.models import Sequential  # type: ignore
from tensorflow.keras.layers import Dense, LSTM  # type: ignore

class AIManager:
    def __init__(self, app):
        self.app = app
    
    def calculate_best_trades(self, df, lookahead, min_movement):
        df = df.copy()  # создаем копию, чтобы не изменять оригинальный DataFrame
        
        # Проверяем, что DataFrame не пустой
        if df.empty:
            raise ValueError("DataFrame пустой. Проверьте загрузку данных.")
        
        # Проверяем, какие индексы у DataFrame
        if not isinstance(df.index, pd.RangeIndex):
            df = df.reset_index(drop=True)

        for i in range(len(df) - lookahead):
            current_close = df.loc[i, 'close']
            max_future_price = df.loc[i:i + lookahead, 'high'].max()
            min_future_price = df.loc[i:i + lookahead, 'low'].min()
            
            upward_movement = (max_future_price - current_close) / current_close * 100
            downward_movement = (current_close - min_future_price) / current_close * 100
            
            if upward_movement > downward_movement:
                df.loc[i, 'order'] = 1 * upward_movement / (downward_movement+0.1)
            else:
                df.loc[i, 'order'] = -1 * downward_movement / (upward_movement+0.1)

        for i in range(len(df) - lookahead, len(df)):
            df.loc[i, 'order'] = 0

        srednee = 0
        mse = 0

        for i in range (len(df)):
            srednee += df['order'].iloc[i]
        srednee/=len(df)

        for i in range (len(df)):
            mse += (srednee-df['order'].iloc[i])*(srednee-df['order'].iloc[i])
        mse/=len(df)

        print('Если loss: '+str(mse)+' то нейронка не работает')
        
        return df

    def create_lstm_model(self, input_shape):
        model = Sequential()
        model.add(Input(shape=input_shape))
        model.add(LSTM(64, return_sequences=True))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(1)) 

        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def train_model(self):
        epochs=50
        batch_size=1
        lookback=5

        if not self.app.file_handler.load_candlesticks():
            return
        
        print('Добавление индикаторов')
        self.app.df = self.calculate_indicators(self.app.df)

        print('Рассчет сделок для обучения')
        self.app.df = self.calculate_best_trades(self.app.df, lookahead=2, min_movement=1)

        print(self.app.df['order'])

        print('Сортировка данных')
        x, y = self.prepare_training_data(self.app.df, n_candles=lookback)

        input_shape = (lookback, 5)
        self.app.model = self.create_lstm_model(input_shape)     

        print('Обучение нейронки')
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
        history = self.app.model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(x_test,y_test), verbose=1, callbacks=[WeightsVisualizer(self)])

        self.app.file_handler.save_model_dialog()

        direction= self.predict_next_action(self.app.df, n_candles = 5)
        print(f"Направление сделки: {direction}")

    def predict(self, X):
        return self.app.model.predict(X)
    
    def predict_next_action(self, df, n_candles):
        # Рассчитываем индикаторы для последних n_candles
        indicators = df[['rsi','atr','ma_50','ma_200', 'ma_div']].iloc[-n_candles:].values
        indicators = indicators.reshape(1, n_candles, indicators.shape[1])

        # Прогнозируем направление сделки, стоп-лосс и тейк-профит
        prediction = self.predict(indicators)

        direction = prediction[0]  # Направление сделки

        return direction
    
    def calculate_indicators(self, df):
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
        df['ma_50'] = (df['close'].rolling(window=50, closed='right').mean() / df['close'].rolling(window=50, closed='left').mean() - 1)  * 50
        df['ma_200'] = (df['close'].rolling(window=200, closed='right').mean() / df['close'].rolling(window=200, closed='left').mean() - 1) * 200
        df['ma_div'] = (df['close'].rolling(window=200).mean() / df['close'].rolling(window=50).mean() - 1)  * 2
        
        df['ma50'] = df['close'].rolling(window=50).mean()
        df['ma200'] = df['close'].rolling(window=200).mean()

        self.app.canvas.ax1.plot(df.index, df['close'], label='price', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['ma_50'], label='ma_50', color='red', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['ma_200'], label='ma_200', color='white', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['ma_div'], label='ma_div', color='yellow', alpha=0.5)
        self.app.canvas.ax1.plot(df.index, df['ma50'], label='ma50', color='green', alpha=0.5)
        self.app.canvas.ax1.plot(df.index, df['ma200'], label='ma200', color='green', alpha=0.5)
        """
        self.app.canvas.ax1.plot(df.index, df['close'], label='price', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['rsi'], label='rsi', color='green', alpha=0.5)
        self.app.canvas.ax1.plot(df.index, df['ma_50'], label='ma_50', color='red', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['ma_200'], label='ma_200', color='white', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['ma50-price'], label='ma50-price', color='blue', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['ma50_incline'], label='ma50_incline', color='yellow', alpha=0.5)
        self.app.canvas.ax2.plot(df.index, df['ma_50-ma_200'], label='ma_50-ma_200', color='pink', alpha=0.5)
        """
        self.app.canvas.draw()
        self.app.show()
        
        #добавить показатель наклона скользящих средних

        df.dropna(inplace=True)
        return df
    
    def prepare_training_data(self, df, n_candles):
        X = []
        y = []

        for i in range(n_candles, len(df)):
            # Входные данные: последние n_candles значений индикаторов
            indicators = df[['rsi','atr','ma_50','ma_200', 'ma_div']].iloc[i-n_candles:i].values
            X.append(indicators)

            # Выходные данные: направление сделки (order)
            y.append(df[['order']].iloc[i].values)

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
        for date, open, high, low, close in candlestick_data:
            color = '#089981' if close >= open else '#F23645'
            self.app.canvas.ax1.plot([date, date], [low, high], color=color, linewidth=0.8)
            self.app.canvas.ax1.plot([date, date], [open, close], color=color, linewidth=2)

        self.app.df['predicted_close'] = 0

        #self.app.df.iloc[300:, self.app.df.columns.get_loc('predicted_close')] = predictions
        #self.app.canvas.ax1.plot(np.arange(50, len(predictions)+50), predictions, label='Predicted Price')
        #self.app.canvas.ax1.scatter(self.app.df.index.to_pydatetime(), self.app.df['predicted_close'], label='Predicted Close Price', color='orange', s=8)
        self.app.canvas.draw()
        self.app.show()
        """
        direction= self.predict_next_action(self.calculate_indicators(self.app.df), n_candles = 5)
        print(f"Направление сделки: {direction}")

    
    def run_ai(self):
        if self.app.file_handler.load_model_dialog():
            if self.app.file_handler.load_candlesticks():
                self.strategy_with_lstm()

class WeightsVisualizer(tf.keras.callbacks.Callback):
    def __init__(self, app):
        self.app = app

    def on_epoch_end(self, epoch, logs=None):
        # Получаем веса из первого слоя модели
        weights = self.model.layers[0].get_weights()[0]
        
        # Визуализируем веса
        self.app.app.canvas.ax2.imshow(weights, cmap='viridis', aspect='auto')
        self.app.app.canvas.ax2.colorbar()
        self.app.app.canvas.ax2.title(f'Weights after epoch {epoch + 1}')
        self.app.app.canvas.ax2.xlabel('Neurons')
        self.app.app.canvas.ax2.ylabel('Features')
        self.app.app.canvas.draw()
        self.app.app.show()