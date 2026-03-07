import csv
from typing import Optional

from market.client import WarframeMarketClient
from syndicates.syndicate_parser import parse_syndicate


def profit_from_syndicate(
    syndicate_name,
    loading_bar: bool = True,
    save_path: Optional[str] = None
) -> list[tuple[str, int, int]]:
    """
    Returns a list of tuples:
    (slug, standings_price, platinum_price)

    Sorted by standings/platinum (lower = better).
    """

    client = WarframeMarketClient()
    offers = parse_syndicate(syndicate_name)

    tradable_offers = [o for o in offers if o.is_tradeable()]
    total = len(tradable_offers)

    profits = []

    for i, offer in enumerate(tradable_offers, 1):

        if loading_bar:
            _print_progress_bar(i - 1, total)

        try:
            buys = client.get_buy_orders(offer.item_slug)
        except Exception as e:
            print(f"\nError fetching buy orders for {offer.item_slug}: {e}")
            continue
        if not buys or len(buys) == 0:
            continue

        best_buy = buys[0]

        profits.append(
            (offer.item_slug, offer.standings_price, best_buy["platinum"])
        )

    profits.sort(key=lambda x: float(x[1]) / x[2])

    if loading_bar:
        _print_progress_bar(total, total)
        print()

    if save_path:
        _save_csv(save_path, profits)

    return profits

def _print_progress_bar(current, total, width=20):

    progress = current / total if total else 1

    filled = int(width * progress)
    empty = width - filled

    bar = "#" * filled + "-" * empty
    percent = int(progress * 100)

    line = f"[{bar}] {percent:3d}% ({current}/{total})"

    print(f"\r\033[K{line}", end="", flush=True)

def _save_csv(path, profits):

    with open(path, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow([
            "item_slug",
            "standing_cost",
            "platinum_price",
            "platinum_per_1k_standing"
        ])

        for slug, standing, plat in profits:

            ratio = plat / (float(standing) / 1000)

            writer.writerow([
                slug,
                standing,
                plat,
                round(ratio, 3)
            ])




def profit_of_syndicates(syndicate_names: Optional[list[str]] = None, loading_bar: bool = True, save_output: bool = True):
    from syndicates.wf_metadata import SYNDICATE_NAMES
    if not syndicate_names:
            syndicate_names = SYNDICATE_NAMES
    for syndicate_name in syndicate_names:
        print(f"Profits for {syndicate_name}:")
        profits = profit_from_syndicate(syndicate_name, loading_bar=loading_bar,
                                        save_path=f"profits_{syndicate_name}.csv" if save_output else None)
        for slug, standings, platinum in profits:
            print(
                f"{slug}: {standings} standings for {platinum} platinum (profit per 1K standing={platinum / float(standings / 1000):.2f})")
        print()