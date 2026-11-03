"""Bounded real BinanceExchange + GridExecutor test, without the CLI/controller layer."""
import asyncio
import json
import logging
import sys
import time
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hummingbot.connector.exchange.binance.binance_exchange import BinanceExchange
from hummingbot.core.clock import Clock, ClockMode
from hummingbot.core.data_type.common import OrderType, PriceType
from hummingbot.core.event.event_logger import EventLogger
from hummingbot.core.event.events import MarketEvent
from hummingbot.strategy_v2.executors.grid_executor.data_types import GridExecutorConfig
from hummingbot.strategy_v2.executors.grid_executor.grid_executor import GridExecutor
from hummingbot.strategy_v2.executors.position_executor.data_types import TripleBarrierConfig

FILL_AND_HOLD = '--fill-and-hold' in sys.argv
PATH = Path('/opt/trader-bot/logs/grid-hold-check-latest.json' if FILL_AND_HOLD else '/opt/trader-bot/logs/grid-check-latest.json')
REPORT = {'orders': [], 'stage': 'initializing', 'fill_and_hold': FILL_AND_HOLD}


def save():
    PATH.write_text(json.dumps(REPORT, indent=2, default=str))


class BoundedStrategy:
    """Routes the executor's strategy interface to the real connector; no mocks."""
    def __init__(self, connector):
        self.connectors = {'binance_testnet': connector}
        self.buy_notional = Decimal(0)
        self.stopping = False

    @property
    def current_timestamp(self):
        return time.time()

    def place(self, side, name, pair, amount, order_type, price, position_action):
        assert name == 'binance_testnet' and pair == 'BTC-USDT'
        assert order_type == OrderType.LIMIT_MAKER or (FILL_AND_HOLD and side == 'buy' and order_type == OrderType.MARKET)
        assert not self.stopping, 'New orders prohibited during stop'
        assert len(REPORT['orders']) < 8, 'Probe submission count reached'
        if side == 'buy':
            assert not FILL_AND_HOLD or not any(o['side'] == 'buy' for o in REPORT['orders']), 'One buy only'
            assert self.buy_notional + amount * price <= 60, 'Probe buy budget reached'
            self.buy_notional += amount * price
        cid = getattr(self.connectors[name], side)(pair, amount, order_type, price)
        REPORT['orders'].append({'client_id': cid, 'side': side, 'amount': str(amount),
                                 'price': str(price), 'type': order_type.name})
        save()
        return cid

    def buy(self, *args):
        return self.place('buy', *args)

    def sell(self, *args):
        return self.place('sell', *args)

    def cancel(self, connector_name, trading_pair, order_id):
        return self.connectors[connector_name].cancel(trading_pair, order_id)

    def get_active_orders(self, connector_name):
        return self.connectors[connector_name].limit_orders


