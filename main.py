import time
from relics.relic_loader import get_relics_data


def main():

    start_time = time.time()
    relics, rewards = get_relics_data()
    print(relics)
    print(rewards)
    end_time = time.time()
    print(f"Relics analysis took {end_time - start_time:.2f} seconds")






if __name__ == "__main__":
    main()