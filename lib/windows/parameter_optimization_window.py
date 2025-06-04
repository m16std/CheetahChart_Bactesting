from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
                           QTableWidget, QTableWidgetItem, QProgressBar,
                           QCheckBox, QGridLayout, QGroupBox, QScrollArea,
                           QTabWidget, QTextEdit, QStackedWidget)  # Add QTabWidget, QTextEdit, and QStackedWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import logging

import itertools
from lib.threads.optimization_thread import OptimizationThread
from lib.threads.fast_optimization_thread import FastOptimizationThread
from scipy.optimize import differential_evolution, dual_annealing, minimize

class ParameterOptimizationWindow(QWidget): 
    def __init__(self, strategy_manager, parent=None, theme="dark"):
        super().__init__(parent)
        self.strategy_manager = strategy_manager
        self.parent = parent
        self.setWindowTitle("Оптимизация параметров")
        self.setMinimumWidth(600)
        self.df = None
        self.data_ready = False
        self.param_inputs = {} 
        self.param_checkboxes = {} 
        self.current_theme = theme

        # Initialize current strategy before UI creation
        self.current_strategy = None
        if self.strategy_manager and self.strategy_manager.strategy_dict:
            first_strategy_name = next(iter(self.strategy_manager.strategy_dict))
            self.current_strategy = self.strategy_manager.strategy_dict[first_strategy_name]

        # Initialize optimization methods before init_ui
        self.optimization_methods = {
            'Дифференциальная эволюция': differential_evolution,
            'Имитация отжига': dual_annealing,
            'Метод Нелдера-Мида': lambda func, x0, bounds: minimize(func, x0, method='Nelder-Mead', bounds=bounds)
        }

        # Add method settings
        self.method_settings = {
            'Дифференциальная эволюция': {
                'max_iterations': ('Максимум итераций', 100, int, 10, 1000),
                'popsize': ('Размер популяции', 15, int, 5, 100),
                'mutation': ('Коэффициент мутации', 0.5, float, 0.1, 1.0),
                'recombination': ('Вероятность рекомбинации', 0.7, float, 0.1, 1.0)
            },
            'Имитация отжига': {
                'max_iterations': ('Максимум итераций', 100, int, 10, 1000),
                'initial_temp': ('Начальная температура', 5.0, float, 0.1, 10.0),
                'visit': ('Коэффициент посещения', 2.0, float, 0.1, 5.0),
                'accept': ('Коэффициент принятия', -5.0, float, -10.0, -0.1)
            },
            'Метод Нелдера-Мида': {
                'max_iterations': ('Максимум итераций', 100, int, 10, 1000),
                'xatol': ('Допуск по x', 0.0001, float, 0.00001, 0.1),
                'fatol': ('Допуск по функции', 0.0001, float, 0.00001, 0.1) 
            }
        }

        self.init_ui()
        if hasattr(parent, 'theme_changed_signal'):
            parent.theme_changed_signal.connect(self.apply_theme)
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) 
        layout.setSpacing(0) 

        # Left panel for controls
        left_panel = QWidget()
        left_panel.setFixedWidth(500) 
        inputs_layout = QVBoxLayout(left_panel)
        inputs_layout.setAlignment(Qt.AlignTop)

        # Add data and strategy controls
        self.add_data_controls(inputs_layout)
        self.add_strategy_controls(inputs_layout)

        # Create tab widget
        tab_widget = QTabWidget()
        direct_tab = self.create_direct_optimization_tab()
        fast_tab = self.create_fast_optimization_tab()
        
        tab_widget.addTab(direct_tab, "Прямая оптимизация")
        tab_widget.addTab(fast_tab, "Быстрая оптимизация")

        tab_widget.currentChanged.connect(self.on_tab_changed)  
        
        inputs_layout.addWidget(tab_widget)

        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        inputs_layout.addWidget(self.progress_bar)

        layout.addWidget(left_panel)

        # Right panel (stacked widget)
        self.right_stack = QStackedWidget()
        
        # Add chart panel
        chart_panel = QWidget()
        chart_layout = QVBoxLayout(chart_panel)
        self.init_matplotlib_canvas()
        chart_layout.addWidget(self.canvas)
        self.right_stack.addWidget(chart_panel)

        # Add results panel
        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        
        self.results_label = QLabel("Результаты оптимизации")
        self.results_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #669FD3;")
        results_layout.addWidget(self.results_label)

        self.iteration_text = QTextEdit()
        self.iteration_text.setReadOnly(True)
        self.iteration_text.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 5px;
                font-family: monospace;
            }
        """)
        results_layout.addWidget(self.iteration_text)

        self.results_text = QLabel()
        self.results_text.setWordWrap(True)
        self.results_text.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 5px;
                margin-top: 10px;
            }
        """)
        results_layout.addWidget(self.results_text)
        
        self.right_stack.addWidget(results_panel)
        layout.addWidget(self.right_stack)

    def on_tab_changed(self, index):
        if hasattr(self, 'right_stack'): 
            self.right_stack.setCurrentIndex(index)
        else:
            raise AttributeError("The 'right_stack' attribute is not initialized.")

    def create_direct_optimization_tab(self):
        """Create tab for direct optimization method"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0) 
        
        # Add parameters table
        self.direct_params_table = QTableWidget()
        self.direct_params_table.setColumnCount(6) 
        self.direct_params_table.setHorizontalHeaderLabels([
            "", "Параметр", "Значение", "Мин", "Макс", "Точки"
        ])
        self.direct_params_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.direct_params_table)
        
        # Update table with current strategy parameters
        self.update_direct_params_table()
        
        # Add optimize button and progress bar
        self.add_control_widgets(layout, "direct")
        
        return tab

    def update_direct_params_table(self):
        """Update parameters table for direct optimization"""
        if not hasattr(self, 'direct_params_table') or not hasattr(self, 'current_strategy'):
            return
            
        self.direct_params_table.setRowCount(0)
        # Очищаем словарь чекбоксов перед обновлением таблицы
        self.param_checkboxes.clear()
        
        if not self.current_strategy:
            return
            
        for name, param in self.current_strategy.parameters.items():
            row = self.direct_params_table.rowCount()
            self.direct_params_table.insertRow(row)
            
            # Add checkbox for optimization
            checkbox = QCheckBox()
            self.param_checkboxes[name] = checkbox
            self.direct_params_table.setCellWidget(row, 0, checkbox)
            
            # Add parameter name
            name_item = QTableWidgetItem(param.description)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.direct_params_table.setItem(row, 1, name_item)
            
            # Add value spinbox
            value_input = QDoubleSpinBox() if param.type == float else QSpinBox()
            value_input.setValue(param.value)
            if param.min_value is not None:
                value_input.setMinimum(param.min_value)
            if param.max_value is not None:
                value_input.setMaximum(param.max_value)
            self.direct_params_table.setCellWidget(row, 2, value_input)
            
            # Add min value spinbox
            min_input = QDoubleSpinBox() if param.type == float else QSpinBox()
            min_input.setValue(param.min_value if param.min_value is not None else 0)
            min_input.setEnabled(False)
            self.direct_params_table.setCellWidget(row, 3, min_input)
            
            # Add max value spinbox
            max_input = QDoubleSpinBox() if param.type == float else QSpinBox()
            max_input.setValue(param.max_value if param.max_value is not None else 100)
            max_input.setEnabled(False)
            self.direct_params_table.setCellWidget(row, 4, max_input)
            
            # Add points spinbox
            points_input = QSpinBox()
            points_input.setRange(2, 100)
            points_input.setValue(10)
            points_input.setEnabled(False)
            self.direct_params_table.setCellWidget(row, 5, points_input)
            
            # Store inputs for later access
            self.param_inputs[name] = {
                'value': value_input,
                'min': min_input,
                'max': max_input,
                'points': points_input  # Add points input to dictionary
            }
            
            # Connect checkbox state change
            checkbox.stateChanged.connect(lambda state, n=name: self.on_checkbox_changed(n, state))

        # Resize columns to fit content
        self.direct_params_table.resizeColumnsToContents()
        self.direct_params_table.resizeRowsToContents()

    def create_fast_optimization_tab(self):
        """Create tab for fast optimization method"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0) 
        
        # Add optimization method selection
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Метод оптимизации:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(self.optimization_methods.keys())
        self.method_combo.currentTextChanged.connect(self.on_method_changed)
        method_layout.addWidget(self.method_combo)
        layout.addLayout(method_layout)
        
        # Add parameters table
        self.fast_params_table = QTableWidget()
        self.fast_params_table.setColumnCount(4)
        self.fast_params_table.setHorizontalHeaderLabels(["Параметр", "Начальное значение", "Мин", "Макс"])
        self.fast_params_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.fast_params_table)
        
        # Update table with current strategy parameters
        self.update_fast_params_table()
        
        self.method_settings_group = QGroupBox("Настройки метода")
        self.method_settings_layout = QVBoxLayout()
        self.method_settings_group.setLayout(self.method_settings_layout)
        layout.addWidget(self.method_settings_group)
        
        # Add optimize button and progress bar
        self.add_control_widgets(layout, "fast")
        
        # Initialize method settings
        self.update_method_settings()
        
        # Add results text area
        self.results_label = QLabel("Результаты оптимизации:")
        self.results_label.hide()  # Initially hidden
        layout.addWidget(self.results_label)
        
        self.results_text = QLabel()
        self.results_text.setWordWrap(True)
        self.results_text.setStyleSheet("padding: 10px; background-color: rgba(255, 255, 255, 0.05); border-radius: 5px;")
        self.results_text.hide()  # Initially hidden
        layout.addWidget(self.results_text)

        return tab

    def update_method_settings(self):
        """Update settings widgets based on selected optimization method"""
        for i in reversed(range(self.method_settings_layout.count())):
            item = self.method_settings_layout.itemAt(i)
            if item and item.widget():  # Ensure item and widget exist
                item.widget().setParent(None)

        method = self.method_combo.currentText()
        if method == "Дифференциальная эволюция":
            self.add_differential_evolution_settings()
        elif method == "Имитация отжига":
            self.add_annealing_settings()
        elif method == "Метод Нелдера-Мида":
            self.add_nelder_mead_settings()

    def update_fast_params_table(self):
        """Update parameters table for fast optimization"""
        if not hasattr(self, 'fast_params_table') or not hasattr(self, 'current_strategy'):
            return
            
        self.fast_params_table.setRowCount(0)
        if not self.current_strategy:
            return
            
        for name, param in self.current_strategy.parameters.items():
            row = self.fast_params_table.rowCount()
            self.fast_params_table.insertRow(row)
            
            name_item = QTableWidgetItem(param.description)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.fast_params_table.setItem(row, 0, name_item)
            
            value_spinbox = QDoubleSpinBox() if param.type == float else QSpinBox()
            min_spinbox = QDoubleSpinBox() if param.type == float else QSpinBox()
            max_spinbox = QDoubleSpinBox() if param.type == float else QSpinBox()
            
            if param.min_value is not None:
                value_spinbox.setMinimum(param.min_value)
                min_spinbox.setMinimum(param.min_value)
                max_spinbox.setMinimum(param.min_value)
            if param.max_value is not None:
                value_spinbox.setMaximum(param.max_value)
                min_spinbox.setMaximum(param.max_value)
                max_spinbox.setMaximum(param.max_value)
                
            value_spinbox.setValue(param.value)
            min_spinbox.setValue(param.min_value if param.min_value is not None else 0)
            max_spinbox.setValue(param.max_value if param.max_value is not None else 100)
            
            self.fast_params_table.setCellWidget(row, 1, value_spinbox)
            self.fast_params_table.setCellWidget(row, 2, min_spinbox)
            self.fast_params_table.setCellWidget(row, 3, max_spinbox)

        self.fast_params_table.resizeColumnsToContents()
        self.fast_params_table.resizeRowsToContents()

    def start_fast_optimization(self):
        """Start optimization using selected numerical method"""
        if not self.data_ready:
            self.parent.show_toast("error", "Ошибка", "Сначала загрузите исторические данные")
            return
            
        method = self.method_combo.currentText()
        optimizer = self.optimization_methods[method]
        
        # Get parameters and bounds using parameter keys
        params = []
        bounds = []
        
        for row in range(self.fast_params_table.rowCount()):
            param_desc = self.fast_params_table.item(row, 0).text()
            
            # Find parameter key by description
            param_key = next(
                (key for key, param in self.current_strategy.parameters.items() if param.description == param_desc),
                None
            )
            if not param_key:
                self.parent.show_toast("error", "Ошибка", f"Не найден параметр: {param_desc}")
                return

            min_widget = self.fast_params_table.cellWidget(row, 2)
            max_widget = self.fast_params_table.cellWidget(row, 3)
            
            if not min_widget or not max_widget:
                self.parent.show_toast("error", "Ошибка", "Некорректные значения в таблице")
                return
                
            min_val = min_widget.value()
            max_val = max_widget.value()
            
            params.append(param_key)  # Store parameter key instead of description
            bounds.append((float(min_val), float(max_val)))  # Ensure float bounds

        # Get max_iterations from settings
        method = self.method_combo.currentText()
        max_iterations = None
        for i in range(self.method_settings_layout.count()):
            item = self.method_settings_layout.itemAt(i)
            if item and item.layout():
                label = item.layout().itemAt(0).widget()
                widget = item.layout().itemAt(1).widget()
                if label.text() == "Максимум итераций":
                    max_iterations = widget.value()
                    break

        self.params = params  

        # Create optimization thread
        self.optimize_thread = FastOptimizationThread(
            self.current_strategy,
            params,
            bounds,
            optimizer,
            self.get_settings()
        )
        if max_iterations:
            self.optimize_thread.max_iterations = max_iterations
        
        self.optimize_thread.progress_changed.connect(self.progress_bar.setValue)
        self.optimize_thread.optimization_complete.connect(self.on_optimization_complete)
        self.optimize_thread.iteration_update.connect(self.update_iteration_result)  # Connect iteration updates
        self.optimize_btn.setEnabled(False)
        self.iteration_text.clear()  # Clear previous results
        self.optimize_thread.start()

    def add_data_controls(self, layout):
        data_group = QHBoxLayout()
        data_group.setContentsMargins(0, 0, 0, 0) 
        data_group.setSpacing(5) 
        open_btn = QPushButton("Открыть данные")
        open_btn.clicked.connect(self.open_data)
        download_btn = QPushButton("Загрузить данные")
        download_btn.clicked.connect(self.download_data)
        
        self.data_status = QLabel("Данные не загружены")
        self.data_status.setStyleSheet("color: red;")
        
        data_group.addWidget(open_btn)
        data_group.addWidget(download_btn)
        data_group.addWidget(self.data_status)
        
        layout.addLayout(data_group)
        layout.addWidget(QLabel(""))

    def add_strategy_controls(self, layout):
        strategy_group = QHBoxLayout()
        strategy_group.setContentsMargins(0, 0, 0, 0) 
        strategy_group.setSpacing(0) 
        strategy_group.addWidget(QLabel("Стратегия:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(self.strategy_manager.strategy_dict.keys())
        self.strategy_combo.currentTextChanged.connect(self.on_strategy_changed)
        strategy_group.addWidget(self.strategy_combo)
        layout.addLayout(strategy_group)

    def add_control_widgets(self, layout, optimization_type):
        """Add control widgets with separate optimize buttons for each tab"""
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0) 
        bottom_layout.setAlignment(Qt.AlignBottom)

        # Create separate optimize buttons for each tab
        if optimization_type == "direct":
            self.direct_optimize_btn = QPushButton("Оптимизировать")
            self.direct_optimize_btn.clicked.connect(self.start_optimization)
            self.direct_optimize_btn.setEnabled(False)
            self.optimize_btn = self.direct_optimize_btn  # Store reference
        else:
            self.fast_optimize_btn = QPushButton("Оптимизировать")
            self.fast_optimize_btn.clicked.connect(self.start_fast_optimization)
            self.fast_optimize_btn.setEnabled(False)
            self.optimize_btn = self.fast_optimize_btn  # Store reference

        bottom_layout.addWidget(self.optimize_btn)
        layout.addWidget(bottom_container)

    def init_matplotlib_canvas(self):
        self.figure = plt.figure(figsize=(6, 4))
        self.figure.patch.set_facecolor('#151924' if self.current_theme == "dark" else '#fafafa')
        self.canvas = FigureCanvasQTAgg(self.figure)

    def update_parameters_ui(self):
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.params_layout.addWidget(QLabel(""), 0, 0)
        self.params_layout.addWidget(QLabel("Параметр"), 0, 1)
        self.params_layout.addWidget(QLabel("Значение"), 0, 2)
        self.params_layout.addWidget(QLabel("Мин"), 0, 3)
        self.params_layout.addWidget(QLabel("Макс"), 0, 4)
        self.params_layout.addWidget(QLabel("Точки"), 0, 5)

        self.param_inputs = {}
        self.param_checkboxes = {}
        
        for row, (name, param) in enumerate(self.current_strategy.parameters.items(), start=1):
            checkbox = QCheckBox()
            self.param_checkboxes[name] = checkbox
            self.params_layout.addWidget(checkbox, row, 0)
            
            self.params_layout.addWidget(QLabel(param.description), row, 1)
            
            value_input = QDoubleSpinBox() if param.type == float else QSpinBox()
            value_input.setValue(param.value)
            if param.min_value is not None:
                value_input.setMinimum(param.min_value)
            if param.max_value is not None:
                value_input.setMaximum(param.max_value)
            self.params_layout.addWidget(value_input, row, 2)
            
            min_input = QDoubleSpinBox() if param.type == float else QSpinBox()
            min_input.setValue(param.min_value if param.min_value is not None else 0)
            min_input.setEnabled(False)
            
            max_input = QDoubleSpinBox() if param.type == float else QSpinBox()
            max_input.setValue(param.max_value if param.max_value is not None else 100)
            max_input.setEnabled(False)
            
            points_input = QSpinBox()
            points_input.setRange(2, 100)
            points_input.setValue(10)
            points_input.setEnabled(False)
            
            self.params_layout.addWidget(min_input, row, 3)
            self.params_layout.addWidget(max_input, row, 4)
            self.params_layout.addWidget(points_input, row, 5)
            
            self.param_inputs[name] = {
                'value': value_input,
                'min': min_input,
                'max': max_input,
                'points': points_input
            }
            
            checkbox.stateChanged.connect(
                lambda state, n=name: self.on_checkbox_changed(n, state)
            )

    def on_checkbox_changed(self, param_name, state):
        inputs = self.param_inputs[param_name]
        inputs['min'].setEnabled(state)
        inputs['max'].setEnabled(state)
        inputs['points'].setEnabled(state)  # Enable/disable points input
        inputs['value'].setEnabled(not state)

    def on_strategy_changed(self, strategy_name):
        self.current_strategy = self.strategy_manager.strategy_dict[strategy_name]
        # Update both tables
        self.update_direct_params_table()
        self.update_fast_params_table()

    def get_optimization_params(self):
        params = []
        for name, checkbox in self.param_checkboxes.items():
            if checkbox.isChecked():
                inputs = self.param_inputs[name]
                params.append((
                    name,
                    inputs['min'].value(),
                    inputs['max'].value(),
                    inputs['points'].value()
                ))
            else:
                self.current_strategy.set_parameter(name, self.param_inputs[name]['value'].value())
        return params

    def start_optimization(self):
        if not self.data_ready:
            self.parent.show_toast("error", "Ошибка", "Сначала загрузите исторические данные")
            return

        params = self.get_optimization_params()
        if not params:
            return

        self.optimize_thread = OptimizationThread(self.current_strategy, params, self.get_settings())
        self.optimize_thread.progress_changed.connect(self.progress_bar.setValue)
        self.optimize_thread.optimization_complete.connect(self.on_optimization_complete)
        self.optimize_btn.setEnabled(False)
        self.optimize_thread.start()

    def on_optimization_complete(self, results):
        self.optimize_thread.progress_changed.disconnect(self.progress_bar.setValue)
        self.optimize_thread.optimization_complete.disconnect(self.on_optimization_complete)
        self.optimize_btn.setEnabled(True)
        # Обработка результатов оптимизации
        self.show_optimization_results(results)
        
        # Update results display with parameter descriptions
        best_result = max(results, key=lambda x: x[1])
        results_text = "Результаты оптимизации:\n\n"
        
        if isinstance(best_result[0], (int, float)):
            param_key = self.params[0]  # Get parameter key
            param = self.current_strategy.parameters[param_key]
            results_text += f"Лучшее значение {param.description}: {best_result[0]:.6f}\n"
        else:
            for param_key, value in zip(self.params, best_result[0]):
                param = self.current_strategy.parameters[param_key]
                results_text += f"Лучшее значение {param.description}: {value:.6f}\n"
                
        results_text += f"\nМаксимальный PnL: {best_result[1]:.2f}"
        
        self.results_label.show()
        self.results_text.setText(results_text)
        self.results_text.show()
        
        # Clear iteration text area for next run
        self.iteration_text.clear()

    def optimize_one_param(self, param):
        name, min_val, max_val, points = param
        values = np.linspace(min_val, max_val, points)
        results = []
        
        for val in values:
            self.current_strategy.set_parameter(name, val)
            pnl = self.run_backtest()
            results.append(pnl)
            
        self.plot_one_param_results(values, results, name)

    def optimize_two_params(self, param1, param2):
        """Оптимизация двух параметров"""
        name1, min1, max1, points1 = param1
        name2, min2, max2, points2 = param2

        # Приводим points к int
        points1 = int(points1)
        points2 = int(points2)
        
        values1 = np.linspace(min1, max1, points1)
        values2 = np.linspace(min2, max2, points2)
        results = np.zeros((points1, points2))
        
        total_iterations = points1 * points2
        current_iteration = 0
        
        for i, v1 in enumerate(values1):
            for j, v2 in enumerate(values2):
                v1_converted = int(v1) if self.current_strategy.parameters[name1].type == int else v1
                v2_converted = int(v2) if self.current_strategy.parameters[name2].type == int else v2
                
                self.current_strategy.set_parameter(name1, v1_converted)
                self.current_strategy.set_parameter(name2, v2_converted)
                results[i,j] = self.run_backtest()
                
                current_iteration += 1
                progress = int((current_iteration / total_iterations) * 100)
                self.progress_bar.setValue(progress)
                
        self.plot_two_param_results(values1, values2, results, name1, name2)

    def optimize_multiple_params(self, params):
        param_ranges = []
        param_names = []
        for name, min_val, max_val, points in params:
            param_names.append(name)
            # Приводим points к int
            points = int(points)
            param_ranges.append(np.linspace(min_val, max_val, points))

        combinations = list(itertools.product(*param_ranges))
        best_pnl = float('-inf')
        best_params = None
        results = []

        total = len(combinations)
        self.progress_bar.setMaximum(total)

        for i, values in enumerate(combinations):
            for name, value in zip(param_names, values):
                # Приводим значение к правильному типу перед установкой
                value_converted = int(value) if self.current_strategy.parameters[name].type == int else value
                self.current_strategy.set_parameter(name, value_converted)

            pnl = self.run_backtest()
            results.append((values, pnl))

            if pnl > best_pnl:
                best_pnl = pnl
                best_params = values

            self.progress_bar.setValue(i + 1)

        self.log_optimization_results(param_names, best_params, best_pnl)

        if len(params) == 2:
            grid_results = np.zeros((len(param_ranges[0]), len(param_ranges[1])))
            for i, v1 in enumerate(param_ranges[0]):
                for j, v2 in enumerate(param_ranges[1]):
                    for values, pnl in results:
                        if values[0] == v1 and values[1] == v2:
                            grid_results[i,j] = pnl
                            break
            self.plot_two_param_results(param_ranges[0], param_ranges[1], 
                                      grid_results, param_names[0], param_names[1])

        for name, value in zip(param_names, best_params):
            self.current_strategy.set_parameter(name, value)

    def plot_one_param_results(self, values, results, param_name):
        self.figure.clear()
        bg_color = '#151924' if self.current_theme == "dark" else '#fafafa'
        text_color = 'white' if self.current_theme == "dark" else 'black'
        
        self.figure.patch.set_facecolor(bg_color)
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(bg_color)
        
        im = ax.imshow([results], aspect='auto', cmap='RdYlGn')
        
        # Добавляем значения с белым цветом
        for i, val in enumerate(results):
            ax.text(i, 0, f'{val:.2f}', ha='center', va='center', color=text_color)
            
        # Настройка осей и сетки
        ax.set_xticks(range(len(values)))
        ax.set_xticklabels([f'{v:.2f}' for v in values], color=text_color)
        ax.set_yticks([])
        ax.set_xlabel(param_name, color=text_color)
        ax.tick_params(colors=text_color)
        ax.grid(True, color='gray', alpha=0.2)
        
        # Добавляем аннотацию с лучшим результатом
        best_idx = np.argmax(results)
        best_val = values[best_idx]
        best_pnl = results[best_idx]
        ax.text(0.02, 0.98, 
                f'Best {param_name}: {best_val:.2f}\nPnL: {best_pnl:.2f}',
                transform=ax.transAxes, va='top', color=text_color)
                
        self.canvas.draw()

    def plot_two_param_results(self, values1, values2, results, name1, name2):
        self.figure.clear()
        bg_color = '#151924' if self.current_theme == "dark" else '#fafafa'
        text_color = 'white' if self.current_theme == "dark" else 'black'
        
        self.figure.patch.set_facecolor(bg_color)
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(bg_color)
        
        # Переворачиваем результаты для правильной ориентации
        results = results.T  # Транспонируем матрицу
        im = ax.imshow(results, cmap='RdYlGn', origin='lower', aspect='equal')
        
        # Добавляем значения поверх ячеек
        for i in range(len(values2)):
            for j in range(len(values1)):
                ax.text(j, i, f'{results[i,j]:.2f}', 
                       ha='center', va='center', color=text_color)
        
        # Настройка осей
        ax.set_xticks(range(len(values1)))
        ax.set_yticks(range(len(values2)))
        ax.set_xticklabels([f'{v:.2f}' for v in values1], color=text_color)
        ax.set_yticklabels([f'{v:.2f}' for v in values2], color=text_color)
        ax.set_xlabel(name1, color=text_color)
        ax.set_ylabel(name2, color=text_color)
        ax.tick_params(colors=text_color)
        ax.grid(True, color='gray', alpha=0.2)

        # Находим лучшие параметры
        best_idx = np.unravel_index(np.argmax(results), results.shape)
        best_val1 = values1[best_idx[1]]
        best_val2 = values2[best_idx[0]]
        best_pnl = results[best_idx]

        # Добавляем аннотацию над графиком
        ax.text(0.02, 1.05, 
                f'Best {name1}: {best_val1:.2f}\nBest {name2}: {best_val2:.2f}\nPnL: {best_pnl:.2f}',
                transform=ax.transAxes, va='bottom', color=text_color)

        self.canvas.draw()

    def run_backtest(self):
        df = self.df

        current_settings = {}
        if hasattr(self.parent, 'trading_status_window') and \
           hasattr(self.parent.trading_status_window.settings_content, 'get_settings'):
            current_settings = self.parent.trading_status_window.settings_content.get_settings()

        self.current_strategy.manager.df = df
        self.current_strategy.manager.leverage = current_settings.get('leverage', 1)
        self.current_strategy.manager.commission = current_settings.get('commission', 0.0008)

        settings = {
            'df': df,
            'initial_balance': current_settings.get('initial_balance', 1000),
            'position_size': current_settings.get('position_size', 100),
            'position_type': current_settings.get('position_type', 'percent'),
            'profit_factor': current_settings.get('profit_factor', 1.5)
        }

        # Приводим параметры к правильным типам перед установкой
        for name, inputs in self.param_inputs.items():
            if not self.param_checkboxes[name].isChecked():
                value = inputs['value'].value()
                # Если параметр целочисленный в стратегии, приводим его к int
                param_type = self.current_strategy.parameters[name].type
                if param_type == int:
                    value = int(value)
                self.current_strategy.set_parameter(name, value)
        
        self.current_strategy.run(**settings)
        
        total_pnl = sum(pos['pnl'] for pos in self.current_strategy.manager.positions)
        return total_pnl

    def log_optimization_results(self, param_names, best_params, best_pnl):
        msg = f"\nOptimization Results:\n"
        msg += "-" * 50 + "\n"
        for name, value in zip(param_names, best_params):
            msg += f"{name}: {value:.4f}\n"
        msg += f"Best PnL: {best_pnl:.4f}\n"
        msg += "-" * 50
        
        logging.info(msg)
        
        if hasattr(self.parent, 'log_window'):
            self.parent.log_window.add_log_entry(msg)

    def open_data(self):
        """Handle data loading and enable optimization buttons"""
        if self.parent.file_handler.load_candlesticks():
            self.df = self.parent.df
            self.data_ready = True
            self.data_status.setText("Данные загружены")
            self.data_status.setStyleSheet("color: green;")
            # Enable both optimization buttons
            if hasattr(self, 'direct_optimize_btn'):
                self.direct_optimize_btn.setEnabled(True)
            if hasattr(self, 'fast_optimize_btn'):
                self.fast_optimize_btn.setEnabled(True)

    def download_data(self):
        symbol = self.parent.symbol_input.currentText()
        interval = self.parent.interval_input.currentText()
        limit = self.parent.limit_input.value()

        self.data_status.setText("Загрузка данных...")
        self.data_status.setStyleSheet("color: orange;")

        from lib.api.okx_load_api import DataDownloadThread
        self.download_thread = DataDownloadThread(symbol, interval, limit)
        self.download_thread.data_downloaded.connect(self.on_data_downloaded)
        self.download_thread.show_toast.connect(self.parent.show_toast)
        self.download_thread.start()

    def on_data_downloaded(self, data):
        self.df = data
        self.data_ready = True
        self.data_status.setText("Данные загружены")
        self.data_status.setStyleSheet("color: green;")
        self.optimize_btn.setEnabled(True)

    def apply_theme(self, theme):
        self.current_theme = theme
        
        # Сохраняем текущие оси и их содержимое
        if len(self.figure.axes) > 0:
            current_ax = self.figure.axes[0]
            bg_color = '#151924' if theme == "dark" else '#fafafa'
            text_color = 'white' if theme == "dark" else 'black'
            
            # Обновляем цвета фона и текста
            self.figure.patch.set_facecolor(bg_color)
            current_ax.set_facecolor(bg_color)
            
            # Обновляем цвета всех текстовых элементов
            current_ax.tick_params(colors=text_color)
            
            # Обновляем цвета подписей осей
            if current_ax.get_xlabel():
                current_ax.set_xlabel(current_ax.get_xlabel(), color=text_color)
            if current_ax.get_ylabel():
                current_ax.set_ylabel(current_ax.get_ylabel(), color=text_color)
                
            # Обновляем цвета тиков
            current_ax.set_xticklabels(current_ax.get_xticklabels(), color=text_color)
            current_ax.set_yticklabels(current_ax.get_yticklabels(), color=text_color)
            
            # Обновляем цвета текстовых аннотаций
            for text in current_ax.texts:
                text.set_color(text_color)
            
            self.canvas.draw()

    def get_settings(self):
        """Получает настройки для бэктеста"""
        current_settings = {}
        if hasattr(self.parent, 'trading_status_window') and \
           hasattr(self.parent.trading_status_window.settings_content, 'get_settings'):
            current_settings = self.parent.trading_status_window.settings_content.get_settings()
            
        return {
            'df': self.df,
            'initial_balance': current_settings.get('initial_balance', 1000),
            'position_size': current_settings.get('position_size', 100),
            'position_type': current_settings.get('position_type', 'percent'),
            'profit_factor': current_settings.get('profit_factor', 1.5),
            'leverage': current_settings.get('leverage', 1),
            'commission': current_settings.get('commission', 0.0008)
        }

    def show_optimization_results(self, results):
        """Display optimization results on the plot"""
        if len(results) == 0:
            return
            
        # Single parameter optimization
        if isinstance(results[0][0], (int, float)):  # Changed check
            values = [r[0] for r in results]  # First element is parameter value
            pnls = [r[1] for r in results]   # Second element is PnL
            param_name = next(name for name, checkbox in self.param_checkboxes.items() 
                            if checkbox.isChecked())
            self.plot_one_param_results(values, pnls, param_name)
            
        # Two parameter optimization
        else:  # results[0][0] is tuple of two values
            param_names = [name for name, checkbox in self.param_checkboxes.items() if checkbox.isChecked()]
            if len(param_names) != 2:
                return
                
            # Extract unique values for each parameter
            values1 = sorted(set(r[0][0] for r in results))  # First parameter values
            values2 = sorted(set(r[0][1] for r in results))  # Second parameter values
            
            # Create results grid
            grid_results = np.zeros((len(values1), len(values2)))
            for (v1, v2), pnl in results:
                i = values1.index(v1)
                j = values2.index(v2)
                grid_results[i,j] = pnl
                
            self.plot_two_param_results(values1, values2, grid_results, param_names[0], param_names[1])

        # Update best parameters
        best_result = max(results, key=lambda x: x[1])  # Sort by PnL
        if isinstance(best_result[0], (int, float)):
            param_name = next(name for name, checkbox in self.param_checkboxes.items() 
                            if checkbox.isChecked())
            self.current_strategy.set_parameter(param_name, best_result[0])
        else:
            param_names = [name for name, checkbox in self.param_checkboxes.items() 
                         if checkbox.isChecked()]
            for name, value in zip(param_names, best_result[0]):
                self.current_strategy.set_parameter(name, value)

    def add_differential_evolution_settings(self):
        """Add settings for differential evolution"""
        settings = self.method_settings['Дифференциальная эволюция']
        for name, (label, default, type_, min_, max_) in settings.items():
            layout = QHBoxLayout()
            label_widget = QLabel(label)
            if type_ == int:
                widget = QSpinBox()
                widget.setRange(min_, max_)
            else:
                widget = QDoubleSpinBox()
                widget.setRange(min_, max_)
                widget.setDecimals(3)
            widget.setValue(default)
            layout.addWidget(label_widget)
            layout.addWidget(widget)
            self.method_settings_layout.addLayout(layout)

    def add_annealing_settings(self):
        """Add settings for simulated annealing"""
        settings = self.method_settings['Имитация отжига']
        for name, (label, default, type_, min_, max_) in settings.items():
            layout = QHBoxLayout()
            label_widget = QLabel(label)
            widget = QDoubleSpinBox()
            widget.setRange(min_, max_)
            widget.setDecimals(3)
            widget.setValue(default)
            layout.addWidget(label_widget)
            layout.addWidget(widget)
            self.method_settings_layout.addLayout(layout)

    def add_nelder_mead_settings(self):
        """Add settings for Nelder-Mead method"""
        settings = self.method_settings['Метод Нелдера-Мида']
        for name, (label, default, type_, min_, max_) in settings.items():
            layout = QHBoxLayout()
            label_widget = QLabel(label)
            if type_ == int:
                widget = QSpinBox()
            else:
                widget = QDoubleSpinBox()
                widget.setDecimals(5)
            widget.setRange(min_, max_)
            widget.setValue(default)
            layout.addWidget(label_widget)
            layout.addWidget(widget)
            self.method_settings_layout.addLayout(layout)

    def on_method_changed(self, method_name):
        """Handle optimization method change"""
        # Clear existing settings and update with new ones
        self.update_method_settings()
        
        # Update parameters table for the selected method
        self.update_fast_params_table()
        
        # Update layout
        if hasattr(self, 'fast_params_table'):
            self.fast_params_table.resizeColumnsToContents()
            self.fast_params_table.resizeRowsToContents()

        # Store current method name
        self.current_method = method_name

    def update_iteration_result(self, iteration, params, pnl):
        """Update iteration results in text area"""
        text = f"Iteration {iteration}:\n"
        for param_name, value in params:
            param = self.current_strategy.parameters[param_name]
            text += f"  {param.description}: {value:.6f}\n"
        text += f"  PnL: {pnl:.2f}\n\n"
        
        self.iteration_text.append(text)
        scrollbar = self.iteration_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
