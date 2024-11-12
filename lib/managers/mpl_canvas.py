import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.widgets import MultiCursor 
import numpy as np 
import matplotlib.style as mplstyle
mplstyle.use('fast')

class MPlCanvas(FigureCanvas):

    def __init__(self, facecolor, textcolor):
        self.fig, (self.ax1, self.ax3) = plt.subplots(2, 1, figsize=(18, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]}, facecolor=facecolor)
        
        # Вызов конструктора базового класса FigureCanvas
        super(MPlCanvas, self).__init__(self.fig)

        self.ax2 = self.ax1.twinx()
        self.ax4 = self.ax1.twinx()
        self.init_canvas(facecolor, textcolor)  # Инициализация настроек canvas

        self.ax1.yaxis.tick_right()
        self.ax1.yaxis.set_label_position("right")
        self.ax2.yaxis.tick_left()
        self.ax2.yaxis.set_label_position("left")
        self.ax3.yaxis.tick_right()
        self.ax3.yaxis.set_label_position("right")
        self.ax4.yaxis.tick_left()
        self.ax4.yaxis.set_label_position("left")


    def init_canvas(self, facecolor, textcolor):
        """Метод для инициализации или обновления цветов"""
        self.fig.patch.set_facecolor(facecolor)
        self.ax1.set_facecolor(facecolor)
        self.ax3.set_facecolor(facecolor)

        # Обновляем цвета для осей и текста
        self.ax1.tick_params(colors=textcolor, direction='out')
        for tick in self.ax1.get_xticklabels():
            tick.set_color(textcolor)
        for tick in self.ax1.get_yticklabels():
            tick.set_color(textcolor)

        self.ax3.tick_params(colors=textcolor, direction='out')
        for tick in self.ax3.get_xticklabels():
            tick.set_color(textcolor)
        for tick in self.ax3.get_yticklabels():
            tick.set_color(textcolor)

        plt.subplots_adjust(left=0, bottom=0.03, right=0.95, top=1, hspace=0.12)

        # Перерисовываем график
        plt.draw()

    def update_colors(self, facecolor, textcolor):
        """Метод для обновления цветов и перерисовки"""
        self.init_canvas(facecolor, textcolor)