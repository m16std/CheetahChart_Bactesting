from PyQt5.QtWidgets import QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QDialog
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import qdarktheme

class PositionsTable(QDialog):
    def __init__(self, positions, current_theme, show_synced_column=False):
        super().__init__()
        self.setWindowTitle('Positions')
        self.setGeometry(100, 100, 1200, 800)
        # Создаём таблицу
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(len(positions))
        self.table_widget.viewport().setAutoFillBackground(False)

        if current_theme == "dark":
            qdarktheme.setup_theme(
                custom_colors={
                    "[dark]": {
                        "background": "#151924",
                        "primary": "#ffffff",
                        "primary>button.hoverBackground": "#669ff55c",
                        "primary>progressBar.background": "#669ff5",
                    }
                }
            )
            self.table_widget.setStyleSheet(f"background-color: #151924;")
        else:
            qdarktheme.setup_theme(current_theme)
            self.table_widget.setStyleSheet(f"background-color: #ffffff;")
        
        if not show_synced_column:
            ColumnCount = 14
        else:
            ColumnCount = 15
        self.table_widget.setColumnCount(ColumnCount) 
        max_pnl = 0 
        if len(positions) > 0:
            max_pnl = max(abs(position['pnl']) for position in positions)

        # Устанавливаем заголовки столбцов
        self.table_widget.setHorizontalHeaderLabels([
            'ID', 'Side', 'Order Type', 'Status', 'Quantity', 'Leverage', 'TP Trigger', 'SL Trigger', 'Open Price', 
             'Close Price', 'Open Time', 'Close Time', 'PnL', 'Commission', 'Synced'
        ])

        # Заполняем таблицу данными о позициях
        for row, position in enumerate(positions):
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(position['posId'])))
            self.table_widget.setItem(row, 1, QTableWidgetItem(position['posSide']))
            self.table_widget.setItem(row, 2, QTableWidgetItem(position['ordType']))
            self.table_widget.setItem(row, 3, QTableWidgetItem(position['status']))
            self.table_widget.setItem(row, 4, QTableWidgetItem(str(round(position['qty'], 1))))
            self.table_widget.setItem(row, 5, QTableWidgetItem(str(position['leverage'])))
            self.table_widget.setItem(row, 6, QTableWidgetItem(str(round(position['tpTriggerPx'], 1))))
            self.table_widget.setItem(row, 7, QTableWidgetItem(str(round(position['slTriggerPx'], 1))))
            formatted_price = self.format_price(position['openPrice'])
            self.table_widget.setItem(row, 8, QTableWidgetItem(formatted_price))
            formatted_price = self.format_price(position['closePrice'])
            self.table_widget.setItem(row, 9, QTableWidgetItem(formatted_price))
            self.table_widget.setItem(row, 10, QTableWidgetItem(str(position['openTimestamp'])))
            self.table_widget.setItem(row, 11, QTableWidgetItem(str(position['closeTimestamp'])))
            self.table_widget.setItem(row, 12, QTableWidgetItem(str(round(position['pnl'], 3))))
            self.table_widget.setItem(row, 13, QTableWidgetItem(str(round(position['commission'], 5))))
            if show_synced_column:
                self.table_widget.setItem(row, 14, QTableWidgetItem(str(position['syncStatus'])))
            
            
            # Заполнение столбца с PnL и настройка цвета фона
            pnl_item = QTableWidgetItem(str(round(position['pnl'], 3)))
            pnl_value = position['pnl']

            # Расчет прозрачности в зависимости от отношения pnl/max_pnl
            if max_pnl != 0:
                transparency_factor = abs(pnl_value) / max_pnl
            else:
                transparency_factor = 1

            # Окрашиваем фон в зависимости от положительного или отрицательного PnL
            if pnl_value > 0:
                color = QColor(8, 153, 89)  # Зеленый
            elif pnl_value < 0:
                color = QColor(242, 54, 69)  # Красный
            else:
                color = QColor(0, 0, 0, 0)  # Нейтральный цвет для нуля

            # Устанавливаем прозрачность цвета
            color.setAlphaF(transparency_factor) 
            pnl_item.setBackground(color)
            self.table_widget.setItem(row, 12, pnl_item)


        # Настройка поведения таблицы
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Layout для окна
        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

    def format_price(self, price):
        if price >= 100000:
            return f"{int(price)}"
        elif 10000 <= price < 100000:
            return f"{price:.1f}"
        elif 1000 <= price < 10000:
            return f"{price:.2f}"
        elif price >= 1:
            return f"{price:.5g}"
        else:
            # Цена меньше 0.01
            num_str = f"{price:.10f}".rstrip('0')
        return num_str

    def format_subscript_price(self, price):
        """Форматирование цены с нижним индексом для нулей."""
        price_str = f"{price:.10f}".rstrip('0')  # Убираем лишние нули в конце
        integer_part, decimal_part = price_str.split('.')
        
        # Найдем количество нулей между точкой и первым числом
        leading_zeros = len(decimal_part) - len(decimal_part.lstrip('0'))
        significant_part = decimal_part.lstrip('0')

        # Форматируем нули как нижний индекс
        if leading_zeros > 0:
            subscript_zeros = f"<sub>{'0' * leading_zeros}</sub>"
            formatted_price = f"{integer_part}.{subscript_zeros}{significant_part}"
        else:
            formatted_price = price_str

        return formatted_price

    def set_price_in_table(self, table_widget, row, column, price):
        # Форматируем цену
        formatted_price = self.format_price(price)

        # Создаем ячейку таблицы
        item = QTableWidgetItem(formatted_price)
        item.setTextAlignment(Qt.AlignCenter)
        
        # Устанавливаем ячейку в таблицу
        table_widget.setItem(row, column, item)