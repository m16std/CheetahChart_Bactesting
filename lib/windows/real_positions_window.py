from PyQt5.QtWidgets import QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QCheckBox, QMessageBox
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import qdarktheme

class RealPositionsWindow(QDialog):
    def __init__(self, api, current_theme):
        super().__init__()
        self.setWindowTitle('Real Positions')
        self.setGeometry(100, 100, 1200, 800)
        self.api = api
        self.current_theme = current_theme

        # Create layout
        self.layout = QVBoxLayout(self)

        # Add checkbox to toggle between open positions and all positions
        self.toggle_checkbox = QCheckBox("Show only open positions")
        self.toggle_checkbox.setChecked(True)
        self.toggle_checkbox.stateChanged.connect(self.load_positions)
        self.layout.addWidget(self.toggle_checkbox)

        # Create table
        self.table_widget = QTableWidget()
        self.layout.addWidget(self.table_widget)

        # Load initial positions
        self.load_positions()

    def load_positions(self):
        """Load positions based on the toggle state and update the table."""
        show_only_open = self.toggle_checkbox.isChecked()
        try:
            if show_only_open:
                positions = self.api.get_open_positions()
            else:
                positions = self.api.get_position_history()  # Fetch all historical positions
            if positions is None or 'data' not in positions:
                raise ValueError("Failed to fetch positions from the API.")
            positions_data = positions['data']
            # Ensure numeric conversion for relevant fields
            for position in positions_data:
                position['upl'] = float(position.get('upl', 0))  # Unrealized PnL
                position['lever'] = float(position.get('lever', 0))  # Leverage
                position['pos'] = float(position.get('pos', 0))  # Position size
                position['avgPx'] = float(position.get('avgPx', 0))  # Entry Price
                position['markPx'] = float(position.get('markPx', 0))  # Mark Price
            self.update_table(positions_data)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить позиции. Ошибка: {str(e)}")
            self.update_table([])

    def update_table(self, positions):
        """Update the table with the given positions."""
        self.table_widget.setRowCount(len(positions))
        self.table_widget.setColumnCount(7)  # Adjusted for available fields
        self.table_widget.setHorizontalHeaderLabels([
            'Instrument ID', 'Position Side', 'Position Size', 'Leverage', 'Entry Price', 'Mark Price', 'Unrealized PnL'
        ])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        max_upl = max(abs(pos['upl']) for pos in positions) if positions else 0

        for row, position in enumerate(positions):
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(position.get('instId', 'N/A'))))
            self.table_widget.setItem(row, 1, QTableWidgetItem(str(position.get('posSide', 'N/A'))))
            self.table_widget.setItem(row, 2, QTableWidgetItem(str(round(float(position.get('pos', 0)), 2))))
            self.table_widget.setItem(row, 3, QTableWidgetItem(str(round(float(position.get('lever', 0)), 2))))
            self.table_widget.setItem(row, 4, QTableWidgetItem(str(round(float(position.get('avgPx', 0)), 2))))
            self.table_widget.setItem(row, 5, QTableWidgetItem(str(round(float(position.get('markPx', 0)), 2))))

            # Unrealized PnL cell with color gradient
            upl_item = QTableWidgetItem(str(round(float(position['upl']), 2)))
            upl_value = position['upl']
            transparency_factor = abs(upl_value) / max_upl if max_upl != 0 else 1
            color = QColor(8, 153, 89) if upl_value > 0 else QColor(242, 54, 69)
            color.setAlphaF(transparency_factor)
            upl_item.setBackground(color)
            self.table_widget.setItem(row, 6, upl_item)

        # Apply theme
        if self.current_theme == "dark":
            qdarktheme.setup_theme(custom_colors={"[dark]": {"background": "#151924", "primary": "#ffffff"}})
            self.table_widget.setStyleSheet("background-color: #151924;")
        else:
            qdarktheme.setup_theme(self.current_theme)
            self.table_widget.setStyleSheet("background-color: #ffffff;")
