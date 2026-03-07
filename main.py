from client import WarframeMarketClient


def main():
    client = WarframeMarketClient()

    item_slug = "soma_prime_set"
    buys, sells = client.get_orders(item_slug)

    print(f"Best buy: {buys[0]['platinum']}p")
    print(f"Best sell: {sells[0]['platinum']}p")



if __name__ == "__main__":
    main()