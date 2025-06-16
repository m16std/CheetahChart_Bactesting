from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BlockDefinition(ABC):
    @abstractmethod
    def get_inputs(self) -> List[str]:
        pass
        
    @abstractmethod
    def get_outputs(self) -> List[str]:
        pass
        
    @abstractmethod
    def get_settings(self) -> Dict[str, Any]:
        pass

# Base block implementations
class PriceBlock(BlockDefinition):
    def get_inputs(self):
        return []
        
    def get_outputs(self):
        return ["Открытие", "Закрытие", "Максимум", "Минимум"]
        
    def get_settings(self):
        return {}

class RSIBlock(BlockDefinition):
    def get_inputs(self):
        return ["Цена", "Период"]
        
    def get_outputs(self):
        return ["RSI"]
        
    def get_settings(self):
        return {"Период": 14}

class BBBlock(BlockDefinition):
    def get_inputs(self):
        return ["Цена", "Период", "Отклонение"]
    
    def get_outputs(self):
        return ["Верхняя", "Средняя", "Нижняя"]
    
    def get_settings(self):
        return {"Период": 20, "Отклонение": 2}

class EMABlock(BlockDefinition):
    def get_inputs(self):
        return ["Цена", "Период"]
    
    def get_outputs(self):
        return ["EMA"]
    
    def get_settings(self):
        return {"Период": 14}

class ConstantBlock(BlockDefinition):
    def get_inputs(self):
        return []
    
    def get_outputs(self):
        return ["Значение"]
    
    def get_settings(self):
        return {"Значение": 0.0}

class CompareBlock(BlockDefinition):
    def get_inputs(self):
        return ["A", "B"]
    
    def get_outputs(self):
        return ["Результат"]
    
    def get_settings(self):
        return {}

class OpenPositionBlock(BlockDefinition):
    def get_inputs(self):
        return ['Сигнал', 'TP', 'SL', 'Размер']
    
    def get_outputs(self):
        return ['ID']
    
    def get_settings(self):
        return {
            "Направление": "LONG"
        }

class ClosePositionBlock(BlockDefinition):
    def get_inputs(self):
        return ['Сигнал', "ID"]
    
    def get_outputs(self):
        return ["Закрыта"]
    
    def get_settings(self):
        return {}

class VariableBlock(BlockDefinition):
    def get_inputs(self):
        return ['Запись']
    
    def get_outputs(self):
        return ['Чтение']
    
    def get_settings(self):
        return {}

class CounterBlock(BlockDefinition):
    def __init__(self):
        self.count = 0
        
    def get_inputs(self):
        return ['Увеличить', 'Уменьшить', 'Сброс']
    
    def get_outputs(self):
        return ['Счетчик']
    
    def get_settings(self):
        return {}

class AddBlock(BlockDefinition):
    def get_inputs(self):
        return ['A', 'B']
    
    def get_outputs(self):
        return ['Сумма']
    
    def get_settings(self):
        return {}

class SubtractBlock(BlockDefinition):
    def get_inputs(self):
        return ['A', 'B']
    
    def get_outputs(self):
        return ['Разность']
    
    def get_settings(self):
        return {}

class MultiplyBlock(BlockDefinition):
    def get_inputs(self):
        return ['A', 'B']
    
    def get_outputs(self):
        return ['Произведение']
    
    def get_settings(self):
        return {}

class DivideBlock(BlockDefinition):
    def get_inputs(self):
        return ['A', 'B']
    
    def get_outputs(self):
        return ['Частное']
    
    def get_settings(self):
        return {}

# Update block registry with categories
BLOCK_REGISTRY = {
    'Индикаторы': {
        'Цена': PriceBlock,
        'RSI': RSIBlock,
        'BB': BBBlock,
        'EMA': EMABlock,
    },
    'Переменные': {
        'Переменная': VariableBlock,
        'Сравнение': CompareBlock,
        'Константа': ConstantBlock,
        'Счетчик': CounterBlock 
    },
    'Математика': {
        'Сложение': AddBlock,
        'Вычитание': SubtractBlock, 
        'Умножение': MultiplyBlock,
        'Деление': DivideBlock
    },
    'Торговля': {
        'Открыть позицию': OpenPositionBlock,
        'Закрыть позицию': ClosePositionBlock
    }
}
