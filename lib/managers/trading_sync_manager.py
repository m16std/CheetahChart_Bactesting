class TradingSyncManager:
    def __init__(self, api, strategy_positions):
        self.api = api
        self.strategy_positions = strategy_positions
        self.log = []

    def sync_positions(self):
        """ Синхронизация позиций из таблицы с биржей """
        # Получаем открытые позиции на бирже
        open_positions = self.api.fetch_positions()

        for pos in self.strategy_positions:
            if pos['status'] == 'open' and not pos.get('synced'):
                # Открываем позицию на бирже
                response = self.api.open_position(
                    symbol=pos['symbol'],
                    side=pos['posSide'],
                    qty=pos['qty'],
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
                    pos_id=pos['posId']
                )
                if response:
                    pos['synced'] = False
                    self.log.append(f"Position {pos['posId']} closed on exchange.")
                else:
                    self.log.append(f"Failed to close position {pos['posId']}.")
