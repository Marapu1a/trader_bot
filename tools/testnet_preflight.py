"""Validate a saved controller config before Testnet trading. No network calls."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    import yaml
    from controllers.generic.grid_strike import GridStrikeConfig
    from hummingbot.client.settings import AllConnectorSettings
    from hummingbot.connector.exchange.binance.binance_endpoints import market_ws_url, rest_base, user_ws_url

    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    config = GridStrikeConfig(**yaml.safe_load(args.config.read_text()))
    if config.connector_name != "binance_testnet":
        raise ValueError("This preflight only permits binance_testnet")
    if config.limit_price != 0 or not config.keep_position:
        raise ValueError("Use limit_price=0 and keep_position=true")
    barriers = config.triple_barrier_config
    if any(value is not None for value in (barriers.stop_loss, barriers.time_limit, barriers.trailing_stop)):
        raise ValueError("Stop-loss, time limit and trailing stop must be disabled")
    settings = AllConnectorSettings.get_connector_settings()["binance_testnet"]
    if settings.parent_name != "binance" or settings.domain_parameter != "testnet":
        raise ValueError("Unexpected Testnet connector registration")
    print("Configuration validated; no exchange connection or orders were made.")
    for fn in (rest_base, market_ws_url, user_ws_url):
        print(fn("testnet"))


if __name__ == "__main__":
    main()
