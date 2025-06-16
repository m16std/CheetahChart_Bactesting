from PyQt5.QtCore import QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor
import numpy as np

class OptimizationThread(QThread):
    progress_changed = pyqtSignal(int)
    optimization_complete = pyqtSignal(list)

    def __init__(self, strategy, params, settings, parent=None):
        super().__init__(parent)
        self.strategy = strategy
        self.params = params
        
        self.strategy.manager.df = settings['df']
        self.strategy.manager.leverage = settings['leverage']
        self.strategy.manager.commission = settings['commission']
        
        self.run_settings = {
            'df': settings['df'],
            'initial_balance': settings['initial_balance'],
            'position_size': settings['position_size'],
            'position_type': settings['position_type'],
            'profit_factor': settings['profit_factor']
        }
        print(self.run_settings)

    def run(self):
        if (len(self.params) == 1):
            self.optimize_one_param(*self.params[0])
        elif (len(self.params) == 2):
            self.optimize_two_params(self.params[0], self.params[1])
        else:
            self.optimize_multiple_params(self.params)

    def run_backtest(self, param_values):
        """Run single backtest with given parameters"""
        for name, value in param_values:
            #print(f"Setting parameter {name} to {value}")
            if self.strategy.parameters[name].type == int:
                value = int(value)
            elif self.strategy.parameters[name].type == float:
                value = float(value)
            self.strategy.set_parameter(name, value)
 
        self.strategy.run(**self.run_settings)
        
        total_pnl = sum(pos['pnl'] for pos in self.strategy.manager.positions)
        #print(f"Total PnL: {total_pnl:.4f}")
        #print(len(self.strategy.manager.positions))
        #print(self.strategy.manager.positions[0])
        #print(self.strategy.manager.positions[1])
        #print(self.strategy.manager.balance['value'].iloc[-1])
        return total_pnl

    def optimize_one_param(self, param):
        name, min_val, max_val, points = param
        values = np.linspace(min_val, max_val, int(points))
        results = []
        
        total = len(values)
        for i, val in enumerate(values):
            param_value = float(val)
            if self.strategy.parameters[name].type == int:
                param_value = int(val)
            pnl = self.run_backtest([(name, param_value)])
            results.append((param_value, pnl))
            self.progress_changed.emit(int((i + 1) / total * 100))
            
        self.optimization_complete.emit(results)

    def optimize_two_params(self, param1, param2):
        name1, min1, max1, points1 = param1
        name2, min2, max2, points2 = param2

        points1 = int(points1)
        points2 = int(points2)
        
        values1 = np.linspace(min1, max1, points1)
        values2 = np.linspace(min2, max2, points2)
        
        total = points1 * points2
        current = 0
        results = []

        for v1 in values1:
            for v2 in values2:
                v1_converted = int(v1) if self.strategy.parameters[name1].type == int else v1
                v2_converted = int(v2) if self.strategy.parameters[name2].type == int else v2
                
                pnl = self.run_backtest([(name1, v1_converted), (name2, v2_converted)])
                results.append(((v1_converted, v2_converted), pnl))
                
                current += 1
                self.progress_changed.emit(int(current / total * 100))
                
        self.optimization_complete.emit(results)

    def optimize_multiple_params(self, params):
        with ThreadPoolExecutor() as executor:
            param_combinations = self.generate_param_combinations(params)
            total = len(param_combinations)
            
            futures = []
            for param_set in param_combinations:
                futures.append(executor.submit(self.run_backtest, param_set))
                
            results = []
            for i, future in enumerate(futures):
                results.append((param_combinations[i], future.result()))
                self.progress_changed.emit(int((i + 1) / total * 100))
                
        self.optimization_complete.emit(results)

    def generate_param_combinations(self, params):
        """Генерирует все возможные комбинации параметров"""
        ranges = []
        names = []
        for name, min_val, max_val, points in params:
            names.append(name)
            ranges.append(np.linspace(min_val, max_val, int(points)))
            
        combinations = []
        for values in np.array(np.meshgrid(*ranges)).T.reshape(-1, len(ranges)):
            combinations.append(list(zip(names, values)))
            
        return combinations
