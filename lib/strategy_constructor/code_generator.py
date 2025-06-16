from .block_model import StrategyModel
from .blocks import BLOCK_REGISTRY

class CodeGenerator:
    def __init__(self, graph_data):
        self.graph_data = graph_data
        self.nodes = graph_data['nodes']
        self.connections = graph_data['connections']
        self.node_outputs = {}

    def generate_strategy_class(self, strategy_name: str) -> str:
        """Generates strategy class code from graph json data"""
        # Prepare imports and class definition
        code = [
            "from lib.strategies.base_strategy import BaseStrategy",
            "import ta",
            "import numpy as np",
            "",
            f"class {strategy_name}(BaseStrategy):",
            "    def __init__(self):",
            "        super().__init__()",
            f"        self.name = \"{strategy_name}\"",
            "        self.description = \"Strategy generated from visual constructor\"",
            "",
            "    def _setup_parameters(self):"
        ]

        # Generate parameters section
        params = []
        for node_id, node in self.nodes.items():
            if node['type_'].endswith('RSI'):
                params.extend([
                    "        self.add_parameter(",
                    "            \"rsi_period\",",
                    "            14,",
                    "            \"RSI Period\",",
                    "            int,",
                    "            min_value=2,",
                    "            max_value=50",
                    "        )"
                ])
            elif node['type_'].endswith('Константа'):
                value = node.get('custom', {}).get('value', '0')
                params.extend([
                    "        self.add_parameter(",
                    f"            \"const_{node_id}\",",
                    f"            {value},",
                    "            \"Constant Value\",",
                    "            float,",
                    "            min_value=0,",
                    "            max_value=100",
                    "        )"
                ])

        code.extend(params)

        # Generate run method
        code.extend([
            "",
            "    def run(self, df, initial_balance, position_size, position_type, profit_factor):",
            "        # Initialize parameters"
        ])

        # Initialize parameters
        param_init = []
        for node_id, node in self.nodes.items():
            if node['type_'].endswith('RSI'):
                param_init.append("        rsi_period = self.parameters['rsi_period'].value")
            elif node['type_'].endswith('Константа'):
                param_init.append(f"        const_{node_id} = self.parameters['const_{node_id}'].value")
        
        code.extend(param_init)

        # Generate indicators
        indicators = []
        for node_id, node in self.nodes.items():
            if node['type_'].endswith('RSI'):
                # Find input price source
                price_input = self._get_input_source(node_id, 'Цена')
                indicators.extend([
                    f"        df['rsi_{node_id}'] = ta.momentum.RSIIndicator({price_input}, window=rsi_period).rsi()",
                    f"        self.manager.indicators = ['rsi_{node_id}']"
                ])
                self.node_outputs[node_id] = f"df['rsi_{node_id}']"

        code.extend(indicators)

        # Trading setup
        # Check if there are any close position blocks
        has_close_block = any(
            node['type_'].endswith('Закрыть позицию') 
            for node in self.nodes.values()
        )

        code.extend([
            "",
            "        current_balance = initial_balance",
            "        qty = position_size",
            "        if position_type == \"percent\":",
            "            qty = position_size / 100 * current_balance",
            "        percent = int(len(df) / 100)",
            "        position_open = False",
            "        posId = None",
            "",
            "        for i in range(len(df)):",
            "            if i % percent == 0:",
            "                self.manager.progress_changed.emit(int(i / len(df) * 100))",
            "",
        ])

        # Add TP/SL check only if there's no close position block
        if not has_close_block:
            code.extend([
                "            if position_open:",
                "                if self.manager.check_tp_sl(posId, tpTriggerPx, slTriggerPx, df.index[i]):",
                "                    position_open = False",
                "                    current_balance = self.manager.get_current_balance()",
                "                    if position_type == \"percent\":",
                "                        qty = position_size / 100 * current_balance",
                ""
            ])

        # Generate trading signals
        signals = []
        for node_id, node in self.nodes.items():
            if node['type_'].endswith('Сравнение'):
                input_a = self._get_input_source(node_id, 'A')
                input_b = self._get_input_source(node_id, 'B')
                comp_type = node.get('custom', {}).get('type', 'Больше')
                
                if comp_type == 'Больше':
                    condition = f"{input_a}.iloc[i] > {input_b}"
                elif comp_type == 'Меньше':
                    condition = f"{input_a}.iloc[i] < {input_b}"
                else:
                    condition = f"{input_a}.iloc[i] == {input_b}"

                # Check if this comparison triggers position open/close
                if self._is_connected_to(node_id, 'Открыть позицию'):
                    target_node = self._get_connected_node(node_id, 'Открыть позицию')
                    direction = target_node.get('custom', {}).get('direction', 'LONG').lower()
                    
                    # Проверяем наличие блока закрытия позиции
                    has_close_block = any(
                        node['type_'].endswith('Закрыть позицию') 
                        for node in self.nodes.values()
                    )
                    
                    if has_close_block:
                        # Если есть блок закрытия, не используем TP/SL
                        signals.extend([
                            "            if not position_open:",
                            f"                if {condition}:",
                            f"                    posId = self.manager.open_position('{direction}', 'market', 0, 0, df['close'].iloc[i], qty, df.index[i])",
                            "                    position_open = True"
                        ])
                    else:
                        # Если нет блока закрытия, используем TP/SL
                        signals.extend([
                            "            if not position_open:",
                            f"                if {condition}:",
                            f"                    tpTriggerPx, slTriggerPx = self.manager.get_tp_sl(df, i, df['close'].iloc[i], profit_factor, '{direction}', 15)",
                            f"                    posId = self.manager.open_position('{direction}', 'market', tpTriggerPx, slTriggerPx, df['close'].iloc[i], qty, df.index[i])",
                            "                    position_open = True"
                        ])
                elif self._is_connected_to(node_id, 'Закрыть позицию'):
                    signals.extend([
                        "            else:",
                        f"                if {condition}:",
                        f"                    self.manager.close_position(posId, df['close'].iloc[i], df.index[i])",
                        "                    position_open = False",
                        "                    current_balance = self.manager.get_current_balance()",
                        "                    if position_type == \"percent\":",
                        "                        qty = position_size / 100 * current_balance"
                    ])

        code.extend(signals)
        return "\n".join(code)

    def _get_input_source(self, node_id, port_name):
        """Get the source expression for a block input"""
        for conn in self.connections:
            if conn['in'][0] == node_id and conn['in'][1] == port_name:
                source_node = self.nodes[conn['out'][0]]
                if source_node['type_'].endswith('Константа'):
                    return f"const_{conn['out'][0]}"
                elif source_node['type_'].endswith('Цена'):
                    if conn['out'][1] == 'Закрытие':
                        return 'df["close"]'
                    elif conn['out'][1] == 'Открытие':
                        return 'df["open"]'
                    elif conn['out'][1] == 'Максимум':
                        return 'df["high"]'
                    elif conn['out'][1] == 'Минимум':
                        return 'df["low"]'
                elif source_node['type_'].endswith('RSI'):
                    # Используем переменную с RSI
                    return f"df['rsi_{conn['out'][0]}']"
                else:
                    return self.node_outputs.get(conn['out'][0], 'df["close"]')
        return 'df["close"]'

    def _is_connected_to(self, node_id, target_type):
        """Check if node is connected to a specific type of node"""
        for conn in self.connections:
            if conn['out'][0] == node_id:
                target_node = self.nodes[conn['in'][0]]
                if target_node['type_'].endswith(target_type):
                    return True
        return False

    def _get_connected_node(self, node_id, target_type):
        """Get node connected to source node of specific type"""
        for conn in self.connections:
            if conn['out'][0] == node_id:
                target_node = self.nodes[conn['in'][0]]
                if target_node['type_'].endswith(target_type):
                    return target_node
        return None


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
                    inputs[input_port.id] = f"df['{source_block.type.lower()}_{source_block_id}']"
        return inputs

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
        return "\n".join(code)
