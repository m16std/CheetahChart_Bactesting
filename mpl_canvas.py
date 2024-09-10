import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt # type: ignore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas # type: ignore


class MPlCanvas(FigureCanvas):

    def __init__(self, facecolor, textcolor):
        self.fig, (self.ax1, self.ax3) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]}, facecolor=facecolor)

        # Вызов конструктора базового класса FigureCanvas
        super(MPlCanvas, self).__init__(self.fig)

        self.ax2 = self.ax1.twinx()
        self.ax4 = self.ax1.twinx()
        self.init_canvas(facecolor, textcolor)  # Инициализация настроек canvas

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

        plt.subplots_adjust(left=0.04, bottom=0.03, right=1, top=1, hspace=0.12)

        # Перерисовываем график
        self.draw()

    def update_colors(self, facecolor, textcolor):
        """Метод для обновления цветов и перерисовки"""
        self.init_canvas(facecolor, textcolor)