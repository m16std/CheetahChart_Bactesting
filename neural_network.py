from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtWidgets import QFileDialog  # type: ignore
import pandas as pd # type: ignore
import numpy as np # type: ignore
import ta # type: ignore
from sklearn.preprocessing import MinMaxScaler  # type: ignore
from tensorflow.keras.models import Sequential  # type: ignore
from tensorflow.keras.layers import Dense, LSTM  # type: ignore
import matplotlib.dates as mdates # type: ignore

class AIManager:
    def __init__(self, app):
        self.app = app

    def create_dataset(self, dataset, time_step=1):
        X, Y = [], []
        for i in range(len(dataset) - time_step - 1):
            X.append(dataset[i:(i + time_step), 0])
            Y.append(dataset[i + time_step, 0])
        return np.array(X), np.array(Y)

    def train_ai(self):
        file_name, _ = QFileDialog.getOpenFileName(self.app, "Load Candlestick Data", "", "CSV Files (*.csv)")
        if file_name:
            self.app.df = pd.read_csv(file_name, index_col=0, parse_dates=True)
            print(f"Candlestick data loaded from {file_name}")

        self.app.df = self.app.df[::-1]
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(self.app.df['close'].values.reshape(-1, 1))

        time_step = 5
        X, Y = self.create_dataset(scaled_data, time_step)
        X = X.reshape(X.shape[0], X.shape[1], 1)

        # Обучение модели LSTM
        self.app.model = Sequential()
        self.app.model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 1)))
        self.app.model.add(LSTM(50, return_sequences=False))
        self.app.model.add(Dense(25))
        self.app.model.add(Dense(1))
        self.app.model.compile(optimizer='adam', loss='mean_squared_error')
        self.app.model.fit(X, Y, epochs=5, batch_size=1, verbose=1)

        self.app.file_handler.save_model_dialog()

    def predict_with_lstm(self, data):
        # Make predictions using the LSTM model
        predictions = []
        predicted_price = self.app.scaler.inverse_transform([[0]])
        predictions.append(predicted_price[0, 0])
        predicted_price = self.app.scaler.inverse_transform([[1]])
        predictions.append(predicted_price[0, 0])
        for i in range(50, len(data)):
            # Prepare the input for the LSTM model
            input_data = data[i-50:i].values.reshape((1, 50, 1))
            # Predict the next price
            predicted_price = self.app.model.predict(input_data)
            print(predicted_price)
            # Inverse the normalization
            predicted_price = self.app.scaler.inverse_transform(predicted_price)
            predictions.append(predicted_price[0, 0])
        return predictions

    def strategy_with_lstm(self, data):

        self.app.df = self.app.df[::-1]
        self.app.scaler = MinMaxScaler(feature_range=(0, 1))
        self.app.df_scaled = self.app.df
        self.app.df_scaled['scaled_close'] = self.app.scaler.fit_transform(self.app.df_scaled[['close']])
        scaled_data = self.app.df_scaled['scaled_close']
        predictions = self.predict_with_lstm(scaled_data)
        
        self.app.df['predicted_close'] = 0
        self.app.df.iloc[48:, self.app.df.columns.get_loc('predicted_close')] = predictions
        self.app.canvas.ax1.clear()
        self.app.canvas.ax2.clear()
        self.app.canvas.ax3.clear()
        self.app.df[['open', 'high', 'low', 'close']] = self.app.df[['open', 'high', 'low', 'close']].astype(float)
        candlestick_data = zip(mdates.date2num(self.app.df.index.to_pydatetime()), self.app.df['open'], self.app.df['high'], self.app.df['low'], self.app.df['close'])
        for date, open, high, low, close in candlestick_data:
            color = '#089981' if close >= open else '#F23645'
            self.app.canvas.ax1.plot([date, date], [low, high], color=color, linewidth=0.8)
            self.app.canvas.ax1.plot([date, date], [open, close], color=color, linewidth=2)

        self.app.canvas.ax1.scatter(self.app.df.index.to_pydatetime(), self.app.df['predicted_close'], label='Predicted Close Price', color='orange', s=8)
        self.app.canvas.draw()
        self.app.show()
        return data
    
    def run_ai(self):
        self.app.file_handler.load_model_dialog()
        file_name, _ = QFileDialog.getOpenFileName(self.app, "Load Candlestick Data", "", "CSV Files (*.csv)")
        if file_name:
            self.app.df = pd.read_csv(file_name, index_col=0, parse_dates=True)
            print(f"Candlestick data loaded from {file_name}")

        #scaler = MinMaxScaler(feature_range=(0, 1))
        #scaled_data = scaler.fit_transform(self.df['close'].values.reshape(-1, 1))
        self.strategy_with_lstm(self.app.df)
    

        """Открывает диалоговое окно для загрузки модели."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self.app, "Загрузить модель", "", "Model Files (*.pkl);;All Files (*)", options=options)
        if file_name:
            self.app.model = self.app.load_model(file_name)
            # Теперь можно использовать загруженную модель
