from .block_model import StrategyModel
from .blocks import BLOCK_REGISTRY

class CodeGenerator:
    def __init__(self, model: StrategyModel):
        self.model = model

    def generate_strategy_class(self, strategy_name: str) -> str:
        """Generates complete strategy class code"""
        code = []
        # Import statements
        code.append("from lib.strategies.base_strategy import BaseStrategy")
        code.append("import ta")
        code.append("")
        
        # Class definition
        code.append(f"class {strategy_name}(BaseStrategy):")
        code.append("    def __init__(self):")
        code.append("        super().__init__()")
        code.append(f"        self.name = \"{strategy_name}\"")
        code.append("        self.description = \"Strategy generated from visual constructor\"")
        code.append("")
        
        # Generate parameters setup method
        code.append("    def _setup_parameters(self):")
        params = self._get_block_parameters()
        for param in params:
            code.append(f"        self.add_parameter(")
            code.append(f"            \"{param['name']}\",")
            code.append(f"            {param['default_value']},")
            code.append(f"            \"{param['description']}\",")
            code.append(f"            {param['type']},")
            code.append(f"            min_value={param['min_value']},")
            code.append(f"            max_value={param['max_value']}")
            code.append("        )")
        code.append("")

        # Generate run method
        code.append("    def run(self, df, initial_balance, position_size, position_type, profit_factor):")
        code.append("        # Get parameters")
        for param in params:
            code.append(f"        {param['name']} = self.parameters[\"{param['name']}\"]")
        code.append("")
        
        # Generate indicators calculation
        indicators = self._generate_indicators_code()
        code.extend(indicators)
        code.append("")
        
        # Trading logic setup
        code.extend([
            "        current_balance = initial_balance",
            "        qty = position_size",
            "        if position_type == \"percent\":",
            "            qty = position_size / 100 * current_balance",
            "        percent = int(len(df) / 100)",
            "        position_open = False",
            "",
            "        for i in range(len(df)):",
            "            if i % percent == 0:",
            "                self.manager.progress_changed.emit(int(i / len(df) * 100))",
            ""
        ])

        # Generate trading logic
        trading_logic = self._generate_trading_logic()
        code.extend(trading_logic)
        
        return "\n".join(code)

    def _get_block_parameters(self) -> list:
        """Extracts parameters from blocks"""
        params = []
        for block in self.model.blocks.values():
            block_def = BLOCK_REGISTRY[block.type]()
            settings = block_def.get_settings()
            for name, value in settings.items():
                param = {
                    "name": f"{block.type.lower()}_{name.lower()}_{block.id}",
                    "default_value": value,
                    "description": f"{block.type} {name}",
                    "type": type(value).__name__,
                    "min_value": 0,  # Default values, should be customized per parameter type
                    "max_value": 100
                }
                params.append(param)
        return params

    def _generate_indicators_code(self) -> list:
        """Generates code for technical indicators"""
        code = []
        indicators = []
        
        for block in self.model.blocks.values():
            if block.type == 'RSI':
                code.append(f"        df['rsi_{block.id}'] = ta.momentum.RSIIndicator(df['close']).rsi()")
                indicators.append(f"rsi_{block.id}")
            elif block.type == 'BB':
                code.extend([
                    f"        bb_{block.id} = ta.volatility.BollingerBands(df['close'])",
                    f"        df['bb_upper_{block.id}'] = bb_{block.id}.bollinger_hband()",
                    f"        df['bb_middle_{block.id}'] = bb_{block.id}.bollinger_mavg()", 
                    f"        df['bb_lower_{block.id}'] = bb_{block.id}.bollinger_lband()"
                ])
                indicators.extend([f"bb_upper_{block.id}", f"bb_middle_{block.id}", f"bb_lower_{block.id}"])
            elif block.type == 'EMA':
                code.append(f"        df['ema_{block.id}'] = ta.trend.EMAIndicator(df['close']).ema_indicator()")
                indicators.append(f"ema_{block.id}")

        if indicators:
            code.append(f"        self.manager.indicators = {indicators}")
            
        return code

    def _generate_trading_logic(self) -> list:
        """Generates trading logic code"""
        code = []
        code.append("            if position_open:")
        code.append("                # Check existing position")
        
        # Generate position management code
        for block in self.model.blocks.values():
            if block.type == 'ClosePosition':
                connected_inputs = self._get_connected_inputs(block)
                code.extend([
                    "                if " + connected_inputs.get('Сигнал', 'False') + ":",
                    f"                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])",
                    "                    position_open = False",
                    "                    current_balance = self.manager.get_current_balance()",
                    "                    if position_type == \"percent\":",
                    "                        qty = position_size / 100 * current_balance"
                ])

        code.append("")
        code.append("            if not position_open:")
        
        # Generate position opening code
        for block in self.model.blocks.values():
            if block.type in ['OpenPositionBlock']:
                connected_inputs = self._get_connected_inputs(block)
                direction = block.settings.get("Направление", "LONG").lower()
                code.extend([
                    "                if " + connected_inputs.get('Сигнал', 'False') + ":",
                    f"                    tp, sl = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, '{direction}', 15)",
                    f"                    posId = self.manager.open_position('{direction}', 'market', tp, sl, df['close'].iloc[i], qty, df.index[i])",
                    "                    position_open = True"
                ])

        return code

    def _get_connected_inputs(self, block) -> dict:
        """Gets values from connected inputs for a block"""
        inputs = {}
        for input_port in block.inputs:
            if input_port.connected_to:
                # Find the source block and its output
                source_block_id = input_port.connected_to[0].split('.')[0]
                source_block = self.model.blocks.get(source_block_id)
                if source_block:
                    inputs[input_port.id] = f"df['{source_block.type.lower()}_{source_block.id}']"
        return inputs

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
        """Generates code from node graph"""
        code = []
        
        # Process connections to build input mapping
        input_map = {}
        for conn in connections:
            to_node = conn['to_node']
            from_node = conn['from_node']
            
            if to_node not in input_map:
                input_map[to_node] = {}
            
            # Map the connection from output port to input port
            input_map[to_node][conn['to_port']] = {
                'node': from_node,
                'port': conn['from_port']
            }

        # Generate code for each node
        for node in nodes:
            node_id = node.name()
            node_inputs = input_map.get(node_id, {})
            
            if node.block_type == 'RSI':
                # Get price input from connection or use default
                price_conn = node_inputs.get('Цена', {})
                if price_conn:
                    price_node = price_conn['node']
                    price_port = price_conn['port']
                    price_input = f"df['{price_port.lower()}']"
                else:
                    price_input = "df['close']"
                
                period = node.get_property('period') or 14
                code.append(f"{node_id} = ta.momentum.RSIIndicator(close={price_input}, window={period}).rsi()")
            
            elif node.block_type == 'BB':
                price_conn = node_inputs.get('Цена', {})
                if price_conn:
                    price_node = price_conn['node']
                    price_port = price_conn['port']
                    price_input = f"df['{price_port.lower()}']"
                else:
                    price_input = "df['close']"
                    
                period = node.get_property('period') or 20
                std = node.get_property('std') or 2
                code.append(f"bb_{node_id} = ta.volatility.BollingerBands(close={price_input}, window={period}, window_dev={std})")
                code.append(f"bb_upper_{node_id} = bb_{node_id}.bollinger_hband()")
                code.append(f"bb_middle_{node_id} = bb_{node_id}.bollinger_mavg()")
                code.append(f"bb_lower_{node_id} = bb_{node_id}.bollinger_lband()")
            
            elif node.block_type == 'EMA':
                price_conn = node_inputs.get('Цена', {})
                if price_conn:
                    price_node = price_conn['node']
                    price_port = price_conn['port']
                    price_input = f"df['{price_port.lower()}']"
                else:
                    price_input = "df['close']"
                    
                period = node.get_property('period') or 14
                code.append(f"{node_id} = ta.trend.EMAIndicator(close={price_input}, window={period}).ema_indicator()")

            elif node.block_type == 'Константа':
                value = node.get_value()
                code.append(f"{node_id} = {value}")

            elif node.block_type == 'Сравнение':
                value1_conn = node_inputs.get('A', {})
                value2_conn = node_inputs.get('B', {})
                
                value1 = "0"
                value2 = "0"
                
                if value1_conn:
                    value1_node = value1_conn['node']
                    value1 = f"{value1_node}"
                if value2_conn:
                    value2_node = value2_conn['node']
                    value2 = f"{value2_node}"
                    
                comp_type = node.get_property('type')
                if comp_type == 'Больше':
                    code.append(f"{node_id} = {value1} > {value2}")
                elif comp_type == 'Меньше':
                    code.append(f"{node_id} = {value1} < {value2}")
                else:
                    code.append(f"{node_id} = {value1} == {value2}")

        return "\n".join(code)
