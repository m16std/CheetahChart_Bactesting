from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import pandas as pd

from scipy.optimize import differential_evolution, dual_annealing, minimize

class StopOptimizationException(Exception):
    pass

class FastOptimizationThread(QThread):
    progress_changed = pyqtSignal(int)
    optimization_complete = pyqtSignal(list)
    iteration_update = pyqtSignal(int, list, float)  # New signal for iteration updates

    def __init__(self, strategy, params, bounds, optimizer, settings):
        super().__init__()
        self.strategy = strategy
        self.params = params
        self.bounds = bounds
        self.optimizer = optimizer

        # Handle DataFrame initialization
        df = settings['df']
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)
        
        # Ensure index is properly set
        if 'ts' in df.columns:
            df.set_index('ts', inplace=True)
        
        # Create deep copy of DataFrame
        self.run_settings = {
            'df': df.copy(deep=True),
            'initial_balance': settings['initial_balance'],
            'position_size': settings['position_size'],
            'position_type': settings['position_type'],
            'profit_factor': settings['profit_factor']
        }

        # Set manager settings
        self.manager_settings = {
            'leverage': settings.get('leverage', 1),
            'commission': settings.get('commission', 0.0008)
        }

        # Pass DataFrame to strategy manager
        self.strategy.manager.df = self.run_settings['df']
        
        self.iterations = 0
        self.stop_flag = False
        self.current_iteration = 0  # Добавляем счетчик итераций

    def objective_function(self, x):
        """Objective function to minimize (negative PnL)"""
        if self.stop_flag:  # Проверяем флаг остановки
            raise StopOptimizationException("Optimization stopped by user")
            
        x = np.array(x).ravel()
        

        # Set parameters
        for param_key, value in zip(self.params, x):
            param_type = self.strategy.parameters[param_key].type
            # Handle NaN values
            if np.isnan(value):
                return float('inf')
            # Convert value to correct type
            try:
                if param_type == int:
                    value = int(round(value))
                value = param_type(value)
                self.strategy.set_parameter(param_key, value)
            except (ValueError, TypeError):
                return float('inf')

        # Configure manager settings first
        self.strategy.manager.leverage = self.manager_settings['leverage']
        self.strategy.manager.commission = self.manager_settings['commission']
        self.iterations += 1 
        
        try:
            self.strategy.run(**self.run_settings)
            pnl = sum(pos['pnl'] for pos in self.strategy.manager.positions)
            
            # Emit iteration update with parameters and PnL
            self.iteration_update.emit(
                self.iterations,
                list(zip(self.params, x)),  # Parameter names and values
                float(pnl)  # Current PnL
            )
            
            return -float(pnl)

        except Exception as e:
            print(f"Error in optimization: {str(e)}")
            return float('inf')

    def run(self):
        try:
            x0 = [(b[0] + b[1]) / 2 for b in self.bounds]

            print("\nStarting optimization...")
            print(f"Optimization method: {self.optimizer.__name__}")
            print(f"Parameters being optimized: {self.params}")
            print(f"Parameter bounds: {self.bounds}")
            print("=" * 50)

            if self.optimizer == differential_evolution:
                result = differential_evolution(
                    func=self.objective_function,
                    bounds=self.bounds,
                    maxiter=self.max_iterations,
                    popsize=15,
                    strategy='best1bin',
                    updating='immediate',
                    workers=1,
                    callback=lambda xk, convergence: bool(self.stop_flag),  # Добавляем callback для проверки флага остановки
                    disp=True,
                    init='sobol'
                )
            elif self.optimizer == dual_annealing:
                result = dual_annealing(
                    func=self.objective_function,
                    bounds=self.bounds,
                    maxiter=self.max_iterations,
                    initial_temp=5.0,
                    restart_temp_ratio=2e-5,
                    no_local_search=True,
                    callback=lambda x, f, context: bool(self.stop_flag)  # Добавляем callback
                )
            else:  # Nelder-Mead
                result = minimize(
                    fun=self.objective_function,
                    x0=x0,
                    method='Nelder-Mead',
                    callback=lambda xk: bool(self.stop_flag),  # Добавляем callback
                    options={
                        'maxiter': self.max_iterations,
                        'xatol': 1e-4,
                        'fatol': 1e-4
                    }
                )

            if not hasattr(result, 'x') or not hasattr(result, 'fun'):
                raise ValueError("Optimization failed to produce valid results")

            best_params = result.x
            best_pnl = -result.fun

            # Print optimization results
            print("\nOptimization Results:")
            print("=" * 50)
            print(f"Best PnL: {best_pnl:.2f}")
            print("\nOptimal Parameters:")
            for param_name, value in zip(self.params, best_params):
                param = self.strategy.parameters[param_name]
                print(f"{param.description}: {value:.6f}")
            print("=" * 50)
            print(f"Number of iterations: {self.iterations}")
            print(f"Success: {result.success if hasattr(result, 'success') else True}")
            if hasattr(result, 'message'):
                print(f"Message: {result.message}")
            print("=" * 50)

            optimization_results = [(param, value) for param, value in zip(self.params, best_params)]
            
            # Verify we have valid results before emitting
            if optimization_results:
                self.optimization_complete.emit(optimization_results)
            else:
                raise ValueError("No valid optimization results produced")

        except StopOptimizationException:
            print("\nOptimization stopped by user")
            self.progress_changed.emit(0)  # Сбрасываем прогресс
            self.optimization_complete.emit([])  # Отправляем пустой результат
        except Exception as e:
            print(f"\nOptimization error: {str(e)}")
            self.progress_changed.emit(0)
            self.optimization_complete.emit([])

    def stop(self):
        """Public method to stop the optimization"""
        self.stop_flag = True
        print("Stop flag set to True")


