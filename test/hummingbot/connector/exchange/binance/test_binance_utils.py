import unittest

from hummingbot.connector.exchange.binance import binance_utils as utils


class BinanceUtilTestCases(unittest.TestCase):

    def test_spot_testnet_registration_and_credentials(self):
        self.assertIn("binance_testnet", utils.OTHER_DOMAINS)
        self.assertEqual("testnet", utils.OTHER_DOMAINS_PARAMETER["binance_testnet"])
        config = utils.BinanceTestnetConfigMap(
            binance_testnet_api_key="test-key", binance_testnet_api_secret="test-secret")
        self.assertEqual("binance_testnet", config.connector)
        self.assertNotIn("test-secret", repr(config))

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.base_asset = "COINALPHA"
        cls.quote_asset = "HBOT"
        cls.trading_pair = f"{cls.base_asset}-{cls.quote_asset}"
        cls.hb_trading_pair = f"{cls.base_asset}-{cls.quote_asset}"
        cls.ex_trading_pair = f"{cls.base_asset}{cls.quote_asset}"

    def test_is_exchange_information_valid(self):
        invalid_info_1 = {
            "status": "BREAK",
            "permissionSets": [["MARGIN"]],
        }

        self.assertFalse(utils.is_exchange_information_valid(invalid_info_1))

        invalid_info_2 = {
            "status": "BREAK",
            "permissionSets": [["SPOT"]],
        }

        self.assertFalse(utils.is_exchange_information_valid(invalid_info_2))

        invalid_info_3 = {
            "status": "TRADING",
            "permissionSets": [["MARGIN"]],
        }

        self.assertFalse(utils.is_exchange_information_valid(invalid_info_3))

        invalid_info_4 = {
            "status": "TRADING",
            "permissionSets": [["SPOT"]],
        }

        self.assertTrue(utils.is_exchange_information_valid(invalid_info_4))
