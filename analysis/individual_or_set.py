
from api.market import WarframeMarketClient


def analyse_set_vs_individual_for(slug: str, verbose: bool = False):
    client = WarframeMarketClient()
    set_slug = slug if slug.endswith("_set") else f"{slug}_set"

    def best_price(orders):
        return orders[0]["platinum"] if orders else None

    set_buy_order_price = best_price(client.get_buy_orders(set_slug))
    set_sell_order_price = best_price(client.get_sell_orders(set_slug))

    set_parts = client.get_item_info(set_slug)["setParts"]

    individual_buy = {
        "known_total": 0,
        "missing": [],
    }
    individual_sell = {
        "known_total": 0,
        "missing": [],
    }

    for part in set_parts:
        part_info = client.get_item_info(part)
        part_slug = part_info["slug"]

        if part_slug.endswith("_set"):
            continue

        count = part_info["quantityInSet"]

        buy_price = best_price(client.get_buy_orders(part))
        sell_price = best_price(client.get_sell_orders(part))

        if buy_price is None:
            individual_buy["missing"].append(part_slug)
        else:
            individual_buy["known_total"] += buy_price * count

        if sell_price is None:
            individual_sell["missing"].append(part_slug)
        else:
            individual_sell["known_total"] += sell_price * count

    for result in (individual_buy, individual_sell):
        result["complete"] = not result["missing"]
        result["price"] = (
            result["known_total"] if result["complete"] else None
        )

    # Buying uses sell orders; selling uses buy orders.
    buying_set_price = set_sell_order_price
    buying_individual_price = individual_sell["price"]

    selling_set_price = set_buy_order_price
    selling_individual_price = individual_buy["price"]

    def compare_prices(set_price, individual_price, known_total):
        if set_price is None:
            return "unknown"

        if individual_price is not None:
            if set_price < individual_price:
                return "set"
            if set_price > individual_price:
                return "individual"
            return "equal"

        # Even with missing components, their nonnegative prices
        # cannot reduce the known subtotal.
        if set_price < known_total:
            return "set"

        return "unknown"

    buying_verdict = compare_prices(
        buying_set_price,
        buying_individual_price,
        individual_sell["known_total"],
    )

    # For selling, a partial component subtotal cannot prove
    # that selling the set is better.
    if selling_set_price is not None and selling_individual_price is not None:
        if selling_set_price > selling_individual_price:
            selling_verdict = "set"
        elif selling_set_price < selling_individual_price:
            selling_verdict = "individual"
        else:
            selling_verdict = "equal"
    elif (
        selling_set_price is not None
        and individual_buy["known_total"] > selling_set_price
    ):
        selling_verdict = "individual"
    else:
        selling_verdict = "unknown"

    result = {
        "set_slug": set_slug,
        "set_buy_order_price": set_buy_order_price,
        "set_sell_order_price": set_sell_order_price,
        "individual_sum_buy_price": individual_buy["price"],
        "individual_sum_sell_price": individual_sell["price"],
        "individual_buy": individual_buy,
        "individual_sell": individual_sell,
        "buying_verdict": buying_verdict,
        "selling_verdict": selling_verdict,
    }

    if verbose:
        print(f"\n{'=' * 50}")
        print(f"Set: {set_slug}")
        print(f"{'=' * 50}")

        print(f"Set Buy Order Price:       {set_buy_order_price}")
        print(f"Set Sell Order Price:      {set_sell_order_price}")
        print(f"Individual Buy Total:      {individual_buy['price']}")
        print(f"Individual Sell Total:     {individual_sell['price']}")

        for label, data in (
            ("Buy orders", individual_buy),
            ("Sell orders", individual_sell),
        ):
            if data["missing"]:
                print(f"\n{label} incomplete:")
                print(f"  Known subtotal: {data['known_total']}")
                print(f"  Missing: {', '.join(data['missing'])}")

        print(f"\n{'=' * 18} VERDICT {'=' * 18}")

        verdict_messages = {
            "set": "Set is better.",
            "individual": "Individual components are better.",
            "equal": "Both options have equal prices.",
            "unknown": "Insufficient market data.",
        }

        print(f"Buying:  {verdict_messages[buying_verdict]}")
        print(f"Selling: {verdict_messages[selling_verdict]}")

    return result


if __name__ == "__main__":
    info_mesa = analyse_set_vs_individual_for(
        "mesa_prime", verbose=True
    )
    print("Info Mesa:", info_mesa)

    info_spira = analyse_set_vs_individual_for(
        "spira_prime", verbose=True
    )
    print("Info Spira:", info_spira)
