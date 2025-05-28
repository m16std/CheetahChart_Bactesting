from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHeaderView, QHBoxLayout, QLabel, QFrame, QScrollArea, QWidget, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class StatisticsWindow(QDialog):
    def __init__(self, stats_data, theme="dark", parent=None, font_size=12):  # Добавлен параметр font_size
        super().__init__(parent)
        self.stats_data = stats_data  # Сохраняем данные
        self.current_theme = theme    # Сохраняем текущую тему
        self.font_size = str(font_size)
        self.title_size = str(int(font_size + 2))  
        self.setWindowTitle('Detailed Statistics')
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        
        # Create scroll area for stats
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 9, 0)
        scroll_layout.setSpacing(2)

        performance_stats = {
            "Performance": {
                "Total Return": f"{stats_data.get('total_return', 0)}%",
                "Profit Factor": str(stats_data.get('profit_factor', 0)),
                "Win Rate": f"{stats_data.get('win_rate', 0)}%",
                "Max Drawdown": f"{stats_data.get('max_drawdown', 0)}%",
                "Sharpe Ratio": str(stats_data.get('sharpe_ratio', 0)),
                "Trades per Day": str(stats_data.get('trades_per_day', 0)),
                "Daily PnL": f"{stats_data.get('daily_pnl', 0)} USDT"
            },
            "Trade Statistics": {
                "Total Trades": str(stats_data.get('total_trades', 0)),
                "Winning Trades": str(stats_data.get('winning_trades', 0)),
                "Losing Trades": str(stats_data.get('losing_trades', 0)),
                "Average Win": f"{stats_data.get('avg_win', 0)} USDT",
                "Average Loss": f"{stats_data.get('avg_loss', 0)} USDT",
                "Largest Win": f"{stats_data.get('largest_win', 0)} USDT",
                "Largest Loss": f"{stats_data.get('largest_loss', 0)} USDT"
            },
            "Time Analysis": {
                "Start Date": str(stats_data.get('start_date', '')),
                "End Date": str(stats_data.get('end_date', '')),
                "Total Days": str(stats_data.get('total_days', 0)),
                "Avg Holding Time": str(stats_data.get('avg_holding_time', '0h'))
            },
            "Strategy Settings": {
                "Strategy Name": stats_data.get('strategy_name', 'N/A'),
                "Symbol": stats_data.get('symbol', 'N/A'),
                "Interval": stats_data.get('interval', 'N/A'),
                "Commission": f"{stats_data.get('commission', 0) * 100}%",
                "Initial Balance": f"{stats_data.get('initial_balance', 0)} USDT",
                "Leverage": f"{stats_data.get('leverage', 1)}x",
                "Position Type": str(stats_data.get('position_type', 'N/A')),
                "Position Size": str(stats_data.get('position_size', 0))
            }
        }

        # Add stats groups
        for group_name, stats in performance_stats.items():
            group_frame = QFrame()
            group_frame.setFrameShape(QFrame.StyledPanel)

            if theme == "dark":
                group_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    padding: 3px;
                }
            """)
            else:
                group_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 0, 0, 0.00);
                    border-radius: 8px;
                    padding: 3px;
                }
            """)
            
            group_layout = QVBoxLayout(group_frame)
            group_layout.setContentsMargins(0, 0, 0, 0) 
            group_layout.setSpacing(2)
            
            # Group title
            title = QLabel(group_name)
            title.setStyleSheet(f"font-size: {self.title_size}px; font-weight: bold; color: #669FD3; padding: 3px;")
            group_layout.addWidget(title)
            
            # Stats grid
            for stat_name, value in stats.items():
                stat_layout = QHBoxLayout()
                stat_label = QLabel(stat_name)
                stat_value = QLabel(str(value))
                
                if theme == "dark":
                    stat_label.setStyleSheet(f"color: #ffffff; font-size: {self.font_size}px;")
                    stat_value.setStyleSheet(f"color: #669FD3; font-size: {self.font_size}px;")
                else:
                    stat_label.setStyleSheet(f"color: #000000; font-size: {self.font_size}px;background-color: rgba(0, 0, 0, 0.05);")
                    stat_value.setStyleSheet(f"color: #669FD3; font-size: {self.font_size}px;background-color: rgba(0, 0, 0, 0.05);")
                
                stat_layout.addWidget(stat_label)
                stat_layout.addStretch()
                stat_layout.addWidget(stat_value)
                stat_layout.setSpacing(2)
                group_layout.addLayout(stat_layout)
            
            scroll_layout.addWidget(group_frame)
        
        positions_frame = QFrame()
        if theme == "dark":
            positions_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    padding: 3px;
                }
            """)
        else:
            positions_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 0, 0, 0.00);
                    border-radius: 8px;
                    padding: 3px;
                }
            """)

        positions_layout = QVBoxLayout(positions_frame)
        positions_layout.setContentsMargins(0, 0, 0, 0)
        positions_layout.setSpacing(2)

        # Заголовок таблицы
        title = QLabel("Positions")
        title.setStyleSheet(f"font-size: {self.title_size}px; font-weight: bold; color: #669FD3; padding: 3px;")
        positions_layout.addWidget(title)

        # Таблица позиций
        positions_table = QTableWidget()
        positions_table.setColumnCount(4)
        positions_table.setHorizontalHeaderLabels(["Side", "Open", "Close", "PnL"])
        positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        positions_table.setMinimumHeight(300)
        #positions_table.setMaxVisibleRows(15) 
        
        # Настраиваем политику прокрутки
        positions_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Настройка стиля таблицы
        if self.current_theme == "dark":
            positions_table.setStyleSheet("""
                QTableWidget {
                    gridline-color: #2d2d2d;
                    background-color: transparent;
                    border: 1px solid #2d2d2d;
                }
                QTableWidget::item {
                    padding: 5px;
                    font-size: 12px;
                }
                QHeaderView::section {
                    background-color: #202020;
                    padding: 5px;
                    border: 1px solid #2d2d2d;
                }
            """)
        else:
            positions_table.setStyleSheet("""
                QTableWidget {
                    gridline-color: #d0d0d0;
                    background-color: transparent;
                    border: 1px solid #d0d0d0;
                }
                QTableWidget::item {
                    padding: 5px;
                    font-size: 12px;
                }
                QHeaderView::section {
                    background-color: #f0f0f0;
                    padding: 5px;
                    border: 1px solid #d0d0d0;
                }
            """)

        # Заполняем таблицу данными
        if 'positions_data' in stats_data:
            positions = stats_data.get('positions_data', [])
            positions_table.setRowCount(len(positions))
            for row, (close_time, pnl, is_profit) in enumerate(positions):             
                # Направление сделки (определяем по PnL)
                side_item = QTableWidgetItem("LONG" if pnl > 0 else "SHORT")
                side_item.setForeground(QColor('#089981') if pnl > 0 else QColor('#F23645'))
                positions_table.setItem(row, 0, side_item)
                
                # Время закрытия
                positions_table.setItem(row, 1, QTableWidgetItem(str(close_time)))
                positions_table.setItem(row, 2, QTableWidgetItem(str(close_time)))
                
                # PnL с цветом
                pnl_item = QTableWidgetItem(f"{pnl:.2f}")
                pnl_item.setForeground(QColor('#089981') if pnl > 0 else QColor('#F23645'))
                positions_table.setItem(row, 3, pnl_item)

        positions_layout.addWidget(positions_table)
        scroll_layout.addWidget(positions_frame)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

