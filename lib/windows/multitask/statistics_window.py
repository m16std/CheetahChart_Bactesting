from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QWidget
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np

class StatisticsWindow(QDialog):
    def __init__(self, stats_data, theme="dark", parent=None):
        super().__init__(parent)
        self.stats_data = stats_data  # Сохраняем данные
        self.current_theme = theme    # Сохраняем текущую тему
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

        # Always create Plot Frame regardless of data
        plot_frame = QFrame()
        plot_frame.setFrameShape(QFrame.StyledPanel)
        if theme == "dark":
            plot_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 2px;
                margin: 0px;
            }
        """)
        else:
            plot_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.0);
                border-radius: 8px;
                padding: 2px;
                margin: 0px;
            }
        """)
        plot_layout = QVBoxLayout(plot_frame)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(2)
        
        
        # Title for plot section
        plot_title = QLabel("PnL History")
        plot_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #669FD3; padding: 3px;background-color: rgba(0, 0, 0, 0.05);")
        plot_layout.addWidget(plot_title)
        
        # Create plot widget with fixed height
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground(None)
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.setMouseEnabled(x=True, y=True)
        plot_widget.setMenuEnabled(False)
        
        # Style axis
        styles = {'color': '#669FD3' if theme == "dark" else '#000000'}
        plot_widget.getAxis('left').setTextPen(styles['color'])
        plot_widget.getAxis('bottom').setTextPen(styles['color'])
        #plot_widget.setLabel('left', 'PnL', units='USDT', **styles)
        #plot_widget.setLabel('bottom', 'Trade #', **styles)
        
        # Only try to plot data if it exists
        if 'positions_data' in stats_data and stats_data['positions_data']:
            try:
                # Split data into profits and losses
                profits = [(i, pnl) for i, (_, pnl, is_profit) in enumerate(stats_data['positions_data']) if is_profit]
                losses = [(i, pnl) for i, (_, pnl, is_profit) in enumerate(stats_data['positions_data']) if not is_profit]
                
                # Plot profits
                if profits:
                    x_profit, y_profit = zip(*profits)
                    plot_widget.plot(x_profit, y_profit, 
                                   pen=None, symbol='o',
                                   symbolPen=None,
                                   symbolBrush=(70, 175, 80, 200),
                                   symbolSize=6)
                
                # Plot losses
                if losses:
                    x_loss, y_loss = zip(*losses)
                    plot_widget.plot(x_loss, y_loss,
                                   pen=None, symbol='o',
                                   symbolPen=None,
                                   symbolBrush=(242, 54, 69, 200),
                                   symbolSize=6)
                    
                # Set Y axis range with some padding
                all_pnls = [pnl for _, pnl, _ in stats_data['positions_data']]
                if all_pnls:
                    y_min, y_max = min(all_pnls), max(all_pnls)
                    padding = (y_max - y_min) * 0.1
                    plot_widget.setYRange(y_min - padding, y_max + padding)
                    
            except Exception as e:
                print(f"Error plotting data: {e}")
        else:
            # Set default empty plot range
            plot_widget.setYRange(-1, 1)
            plot_widget.setXRange(0, 10)
        
        plot_widget.setFixedHeight(150)
        plot_layout.addWidget(plot_widget)
        scroll_layout.addWidget(plot_frame)

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
            title.setStyleSheet("font-size: 14px; font-weight: bold; color: #669FD3; padding: 3px;")
            group_layout.addWidget(title)
            
            # Stats grid
            for stat_name, value in stats.items():
                stat_layout = QHBoxLayout()
                stat_label = QLabel(stat_name)
                stat_value = QLabel(str(value))
                
                if theme == "dark":
                    stat_label.setStyleSheet("color: #ffffff; font-size: 12px;")
                    stat_value.setStyleSheet("color: #669FD3; font-size: 12px;")
                else:
                    stat_label.setStyleSheet("color: #000000; font-size: 12px;background-color: rgba(0, 0, 0, 0.05);")
                    stat_value.setStyleSheet("color: #669FD3; font-size: 12px;background-color: rgba(0, 0, 0, 0.05);")
                
                stat_layout.addWidget(stat_label)
                stat_layout.addStretch()
                stat_layout.addWidget(stat_value)
                stat_layout.setSpacing(2)
                group_layout.addLayout(stat_layout)
            
            scroll_layout.addWidget(group_frame)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
