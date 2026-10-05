import argparse

from relics.relic import Relic, RelicReward, RelicRefinement
from relics.relic_loader import get_relics_data
from api.market import WarframeMarketClient


class RelicsAnalyzer:

    def __init__(self):
        self.relic_data, self.reward_data = get_relics_data()
        self.rewards_platinum_values: dict[str, int] = {}
        self.relics_platinum_values: dict[str, int] = {}


    def _get_reward_platinum(self, slug):
        plat = self.rewards_platinum_values.get(slug, None)
        if plat:
            return plat
        orders = WarframeMarketClient().get_sell_orders(slug)
        if not orders or len(orders) == 0:
            return None
        

def main():
    parser = argparse.ArgumentParser(description="Analyze relics for profit.")
    parser.add_argument(
        "--save-path", type=str, default=None, help="Path to save the results as CSV."
    )
    args = parser.parse_args()

    analyzer = RelicsAnalyzer()
    analyzer.analyze_relics(save_path=args.save_path)

if __name__ == "__main__":
    main()