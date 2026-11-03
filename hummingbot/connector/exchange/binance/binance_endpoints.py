"""Explicit routing for Binance Spot production and Spot Testnet."""


def rest_base(domain: str) -> str:
    if domain == "testnet":
        return "https://testnet.binance.vision/api/"
    if domain not in {"com", "us"}:
        raise ValueError(f"Unsupported Binance Spot domain: {domain}")
    return f"https://api.binance.{domain}/api/"


def market_ws_url(domain: str) -> str:
    if domain == "testnet":
        return "wss://stream.testnet.binance.vision/ws"
    rest_base(domain)
    return f"wss://stream.binance.{domain}:9443/ws"


def user_ws_url(domain: str) -> str:
    if domain == "testnet":
        return "wss://ws-api.testnet.binance.vision/ws-api/v3"
    rest_base(domain)
    return f"wss://ws-api.binance.{domain}:443/ws-api/v3"
