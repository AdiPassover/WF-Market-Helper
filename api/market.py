import requests
import time


class WarframeMarketClient:
    _instance = None

    BASE_URL = "https://api.warframe.market/v2"
    RATE_LIMIT_DELAY = 0.35  # ~3 requests/sec

    def __new__(self, platform="pc", crossplay=True, language="en"):
        if self._instance is None:
            self._instance = super(WarframeMarketClient, self).__new__(self)
            self._instance.session = requests.Session()
            self._instance.session.headers.update({
                "User-Agent": "Warframe-Market-Tool/1.0 (personal syndicate profit analysis)",
                "Accept": "application/json",
                "Platform": platform,
                "Crossplay": str(crossplay).lower(),
                "Language": language
            })
            self._instance._last_request_time = 0
        return self._instance

    def get_item_info(self, slug) -> dict:
        """Returns detailed information about an item given its slug."""
        return self._get(f"/items/{slug}")

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
        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(3):
            self._rate_limit()
            response = self.session.get(url, params=params)
            self._last_request_time = time.time()

            if response.status_code not in (403, 429):
                break
            time.sleep(2 ** (attempt + 1))  # back off instead of hammering

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