from typing import Optional

from arcanes.arcanes_data import get_arcane_dissolution, get_arcane_collections, COUNT_FOR_RANK
from api.market import WarframeMarketClient


class ArcanesAnalyzer:

    ARCANES_PER_COLLECTION = 3
    VOSFOR_PER_COLLECTION = 200

    def __init__(self, loading_bar: bool = True, save_path: Optional[str] = None, load_prices: Optional[str] = None):
        self.arcanes_dissolution = get_arcane_dissolution()
        self.arcanes_collections = get_arcane_collections()
        if not load_prices:
            self.arcane_prices = self._get_prices(loading_bar=loading_bar, save_path=save_path)
        else:
            self.arcane_prices = {}
            with open(load_prices, "r", encoding="utf-8") as f:
                for line in f:
                    name, price = line.strip().split(",")
                    self.arcane_prices[name] = float(price) if price != "None" else None


    def _get_prices(self, loading_bar: bool = True, save_path: Optional[str] = None) -> dict[str, int]:
        arcane_names = list(self.arcanes_dissolution.keys())
        prices = {}
        total = len(arcane_names)

        for i, name in enumerate(arcane_names, 1):
            slug = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
            orders = WarframeMarketClient().get_sell_orders(slug)
            if orders and len(orders) > 0:
                prices[name]  = min(float(order["platinum"]) / COUNT_FOR_RANK[order["rank"]] for order in orders)
            else:
                prices[name] = None

            if loading_bar:
                self._print_progress(i, total)

        if loading_bar:
            print()  # Ensure the progress bar ends with a newline

        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                for name, price in prices.items():
                    f.write(f"{name},{price}\n")

        return prices

    @staticmethod
    def _print_progress(current, total, width=30):
        progress = current / total if total else 1
        filled = int(width * progress)
        bar = "#" * filled + "-" * (width - filled)
        percent = int(progress * 100)
        line = f"[{bar}] {percent:3d}% ({current}/{total})"
        print(f"\r\033[K{line}", end="", flush=True)

    def get_plat_vosfor_ratio(self, include_collections: bool = True, save_path: Optional[str] = None) -> dict[str, Optional[float]]:
        ratio_dict = {}
        for arcane, price in self.arcane_prices.items():
            dissolution = self.arcanes_dissolution.get(arcane)
            if dissolution is not None and price is not None:
                ratio = price / dissolution  # larger ratio means more plat per vosfor
                ratio_dict[arcane] = ratio
            else:
                ratio_dict[arcane] = None

        if include_collections:
            collections_expectancy = self.get_collections_plat_expectancy()
            for collection, expectancy in collections_expectancy.items():
                ratio_dict[f"{collection} Collection"] = expectancy / self.VOSFOR_PER_COLLECTION

        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                for arcane, ratio in ratio_dict.items():
                    f.write(f"{arcane},{ratio}\n")

        return ratio_dict

    def get_collections_plat_expectancy(self, save_path: Optional[str] = None) -> dict[str, float]:
        collections_expectancy = {}
        for collection, arcanes in self.arcanes_collections.items():
            total_expectancy = 0
            for arcane, probability in arcanes.items():
                price = self.arcane_prices.get(arcane)
                if price is not None:
                    total_expectancy += price * probability
            collections_expectancy[collection] = total_expectancy * self.ARCANES_PER_COLLECTION

        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                for collection, expectancy in collections_expectancy.items():
                    f.write(f"{collection},{expectancy}\n")

        return collections_expectancy

    def get_collections_dissolution_expectancy(self, save_path: Optional[str] = None) -> dict[str, float]:
        collections_expectancy = {}
        for collection, arcanes in self.arcanes_collections.items():
            total_expectancy = 0
            for arcane, probability in arcanes.items():
                dissolution = self.arcanes_dissolution.get(arcane)
                if dissolution is not None:
                    total_expectancy += dissolution * probability
            collections_expectancy[collection] = total_expectancy * self.ARCANES_PER_COLLECTION

        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                for collection, expectancy in collections_expectancy.items():
                    f.write(f"{collection},{expectancy}\n")

        return collections_expectancy


if __name__ == "__main__":
    analyzer = ArcanesAnalyzer(
        save_path="C:\\Users\\adipe\\PycharmProjects\\Warframe-Market-Tool\\saved_analysis_results\\arcane_prices.csv"
        , load_prices="C:\\Users\\adipe\\PycharmProjects\\Warframe-Market-Tool\\saved_analysis_results\\arcane_prices.csv"
    )
    plat_vosfor_ratio = analyzer.get_plat_vosfor_ratio(save_path="C:\\Users\\adipe\\PycharmProjects\\Warframe-Market-Tool\\saved_analysis_results\\arcane_plat_vosfor_ratio.csv")
    plat_expectancy = analyzer.get_collections_plat_expectancy(save_path="C:\\Users\\adipe\\PycharmProjects\\Warframe-Market-Tool\\saved_analysis_results\\arcane_collections_plat_expectancy.csv")
    dissolution_expectancy = analyzer.get_collections_dissolution_expectancy(save_path="C:\\Users\\adipe\\PycharmProjects\\Warframe-Market-Tool\\saved_analysis_results\\arcane_collections_dissolution_expectancy.csv")

    print("Arcane Platinum Prices:")
    print(analyzer.arcane_prices)
    print("\n============================================================\nArcane Platinum to Dissolution Ratio:")
    print(plat_vosfor_ratio)
    print("\n============================================================\nArcane Collections Platinum Expectancy:")
    print(plat_expectancy)
    print("\n============================================================\nArcane Collections Dissolution Expectancy:")
    print(dissolution_expectancy)

