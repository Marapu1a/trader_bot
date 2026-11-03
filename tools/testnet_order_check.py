"""One small Spot Testnet maker order, private events, and cancellation."""
import asyncio
import json
import logging
import sys
import time
import uuid
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path

import aiohttp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hummingbot.connector.exchange.binance.binance_auth import BinanceAuth
from hummingbot.connector.exchange.binance.binance_endpoints import rest_base, user_ws_url

REPORT = Path('/opt/trader-bot/logs/order-check-latest.json')


async def main():
    keys = json.loads(Path('/opt/trader-bot/shared/secrets/binance-testnet.json').read_text())
    auth = BinanceAuth(keys['api_key'], keys['api_secret'], time)
    cid = 'probe-' + uuid.uuid4().hex[:24]
    report = {'client_order_id': cid, 'symbol': 'BTCUSDT', 'events': []}
    def save():
        REPORT.write_text(json.dumps(report, indent=2))
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        async def request(method, endpoint, params, signed=False):
            params = auth.add_auth_to_params(dict(params, recvWindow=10000)) if signed else params
            async with session.request(method, rest_base('testnet') + 'v3/' + endpoint,
                                       params=params, headers=auth.header_for_authentication() if signed else {}) as r:
                data = await r.json()
                if r.status != 200:
                    raise RuntimeError(f'API HTTP {r.status}, code {data.get("code")}')
                return data
        info = await request('GET', 'exchangeInfo', {'symbol': 'BTCUSDT'})
        symbol = info['symbols'][0]
        assert symbol['status'] == 'TRADING' and 'LIMIT_MAKER' in symbol['orderTypes']
        filters = {f['filterType']: f for f in symbol['filters']}
        book = await request('GET', 'ticker/bookTicker', {'symbol': 'BTCUSDT'})
        tick = Decimal(filters['PRICE_FILTER']['tickSize'])
        step = Decimal(filters['LOT_SIZE']['stepSize'])
        price = (Decimal(book['bidPrice']) * Decimal('0.97') / tick).to_integral_value(rounding=ROUND_FLOOR) * tick
        minimum = Decimal(filters.get('NOTIONAL', filters.get('MIN_NOTIONAL', {})).get('minNotional', '5'))
        target = max(Decimal('10'), minimum * Decimal('1.1'))
        qty = max(Decimal(filters['LOT_SIZE']['minQty']), (target / price / step).to_integral_value(rounding=ROUND_CEILING) * step)
        assert 0 < price * qty <= 25, 'Probe budget exceeds 25 test USDT'
        report.update(price=str(price), quantity=str(qty), notional=str(price * qty))
        save()
        async with session.ws_connect(user_ws_url('testnet'), heartbeat=15) as ws:
            await ws.send_json({'id': 'probe-sub', 'method': 'userDataStream.subscribe.signature',
                                'params': auth.generate_ws_subscribe_params()})
            reply = await asyncio.wait_for(ws.receive_json(), 20)
            assert reply.get('status') == 200, 'Subscription rejected'
            async def event(status):
                async def read():
                    while True:
                        msg = await ws.receive_json()
                        e = msg.get('event', msg)
                        if e.get('e') == 'executionReport' and (e.get('c') == cid or e.get('C') == cid):
                            report['events'].append({k: e.get(k) for k in ('i', 'x', 'X', 'z')})
                            save()
                            if e.get('X') == status:
                                return
                await asyncio.wait_for(read(), 15)
            try:
                # Persist the ID before the single submission; never retry POST on timeout.
                report['submission_attempted'] = True
                save()
                order = await request('POST', 'order', {'symbol': 'BTCUSDT', 'side': 'BUY',
                    'type': 'LIMIT_MAKER', 'quantity': str(qty), 'price': str(price),
                    'newClientOrderId': cid, 'newOrderRespType': 'RESULT'}, True)
                report['order_id'] = order['orderId']
                report['create_status'] = order['status']
                save()
                await event('NEW')
                checked = await request('GET', 'order', {'symbol': 'BTCUSDT', 'origClientOrderId': cid}, True)
                report['query_status'] = checked['status']
                save()
            finally:
                # Only cancel this probe, including an ambiguous POST timeout.
                for attempt in range(3):
                    try:
                        cancelled = await request('DELETE', 'order', {'symbol': 'BTCUSDT', 'origClientOrderId': cid}, True)
                        report['cancel_status'] = cancelled['status']
                        save()
                        break
                    except Exception:
                        if attempt == 2:
                            report['cleanup_requires_reconciliation'] = True
                            save()
                            raise
                        await asyncio.sleep(1)
            await event('CANCELED')
            final = await request('GET', 'order', {'symbol': 'BTCUSDT', 'origClientOrderId': cid}, True)
            report['final_status'] = final['status']
            report['executed_qty'] = final['executedQty']
            opened = await request('GET', 'openOrders', {'symbol': 'BTCUSDT'}, True)
            report['probe_still_open'] = any(o['clientOrderId'] == cid for o in opened)
            report['passed'] = final['status'] == 'CANCELED' and Decimal(final['executedQty']) == 0 and not report['probe_still_open']
            save()
            print(json.dumps(report), flush=True)
            assert report['passed'], 'Unexpected terminal state'


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    try:
        asyncio.run(main())
    except Exception as exc:
        print('FAIL:', type(exc).__name__, '(details withheld; inspect sanitized report)', flush=True)
        sys.exit(1)
