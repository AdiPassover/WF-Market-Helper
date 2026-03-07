import requests
import time


class WarframeMarketClient:

    BASE_URL = "https://api.warframe.market/v2"
    RATE_LIMIT_DELAY = 0.35  # ~3 requests/sec

    def __init__(self, platform="pc", crossplay=True, language="en"):
        self.session = requests.Session()

        self.session.headers.update({
            "Platform": platform,
            "Crossplay": str(crossplay).lower(),
            "Language": language
        })

        self._last_request_time = 0

    def get_orders(self, slug, online_only=True) -> tuple[list, list]:
        """Returns a tuple of (buys, sells) for the given item slug sorted by best price."""
        data = self._get(f"/orders/item/{slug}")

        buys = []
        sells = []

        for order in data:
            if online_only and order["user"]["status"] != "ingame":
                continue
            if order["type"] != "sell":
                buys.append(order)
            else:
                sells.append(order)

        buys.sort(key=lambda o: o["platinum"], reverse=True)
        sells.sort(key=lambda o: o["platinum"])

        return buys, sells

    def get_buy_orders(self, slug, online_only=True) -> list:
        """Returns a list of buy orders for the given item slug sorted by best price."""
        return self.get_orders(slug, online_only)[0]
    def get_sell_orders(self, slug, online_only=True) -> list:
        """Returns a list of sell orders for the given item slug sorted by best price."""
        return self.get_orders(slug, online_only)[1]

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)

    def _get(self, endpoint, params=None):
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.get(url, params=params)

        self._last_request_time = time.time()

        response.raise_for_status()

        payload = response.json()

        if payload["error"]:
            raise RuntimeError(payload["error"])

        return payload["data"]


# Example usage
if __name__ == "__main__":
    client = WarframeMarketClient()
    buys, sells = client.get_orders("soma_prime_set")
    print(f"Best buy: {buys[0]['platinum']}p")
    print(f"Best sell: {sells[0]['platinum']}p")