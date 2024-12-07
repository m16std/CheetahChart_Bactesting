import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input, Dropout
from tensorflow.keras.callbacks import Callback

# Создание простой нейронной сети для примера
def create_model():
    model = Sequential([
        Input(shape=(10,)),  # 10 входов
        Dense(5, activation='relu'),  # Скрытый слой из 5 нейронов
        Dropout(0.5),
        Dense(5, activation='relu'),  # Скрытый слой из 5 нейронов
        Dense(3, activation='relu'),  # Еще один скрытый слой из 3 нейронов
        Dense(1, activation='sigmoid')  # Выход
    ])
    return model

# Генерация тестовых данных
X = np.random.rand(100, 10)  # 100 образцов с 10 входами
y = np.random.randint(0, 2, 100)  # Бинарные выходы

# Создание модели
model = create_model()
model.compile(optimizer='adam', loss='binary_crossentropy')





# PyQt приложение
app = QtWidgets.QApplication([])

# Основное окно
win = pg.GraphicsLayoutWidget()
win.setWindowTitle('Visualization of Neural Network Weights')
win.show()

# Создание графика
plot = win.addPlot(title="Neural Network Visualization")

# Параметры нейронной сети
layer_sizes = [10, 5, 5, 3, 1]  # Количество нейронов на каждом слое
neuron_positions = []
connections = []

# Расположение нейронов
x_spacing = 1.0
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

# Функция обновления весов
def update_weights(epoch, logs):
    for line, layer_idx, src_idx, dst_idx in connections:
        weights = model.layers[layer_idx].get_weights()[0]  # Извлечение весов
        weight = weights[src_idx, dst_idx]
        alpha = int(min(255, max(0, abs(weight) * 255)))  # Прозрачность на основе веса
        line.setPen(pg.mkPen((200, 50, 50, alpha), width=2))  # Цветовая шкала

# Подключение колбэка для визуализации
class WeightVisualizerCallback(Callback):
    def on_epoch_end(self, epoch, logs=None):
        update_weights(epoch, logs)
        app.processEvents()  # Обновить PyQt графику

# Обучение модели с визуализацией
model.fit(X, y, epochs=100, batch_size=10, callbacks=[WeightVisualizerCallback()])

# Запуск приложения
app.exec()
