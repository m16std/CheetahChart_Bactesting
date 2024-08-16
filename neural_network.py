from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtWidgets import QFileDialog  # type: ignore
import pandas as pd # type: ignore
import numpy as np # type: ignore
import ta # type: ignore
from sklearn.preprocessing import MinMaxScaler  # type: ignore
import tensorflow as tf  # type: ignore
from tensorflow.keras.models import Sequential  # type: ignore
from tensorflow.keras.layers import Dense, LSTM  # type: ignore
import matplotlib.dates as mdates # type: ignore
from keras.models import Sequential # type: ignore
from keras.layers import LSTM, Dense, Dropout, Input # type: ignore
from tensorflow.keras.losses import MeanSquaredError # type: ignore


class AIManager:
    def __init__(self, app):
        self.app = app
    
    def create_lstm_model(self, input_shape):
        model = Sequential()
        model.add(Input(shape=input_shape))
        model.add(LSTM(50, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(50, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(50, activation='relu'))
        model.add(Dense(3))  # Три выхода: направление, тейк-профит, стоп-лосс
        model.compile(optimizer='adam', loss=self.custom_loss)
        return model

    def custom_loss(self, y_true, y_pred):
        direction_true, take_profit_true, stop_loss_true = tf.split(y_true, num_or_size_splits=3, axis=-1)
        direction_pred, take_profit_pred, stop_loss_pred = tf.split(y_pred, num_or_size_splits=3, axis=-1)
        
        # Приведение предсказаний направления сделки к нужной форме
        direction_pred = tf.squeeze(direction_pred, axis=-1)

        # Функции потерь для каждого выхода
        loss_direction = tf.keras.losses.BinaryCrossentropy()(direction_true, direction_pred)
        loss_tp = MeanSquaredError()(take_profit_true, take_profit_pred)
        loss_sl = MeanSquaredError()(stop_loss_true, stop_loss_pred)
        
        # Комбинированная функция потерь
        loss = loss_direction + loss_tp + loss_sl
        return loss

    def train_model(self):
        epochs=10
        batch_size=32
        self.app.file_handler.load_candlesticks()
        self.app.X, self.app.y = self.prepare_data()
        input_shape = (self.app.X.shape[1], self.app.X.shape[2])
        model = self.create_lstm_model(input_shape)
        model.fit(self.app.X, self.app.y, epochs=epochs, batch_size=batch_size)
        self.app.model = model
        self.app.file_handler.save_model_dialog()
    
    def predict_with_lstm(self, data):
        # Предсказание
        predictions = self.model.predict(data)
        direction_pred = (predictions[:, 0] > 0.5).astype(int)
        take_profit_pred = predictions[:, 1]
        stop_loss_pred = predictions[:, 2]
        return direction_pred, take_profit_pred, stop_loss_pred


    # Загружаем данные и вычисляем индикаторы
    def prepare_data(self):
        self.app.df['RSI'] = ta.momentum.RSIIndicator(self.app.df['close'], window=14).rsi()
        self.app.df['MACD'] = ta.trend.MACD(self.app.df['close']).macd()
        self.app.df['Signal_Line'] = ta.trend.MACD(self.app.df['close']).macd_signal()
        self.app.df['MA50'] = ta.trend.SMAIndicator(self.app.df['close'], window=50).sma_indicator()
        self.app.df['MA200'] = ta.trend.SMAIndicator(self.app.df['close'], window=200).sma_indicator()

        # Убираем строки с NaN
        self.app.df.dropna(inplace=True)

        # Используем нужные колонки в качестве признаков
        feature_columns = ['RSI', 'MACD', 'Signal_Line', 'MA50', 'MA200']
        data = self.app.df[feature_columns].values

        # Нормализация данных
        self.app.scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = self.app.scaler.fit_transform(data)

        # Подготовка данных для LSTM
        X = []
        y = []
        lookback = 50

        for i in range(lookback, len(scaled_data)):
            X.append(scaled_data[i-lookback:i])
            y.append(self.app.df['close'].values[i])

        X, y = np.array(X), np.array(y)

        return X, y

    def strategy_with_lstm(self):
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
    
    def run_ai(self):
        self.app.file_handler.load_model_dialog()
        self.app.file_handler.load_candlesticks()

        self.strategy_with_lstm()
