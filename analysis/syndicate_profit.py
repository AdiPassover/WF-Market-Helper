import csv
from typing import Callable, Optional
import argparse

from api.market import WarframeMarketClient
from syndicates.syndicate_parser import parse_syndicate


def profit_from_syndicate(
    syndicate_name,
    loading_bar: bool = True,
    save_path: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> list[tuple[str, int, int]]:
    """
    Returns a list of tuples:
    (slug, standings_price, platinum_price)

    Sorted by standings/platinum (lower = better).

    progress_callback, if given, is called with (current, total) instead of
    printing the console loading bar.
    """

    client = WarframeMarketClient()
    offers = parse_syndicate(syndicate_name)

    tradable_offers = [o for o in offers if o.is_tradeable()]
    total = len(tradable_offers)

    profits = []
    report_progress = progress_callback or (_print_progress_bar if loading_bar else None)

    for i, offer in enumerate(tradable_offers, 1):

        if report_progress:
            report_progress(i - 1, total)

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

    if report_progress:
        report_progress(total, total)
    if report_progress is _print_progress_bar:
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


def main():
    parser = argparse.ArgumentParser(
        description="Calculate profits from syndicate offers in Warframe."
    )
    parser.add_argument(
        "--syndicates",
        nargs="+",
        help="List of syndicate names to calculate profits for. If not provided, all syndicates will be processed.",
    )
    parser.add_argument(
        "--no-loading-bar",
        action="store_true",
        help="Disable the loading bar display.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save the output to CSV files.",
    )

    args = parser.parse_args()

    profit_of_syndicates(
        syndicate_names=args.syndicates,
        loading_bar=not args.no_loading_bar,
        save_output=not args.no_save
    )

if __name__ == "__main__":
    main()