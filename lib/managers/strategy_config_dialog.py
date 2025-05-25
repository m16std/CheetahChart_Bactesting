from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSpinBox, QDoubleSpinBox, QLineEdit, QPushButton)

class StrategyConfigDialog(QDialog):
    def __init__(self, strategy, parent=None):
        super().__init__(parent)
        self.strategy = strategy
        self.setWindowTitle(f"Configure {strategy.name}")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.param_widgets = {}

        # Add description
        desc_label = QLabel(self.strategy.description)
        layout.addWidget(desc_label)

        # Create widgets for each parameter
        for key, param in self.strategy.get_parameters().items():
            param_layout = QHBoxLayout()
            
            # Label with description
            label = QLabel(f"{param.name}: {param.description}")
            param_layout.addWidget(label)

            # Input widget based on parameter type
            if param.type == int:
                widget = QSpinBox()
                if param.min_value is not None:
                    widget.setMinimum(int(param.min_value))
                if param.max_value is not None:
                    widget.setMaximum(int(param.max_value))
                widget.setValue(param.value)
            elif param.type == float:
                widget = QDoubleSpinBox()
                if param.min_value is not None:
                    widget.setMinimum(param.min_value)
                if param.max_value is not None:
                    widget.setMaximum(param.max_value)
                widget.setValue(param.value)
            else:
                widget = QLineEdit(str(param.value))

            self.param_widgets[key] = widget
            param_layout.addWidget(widget)
            layout.addLayout(param_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        
        save_button.clicked.connect(self.save_config)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def save_config(self):
        # Save all parameter values
        for key, widget in self.param_widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                value = widget.value()
            else:
                value = widget.text()
            self.strategy.set_parameter(key, value)
        self.accept()
