"""Endpoint isolation checks without installing the trading engine."""
import importlib.util
from pathlib import Path
import unittest
from urllib.parse import urlparse

MODULE = Path(__file__).resolve().parents[1] / "hummingbot/connector/exchange/binance/binance_endpoints.py"
spec = importlib.util.spec_from_file_location("binance_endpoints", MODULE)
endpoints = importlib.util.module_from_spec(spec)
spec.loader.exec_module(endpoints)


class EndpointIsolationTests(unittest.TestCase):
    def test_all_testnet_channels_are_isolated(self):
        for fn in (endpoints.rest_base, endpoints.market_ws_url, endpoints.user_ws_url):
            with self.subTest(channel=fn.__name__):
                host = urlparse(fn("testnet")).hostname
                self.assertTrue(host == "testnet.binance.vision" or host.endswith(".testnet.binance.vision"))

    def test_market_stream_is_raw(self):
        self.assertEqual("/ws", urlparse(endpoints.market_ws_url("testnet")).path)

    def test_private_ws_is_signature_api(self):
        self.assertEqual("/ws-api/v3", urlparse(endpoints.user_ws_url("testnet")).path)

    def test_unknown_domain_does_not_fall_back_to_live(self):
        for fn in (endpoints.rest_base, endpoints.market_ws_url, endpoints.user_ws_url):
            with self.assertRaises(ValueError):
                fn("testnett")

    def test_existing_domains_are_preserved(self):
        for domain in ("com", "us"):
            self.assertEqual(f"https://api.binance.{domain}/api/", endpoints.rest_base(domain))
            self.assertEqual(f"wss://stream.binance.{domain}:9443/ws", endpoints.market_ws_url(domain))


if __name__ == "__main__":
    unittest.main()
