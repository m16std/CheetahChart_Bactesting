from lib.api.okx_trade_api import OKXApi
from PyQt5.QtCore import QObject, pyqtSignal 

class TradingSyncManager(QObject):
    log_signal = pyqtSignal(object)

    def __init__(self, api_key=None, api_secret=None, passphrase=None, instrument = None):
        super().__init__()
        self.api = OKXApi(api_key=api_key, api_secret=api_secret, passphrase=passphrase)
        self.instrument = instrument
        
    def compare_positions(self, current_positions, previous_positions):
        """
        Синхронизирует изменения между таблицами позиций и записывает лог в файл.
        
        :param current_positions: DataFrame с текущими позициями
        :param previous_positions: DataFrame с позициями с предыдущего цикла или None, если это первый цикл
        :param exchange_api: Объект API для работы с биржей
        :param log_file_path: Путь к файлу для записи логов
        :return: Обновленная таблица с синхронизацией
        """

        # Первый цикл: если нет предыдущей таблицы
        if not previous_positions:
            for pos in current_positions:
                pos['syncStatus'] = 'unsynced'  # Добавляем поле синхронизации
            return current_positions
        
        # Сравнение текущих и предыдущих позиций
        for current_pos in current_positions:
            # Эта же позиция из предыдущей таблицы
            matching_pos = next((p for p in previous_positions if p['posId'] == current_pos['posId']), None)

            # Скипаем если она была запетущена в прошлом цикле
            if matching_pos and matching_pos['syncStatus'] == 'unsynced':
                continue
            
            # Обрабатываем изменения тейка, стопа, статуса
            if matching_pos:

                if current_pos['status'] == 'closed' and matching_pos['status'] == 'open':
                    # Позиция была закрыта
                    try:
                        self.api.close_position(self.instrument, current_pos['posId'], current_pos['posSide'])
                        current_pos['syncStatus'] = 'synced'
                        message = f"Позиция {current_pos['posId']} успешно закрыта."
                        self.log_signal.emit(message)
                    except Exception as e:
                        current_pos['syncStatus'] = 'unsynced'
                        message = f"Не удалось закрыть позицию {current_pos['posId']}: {str(e)}"
                        self.log_signal.emit(message)
            else:
                if current_pos['status'] == 'open':
                    # Новая позиция
                    try:
                        self.api.open_position(self.instrument, current_pos['qty'], current_pos['posSide'], current_pos['leverage'], current_pos['tpTriggerPx'], current_pos['slTriggerPx'])
                        current_pos['syncStatus'] = 'synced'
                        message = f"Позиция {current_pos['posId']} успешно открыта."
                        self.log_signal.emit(message)
                    except Exception as e:
                        current_pos['syncStatus'] = 'unsynced'
                        message = f"Не удалось открыть позицию {current_pos['posId']}: {str(e)}"
                        self.log_signal.emit(message)

        return current_positions


    def sync_positions(self, positions):
        """ Синхронизация позиций из таблицы с биржей """
        # Получаем открытые позиции на бирже
        self.strategy_positions = positions
        open_positions = self.api.get_open_positions()

        for pos in self.strategy_positions:
            if pos['status'] == 'open' and not pos.get('synced'):
                # Открываем позицию на бирже
                response = self.api.open_position(
                    symbol=pos['symbol'],
                    qty=pos['qty'],
                    posSide=pos['posSide'],
                    leverage=pos.get('leverage', 1),
                    tp=pos.get('tpTriggerPx'),
                    sl=pos.get('slTriggerPx')
                )
                if response:
                    pos['synced'] = True
                    self.log_signal.emit(f"Позиция {pos['posId']} успешно открыта.")
                else:
                    self.log_signal.emit(f"Не удалось открыть позицию {pos['posId']}.")

            if pos['status'] == 'closed' and pos.get('synced'):
                # Закрываем позицию на бирже
                response = self.api.close_position(
                    symbol=pos['symbol'],
                    posId=pos['posId'],
                    posSide=pos['posSide']
                )
                if response:
                    pos['synced'] = False
                    self.log_signal.emit(f"Позиция {pos['posId']} успешно закрыта.")
                else:
                    self.log_signal.emit(f"Не удалось закрыть позицию {pos['posId']}.")
