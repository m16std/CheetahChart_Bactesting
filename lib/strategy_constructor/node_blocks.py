from NodeGraphQt import BaseNode
from ..strategy_constructor.blocks import BLOCK_REGISTRY

class StrategyNode(BaseNode):
    NODE_NAME = None  # Will be set by derived classes

    def __init__(self):
        super().__init__()
        if hasattr(self, 'block_type'):
            self.create_node()

    def create_node(self):
        block_def = None
        for category, blocks in BLOCK_REGISTRY.items():
            if self.block_type in blocks:
                block_def = blocks[self.block_type]()
                break
        
        if not block_def:
            raise KeyError(f"Block type '{self.block_type}' not found in registry")

        # Add ports and set name
        for input_name in block_def.get_inputs():
            self.add_input(input_name)
        for output_name in block_def.get_outputs():
            self.add_output(output_name)
        self.set_name(self.block_type)
        
        if self.block_type == 'Константа':
            self.add_text_input('value', 'Значение')
            
        elif self.block_type == 'Открыть Позицию':
            self.add_combo_menu('direction', 'Направление:', items=['LONG', 'SHORT'])

        elif self.block_type == 'Сравнение':
            self.add_combo_menu('type', 'Тип:', items=['Больше', 'Меньше', 'Равно'])

        self.model.color = (31, 33, 36)
        self.model.border_color = (58, 65, 68)

    def on_property_changed(self, prop_name, value):
        """Handle property value changes"""
        super().on_property_changed(prop_name, value)
        
        if self.block_type == 'Constant':
            # Обновляем выходной порт при изменении значения
            try:
                float_val = float(value)
                if 'value' in self.outputs:
                    self.outputs['value'].value = float_val
            except ValueError:
                pass
        
        elif self.block_type == 'Open Position':
            if prop_name == 'direction':
                # Надо добавить дополнительную логику при смене направления
                pass    

    def get_settings(self):
        """Get all node settings."""
        return {
            name: self.model.get_property(name)
            for name in self.model.properties.keys()
        }
