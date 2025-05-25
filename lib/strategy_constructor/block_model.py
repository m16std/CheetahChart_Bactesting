from dataclasses import dataclass
from typing import List, Dict, Any
import json

@dataclass
class BlockPort:
    id: str
    block_id: str
    is_input: bool
    position: tuple[float, float]
    connected_to: List[str] = None

@dataclass
class Block:
    id: str
    type: str
    position: tuple[float, float]
    size: tuple[float, float]
    settings: Dict[str, Any]
    inputs: List[BlockPort]
    outputs: List[BlockPort]

class StrategyModel:
    def __init__(self):
        self.blocks: Dict[str, Block] = {}
        
    def add_block(self, block: Block):
        self.blocks[block.id] = block
        
    def connect_ports(self, output_port_id: str, input_port_id: str):
        for block in self.blocks.values():
            for port in block.inputs + block.outputs:
                if port.id == output_port_id:
                    if port.connected_to is None:
                        port.connected_to = []
                    port.connected_to.append(input_port_id)
                    
    def save_to_file(self, filename: str):
        with open(filename, 'w') as f:
            json.dump(self.__dict__, f, default=lambda o: o.__dict__)
            
    @classmethod
    def load_from_file(cls, filename: str) -> 'StrategyModel':
        with open(filename, 'r') as f:
            data = json.load(f)
            model = cls()
            model.blocks = {
                k: Block(**v) for k, v in data['blocks'].items()
            }
            return model
