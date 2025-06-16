from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel, QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal

class StrategySettingsWindow(QWidget):
    parameters_changed = pyqtSignal()  # Add signal

    def __init__(self, strategy, theme="dark", parent=None):
        super().__init__(parent)
        self.strategy = strategy
        self.current_theme = theme
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignTop)  # Add top alignment

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 9, 0)
        scroll_layout.setSpacing(2)
        scroll_layout.setAlignment(Qt.AlignTop)  # Add top alignment

        # Add parameters frame
        params_frame = QFrame()
        params_frame.setFrameShape(QFrame.StyledPanel)
        if self.current_theme == "dark":
            params_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    padding: 3px;
                }
            """)
        else:
            params_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 0, 0, 0.00);
                    border-radius: 8px;
                    padding: 3px;
                }
            """)

        params_layout = QVBoxLayout(params_frame)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(2)
        params_layout.setAlignment(Qt.AlignTop)  # Add top alignment

        # Add title
        title = QLabel("Strategy Parameters")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #669FD3; padding: 3px;")
        title.setFixedHeight(25)
        params_layout.addWidget(title)

        # Create input widgets for each parameter
        self.param_widgets = {}
        for key, param in self.strategy.parameters.items():
            param_layout = QHBoxLayout()
            param_layout.setAlignment(Qt.AlignTop)  # Add top alignment
            
            # Label with description
            label = QLabel(f"{param.description}")
            if self.current_theme == "dark":
                label.setStyleSheet("color: #ffffff; font-size: 12px;")
            else:
                label.setStyleSheet("color: #000000; font-size: 12px;")
            label.setFixedHeight(25)
            param_layout.addWidget(label)

            # Input widget based on parameter type
            if param.type == int:
                widget = QSpinBox()
                if param.min_value is not None:
                    widget.setMinimum(int(param.min_value))
                if param.max_value is not None:
                    widget.setMaximum(int(param.max_value))
                widget.setValue(param.value)
                widget.setFixedHeight(25)  # Set fixed height
                widget.valueChanged.connect(lambda value, k=key: self.on_parameter_changed(k, value))
            elif param.type == float:
                widget = QDoubleSpinBox()
                if param.min_value is not None:
                    widget.setMinimum(param.min_value)
                if param.max_value is not None:
                    widget.setMaximum(param.max_value)
                widget.setValue(param.value)
                widget.setFixedHeight(25)  # Set fixed height
                widget.valueChanged.connect(lambda value, k=key: self.on_parameter_changed(k, value))
            else:
                widget = QLineEdit(str(param.value))
                widget.setFixedHeight(25)  # Set fixed height
                widget.textChanged.connect(lambda text, k=key: self.on_parameter_changed(k, text))

            widget.setStyleSheet("""
                QSpinBox, QDoubleSpinBox, QLineEdit {
                    margin-bottom: 10px;
                    padding: 2px 5px;
                    border: 1px solid #669FD3;
                    border-radius: 4px;
                }
            """)
            self.param_widgets[key] = widget
            param_layout.addWidget(widget)
            param_layout.setSpacing(5)  # Set spacing between label and input
            params_layout.addLayout(param_layout)

        scroll_layout.addWidget(params_frame)

        # Add testing settings frame
        testing_frame = QFrame()
        testing_frame.setFrameShape(QFrame.StyledPanel)
        if self.current_theme == "dark":
            testing_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    padding: 3px;
                }
            """)
        else:
            testing_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 0, 0, 0.00);
                    border-radius: 8px;
                    padding: 3px;
                }
            """)

        testing_layout = QVBoxLayout(testing_frame)
        testing_layout.setContentsMargins(0, 0, 0, 0)
        testing_layout.setSpacing(2)

        # Add testing settings title
        testing_title = QLabel("Testing Settings")
        testing_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #669FD3; padding: 3px;")
        testing_layout.addWidget(testing_title)

        # Add testing settings fields
        self.testing_widgets = {}
        testing_params = {
            'initial_balance': ('Initial Balance (USDT)', 1000, int),
            'position_size': ('Position Size', 100, int),
            'leverage': ('Leverage', 1, float),
            'profit_factor': ('Profit Factor', 1.5, float),
            'commission': ('Commission', 0.0008, float),
        }

        for key, (label_text, default_value, param_type) in testing_params.items():
            param_layout = QHBoxLayout()
            label = QLabel(label_text)
            if self.current_theme == "dark":
                label.setStyleSheet("color: #ffffff; font-size: 12px;")
            else:
                label.setStyleSheet("color: #000000; font-size: 12px;")
            
            widget = QDoubleSpinBox() if (param_type == float or param_type == int) else QSpinBox()
            widget.setValue(default_value)
            widget.setDecimals(6 if key == 'commission' else 0)
            if key == 'profit_factor': widget.setDecimals(2)
            widget.setRange(0, 1000000)
            widget.valueChanged.connect(self.parameters_changed.emit)
            
            param_layout.addWidget(label)
            param_layout.addWidget(widget)
            testing_layout.addLayout(param_layout)
            self.testing_widgets[key] = widget

        # Add position type selection
        param_layout = QHBoxLayout()
        label = QLabel("Position Type")
        self.position_type = QComboBox()
        self.position_type.addItems(["percent", "fixed"])
        self.position_type.currentTextChanged.connect(self.parameters_changed.emit)
        param_layout.addWidget(label)
        param_layout.addWidget(self.position_type)
        testing_layout.addLayout(param_layout)
        self.testing_widgets['position_type'] = self.position_type

        scroll_layout.addWidget(testing_frame)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def get_parameters(self):
        """Return current parameter values"""
        params = {}
        for key, widget in self.param_widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                params[key] = widget.value()
            else:
                params[key] = widget.text()
        return params

    def get_settings(self):
        """Return all settings including testing parameters"""
        settings = {
            'initial_balance': self.testing_widgets['initial_balance'].value(),
            'position_size': self.testing_widgets['position_size'].value(),
            'leverage': self.testing_widgets['leverage'].value(),
            'profit_factor': self.testing_widgets['profit_factor'].value(),
            'commission': self.testing_widgets['commission'].value(),
            'position_type': self.testing_widgets['position_type'].currentText()
        }
        return settings

    def on_parameter_changed(self, key, value):
        """Handle parameter value change"""
        self.strategy.set_parameter(key, value)
        self.parameters_changed.emit()
