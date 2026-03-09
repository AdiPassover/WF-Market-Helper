import requests


class WarframeDropClient:
    _instance = None
    BASE_URL = "https://drops.warframestat.us/data/all.json"

    def __new__(self, session: requests.Session | None = None):
        if self._instance is None:
            self._instance = super(WarframeDropClient, self).__new__(self)
            self._instance.session = session or requests.Session()
            self._instance._data = None
        return self._instance

    def fetch_all(self, force: bool = False) -> dict:
        """
        Fetch the full drop dataset.
        Cached after the first request unless force=True.
        """
        if self._data is None or force:
            resp = self.session.get(self.BASE_URL, timeout=30)
            resp.raise_for_status()
            self._data = resp.json()
        return self._data

    def get_category(self, name: str):
        """
        Return a top-level category from the dataset.
        Example: 'blueprintLocations', 'modLocations'
        """
        data = self.fetch_all()
        return data.get(name)

    def search_item(self, item_name: str):
        """
        Search for entries mentioning a specific item.
        """
        data = self.fetch_all()
        results = []

        for category, value in data.items():
            if isinstance(value, list):
                for entry in value:
                    if item_name.lower() in str(entry).lower():
                        results.append((category, entry))

        return results