from client import WarframeMarketClient
from syndicates.syndicate_parser import parse_syndicate
from syndicates.wf_metadata import SYNDICATE_WEAPON_SERIES


def main():
    # client = WarframeMarketClient()
    #
    # item_slug = "soma_prime_set"
    # buys, sells = client.get_orders(item_slug)
    #
    # print(f"Best buy: {buys[0]['platinum']}p")
    # print(f"Best sell: {sells[0]['platinum']}p")

    for syndicate_name in SYNDICATE_WEAPON_SERIES:
        print(f"{syndicate_name}:")
        offers = parse_syndicate(syndicate_name)
        for offer in offers:
            print(f"\t{offer}")




if __name__ == "__main__":
    main()