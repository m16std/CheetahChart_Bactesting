from lib.api.okx_trade_api import OKXApi

class TradingSyncManager:
    def __init__(self, api_key=None, api_secret=None, passphrase=None):
        # Initialize with default or provided API credentials
        self.api = OKXApi(api_key=api_key, api_secret=api_secret, passphrase=passphrase)
        self.log = []

        
    def compare_positions(self, current_positions, previous_positions):
        log = []
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
                pos['syncStatus'] = 'synced'  # Добавляем поле синхронизации
            return current_positions
        
        # Сравнение текущих и предыдущих позиций
        for current_pos in current_positions:
            matching_pos = next((p for p in previous_positions if p['posId'] == current_pos['posId']), None)

            # Игнорируем не синхронизированные позиции из предыдущей таблицы
            if matching_pos and matching_pos['syncStatus'] == 'unsynced':
                continue
            
            # Обрабатываем изменения тейка, стопа, статуса
            if matching_pos:
                changes = []

                if current_pos['status'] != matching_pos['status']:
                    changes.append(f"status changed to {current_pos['status']}")
                
                if current_pos['tpTriggerPx'] != matching_pos['tpTriggerPx']:
                    changes.append('take profit changed')

                if current_pos['slTriggerPx'] != matching_pos['slTriggerPx']:
                    changes.append('stop loss changed')

                # Новая обработка: изменение количества
                if current_pos['qty'] != matching_pos['qty']:
                    changes.append(f"quantity changed to {current_pos['qty']}")

                # Новая обработка: изменение цены открытия
                if current_pos['openPrice'] != matching_pos['openPrice']:
                    changes.append(f"open price changed to {current_pos['openPrice']}")

                if changes:
                    try:
                        # Пытаемся синхронизировать с биржей
                        #self.api.sync_position(current_pos)
                        current_pos['syncStatus'] = 'synced'
                        message = f"Position {current_pos['posId']} synced: {', '.join(changes)}"
                        self.log_message(message)
                        self.log_window.update_log(message)
                    except Exception as e:
                        current_pos['syncStatus'] = 'unsynced'
                        message = f"Error syncing position {current_pos['posId']}: {str(e)}"
                        self.log_message(message)
                        self.log_window.update_log(message)
                else:
                    current_pos['syncStatus'] = 'synced'
            else:
                if current_pos['status'] == 'open':
                    # Новая позиция
                    try:
                        #self.api.open_position(current_pos)
                        current_pos['syncStatus'] = 'synced'
                        message = f"New position {current_pos['posId']} opened"
                        self.log_message(message)
                        self.log_window.update_log(message)
                    except Exception as e:
                        current_pos['syncStatus'] = 'unsynced'
                        message = f"Error opening new position {current_pos['posId']}: {str(e)}"
                        self.log_message(message)
                        self.log_window.update_log(message)
        
        print(log)
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
                    self.log.append(f"Position {pos['posId']} opened on exchange.")
                else:
                    self.log.append(f"Failed to open position {pos['posId']}.")

            if pos['status'] == 'closed' and pos.get('synced'):
                # Закрываем позицию на бирже
                response = self.api.close_position(
                    symbol=pos['symbol'],
                    posId=pos['posId'],
                    posSide=pos['posSide']
                )
                if response:
                    pos['synced'] = False
                    self.log.append(f"Position {pos['posId']} closed on exchange.")
                else:
                    self.log.append(f"Failed to close position {pos['posId']}.")
