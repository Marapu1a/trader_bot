#!/usr/bin/env bash
# Run as trader-bot inside a resource-limited systemd unit. Never starts trading.
set -euo pipefail
cd /opt/trader-bot/releases/testnet-20261103
export PATH=/opt/trader-bot/env/bin:$PATH
export HBOT_BUILD_JOBS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python - <<'PY'
import ast
from pathlib import Path
tree = ast.parse(Path('setup.py').read_text())
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'install_requires' for t in node.targets):
        requirements = ast.literal_eval(node.value)
        requirements += ['aiohttp<3.14', 'pytest', 'pytest-asyncio', 'pytest-timeout']
        Path('/opt/trader-bot/build-requirements.txt').write_text('\n'.join(requirements) + '\n')
        break
else:
    raise RuntimeError('Cannot find upstream dependencies')
PY
python -m pip install -r /opt/trader-bot/build-requirements.txt
python setup.py build_ext --inplace
python - <<'PY'
import site
from pathlib import Path
Path(site.getsitepackages()[0], 'hummingbot-source.pth').write_text(str(Path.cwd()) + '\n')
PY
python -m pip freeze > /opt/trader-bot/logs/python-freeze.txt
python bin/hbot --help > /opt/trader-bot/logs/hbot-help.txt
python -m pytest test/hummingbot/connector/exchange/binance/test_binance_web_utils.py test/hummingbot/connector/exchange/binance/test_binance_utils.py test/hummingbot/connector/exchange/binance/test_binance_user_stream_data_source.py test/hummingbot/strategy_v2/executors/grid_executor/test_grid_executor.py -q
