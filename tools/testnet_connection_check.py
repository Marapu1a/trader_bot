"""Read-only Spot Testnet authentication probe. Never prints credentials."""
import asyncio
import json
import logging
import stat
import sys
import time
from pathlib import Path

import aiohttp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hummingbot.connector.exchange.binance.binance_auth import BinanceAuth
from hummingbot.connector.exchange.binance.binance_endpoints import rest_base, user_ws_url


async def main():
    path = Path('/opt/trader-bot/shared/secrets/binance-testnet.json')
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise RuntimeError('Credential file must have mode 600')
    keys = json.loads(path.read_text())
    if not all(isinstance(keys.get(k), str) and keys[k].strip() for k in ('api_key', 'api_secret')):
        raise RuntimeError('Missing credential fields')
    auth = BinanceAuth(keys['api_key'], keys['api_secret'], time)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=25)) as session:
        async with session.get(rest_base('testnet') + 'v3/account',
                               params=auth.add_auth_to_params({'recvWindow': 10000}),
                               headers=auth.header_for_authentication()) as response:
            data = await response.json()
            print(json.dumps({'check': 'account', 'http_status': response.status,
                              'error_code': data.get('code'), 'can_trade': data.get('canTrade'),
                              'account_type': data.get('accountType'),
                              'balance_asset_count': len(data.get('balances', []))}), flush=True)
            if response.status != 200:
                raise RuntimeError('Account request failed; response details withheld')
        async with session.ws_connect(user_ws_url('testnet'), heartbeat=15) as ws:
            await ws.send_json({'id': 'connection-check', 'method': 'userDataStream.subscribe.signature',
                                'params': auth.generate_ws_subscribe_params()})
            reply = await asyncio.wait_for(ws.receive_json(), timeout=20)
            print(json.dumps({'check': 'private_ws_subscription', 'status': reply.get('status'),
                              'error_code': reply.get('error', {}).get('code')}), flush=True)
            if reply.get('status') != 200:
                raise RuntimeError('Private stream subscription failed')
    print('PASS: account read and private stream subscription; no orders submitted.', flush=True)


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    try:
        asyncio.run(main())
    except Exception as exc:
        print('FAIL:', type(exc).__name__, '(details withheld to protect credentials)', flush=True)
        sys.exit(1)