async def main():
    keys = json.loads(Path('/opt/trader-bot/shared/secrets/binance-testnet.json').read_text())
    connector = BinanceExchange(keys['api_key'], keys['api_secret'], trading_pairs=['BTC-USDT'], domain='testnet')
    assert connector.name == 'binance_testnet'
    strategy = BoundedStrategy(connector)
    events = EventLogger()
    for tag in (MarketEvent.BuyOrderCreated, MarketEvent.SellOrderCreated, MarketEvent.OrderFilled,
                MarketEvent.OrderCancelled, MarketEvent.OrderFailure, MarketEvent.BuyOrderCompleted,
                MarketEvent.SellOrderCompleted):
        connector.add_listener(tag, events)
    clock = Clock(ClockMode.REALTIME, 1.0)
    clock.add_iterator(connector)
    executor = None
    with clock:
        clock_task = asyncio.create_task(clock.run())
        try:
            for _ in range(90):
                if connector.ready:
                    break
                await asyncio.sleep(1)
            REPORT['connector_status'] = connector.status_dict
            save()
            assert connector.ready, 'Connector readiness timeout'
            print('Connector ready: order book, trading rules, balances and user stream.', flush=True)
            mid = connector.get_price_by_type('BTC-USDT', PriceType.MidPrice)
            REPORT['balances_before'] = {a: str(connector.get_balance(a)) for a in ('BTC', 'USDT')}
            config = GridExecutorConfig(timestamp=time.time(), connector_name='binance_testnet',
                trading_pair='BTC-USDT', start_price=mid * Decimal('0.998'), end_price=mid * Decimal('1.002'),
                limit_price=Decimal(0), total_amount_quote=Decimal(45), min_order_amount_quote=Decimal(10),
                min_spread_between_orders=Decimal('0.001'), max_open_orders=2, max_orders_per_batch=1,
                order_frequency=3600 if FILL_AND_HOLD else 2, leverage=1, keep_position=True,
                triple_barrier_config=TripleBarrierConfig(take_profit=Decimal('0.01') if FILL_AND_HOLD else Decimal('0.001'),
                    open_order_type=OrderType.MARKET if FILL_AND_HOLD else OrderType.LIMIT_MAKER,
                    take_profit_order_type=OrderType.LIMIT_MAKER))
            executor = GridExecutor(strategy, config, update_interval=1)
            REPORT['config'] = config.model_dump(mode='json')
            REPORT['grid_levels'] = len(executor.grid_levels)
            REPORT['stage'] = 'running'
            save()
            executor.start()
            for _ in range(60):
                await asyncio.sleep(1)
                if FILL_AND_HOLD and any(type(e).__name__ == 'SellOrderCreatedEvent' for e in events.event_log):
                    break
        finally:
            REPORT['stage'] = 'stopping'
            save()
            strategy.stopping = True
            if executor is not None:
                executor.early_stop(keep_position=True)
                try:
                    await asyncio.wait_for(executor.terminated.wait(), 25)
                except asyncio.TimeoutError:
                    executor.stop()
                    REPORT['executor_stop_timeout'] = True
                REPORT['close_type'] = str(executor.close_type)
            # Reconcile only this run's IDs, including connector pending/lost orders.
            await asyncio.sleep(2)
            states = []
            try:
                for item in REPORT['orders']:
                    params = {'symbol': 'BTCUSDT', 'origClientOrderId': item['client_id']}
                    state = await connector._api_get(path_url='/order', params=params, is_auth_required=True)
                    if state['status'] in ('NEW', 'PARTIALLY_FILLED', 'PENDING_CANCEL'):
                        REPORT.setdefault('fallback_cancel_ids', []).append(item['client_id'])
                        save()
                        await connector._api_delete(path_url='/order', params=params, is_auth_required=True)
                        state = await connector._api_get(path_url='/order', params=params, is_auth_required=True)
                    states.append({k: state.get(k) for k in ('clientOrderId', 'orderId', 'status', 'side', 'type', 'executedQty')})
                REPORT['final_orders'] = states
                REPORT['events'] = [{'type': type(e).__name__, 'order_id': getattr(e, 'order_id', None)} for e in events.event_log]
                await connector._update_balances()
                REPORT['balances_after'] = {a: str(connector.get_balance(a)) for a in ('BTC', 'USDT')}
                REPORT['passed'] = bool(states) and all(s['status'] in ('CANCELED', 'FILLED') for s in states)
                if FILL_AND_HOLD:
                    REPORT['passed'] = (REPORT['passed'] and any(s['side'] == 'BUY' and s['status'] == 'FILLED' for s in states)
                        and any(s['side'] == 'SELL' and s['status'] == 'CANCELED' for s in states)
                        and all(Decimal(s['executedQty']) == 0 for s in states if s['side'] == 'SELL')
                        and Decimal(REPORT['balances_after']['BTC']) > Decimal(REPORT['balances_before']['BTC'])
                        and REPORT['close_type'] == 'CloseType.POSITION_HOLD')
                REPORT['stage'] = 'finished'
                save()
                print(json.dumps(REPORT, default=str), flush=True)
                if not REPORT['passed']:
                    raise RuntimeError('Probe acceptance conditions failed')
            finally:
                await connector.stop_network()
                clock_task.cancel()
                await asyncio.gather(clock_task, return_exceptions=True)


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    try:
        asyncio.run(main())
    except Exception as exc:
        REPORT['error_type'] = type(exc).__name__
        save()
        print('FAIL:', type(exc).__name__, '(details withheld; sanitized report saved)', flush=True)
        sys.exit(1)
