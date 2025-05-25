from .block_model import StrategyModel
from .blocks import BLOCK_REGISTRY

class CodeGenerator:
    def __init__(self, model: StrategyModel):
        self.model = model
        
    def generate(self) -> str:
        code = []
        code.append("def strategy(df):")
        code.append("    positions = []")
        
        # Generate variables for each block output
        var_map = {}
        for block in self.model.blocks.values():
            block_def = BLOCK_REGISTRY[block.type]()
            inputs = {
                port.id: var_map[port.connected_to[0]]
                for port in block.inputs
                if port.connected_to
            }
            
            block_code = block_def.generate_code(inputs)
            for output in block_def.get_outputs():
                var_name = f"{block.type.lower()}_{output}_{block.id}"
                var_map[block.id] = var_name
                code.append(f"    {var_name} = {block_code}")
        
        return "\n".join(code)

    def generate_from_graph(self, nodes, connections):
        code = []
        
        # Generate code for each node
        for node in nodes:
            if node.block_type == 'RSI':
                code.append(f"rsi_{node.id} = ta.momentum.RSIIndicator(price={node.inputs['price']}, window={node.inputs['period']}).rsi()")
            
            elif node.block_type == 'Bollinger Bands':
                code.append(f"bb_{node.id} = ta.volatility.BollingerBands(close={node.inputs['price']}, window={node.inputs['period']}, window_dev={node.inputs['std']})")
                code.append(f"bb_upper_{node.id} = bb_{node.id}.bollinger_hband()")
                code.append(f"bb_middle_{node.id} = bb_{node.id}.bollinger_mavg()")
                code.append(f"bb_lower_{node.id} = bb_{node.id}.bollinger_lband()")
            
            elif node.block_type == 'EMA':
                code.append(f"ema_{node.id} = ta.trend.EMAIndicator(close={node.inputs['price']}, window={node.inputs['period']}).ema_indicator()")

            elif node.block_type == 'Constant':
                code.append(f"const_{node.id} = {node.inputs['value']}")

            elif node.block_type == 'Compare':
                code.append(f"greater_{node.id} = {node.inputs['value1']} > {node.inputs['value2']}")
                code.append(f"equal_{node.id} = {node.inputs['value1']} == {node.inputs['value2']}")  
                code.append(f"less_{node.id} = {node.inputs['value1']} < {node.inputs['value2']}")

            elif node.block_type == 'Open Long':
                code.append(f"if {node.inputs['signal']}:")
                code.append(f"    pos_id_{node.id} = self.open_position('long', 'market', {node.inputs['tp']}, {node.inputs['sl']}, close, {node.inputs['size']}, timestamp)")

            elif node.block_type == 'Open Short':
                code.append(f"if {node.inputs['signal']}:")
                code.append(f"    pos_id_{node.id} = self.open_position('short', 'market', {node.inputs['tp']}, {node.inputs['sl']}, close, {node.inputs['size']}, timestamp)")

            elif node.block_type == 'Close Position':
                code.append(f"self.close_position({node.inputs['position_id']}, close, timestamp)")

        return "\n".join(code)
