import os
import csv
from relics.relic import Relic, RelicReward, RelicRefinement, RelicTier, RewardRarity
from api.market import WarframeMarketClient
from api.drops import WarframeDropClient


DEFAULT_RELICS_CSV_PATH = "relics/data/relics.csv"
DEFAULT_REWARDS_CSV_PATH = "relics/data/rewards.csv"

def get_relics_data(force_update: bool = False, relics_csv_path: str = DEFAULT_RELICS_CSV_PATH,
                    rewards_csv_path: str = DEFAULT_REWARDS_CSV_PATH) -> tuple[dict[str, Relic], dict[str, RelicReward]]:
    if os.path.exists(relics_csv_path) and os.path.exists(rewards_csv_path) and not force_update:
        print("Loading relic data from CSV cache...")
        return _parse_csvs(relics_csv_path, rewards_csv_path) # TODO add a case where we can use the rewards for fetching relics

    print("Fetching relic data from API...")
    relics, rewards = _fetch_relics_data()
    _save_relics_to_csv(relics, relics_csv_path)
    _save_rewards_to_csv(rewards, rewards_csv_path)
    return relics, rewards



def _parse_csvs(relics_path: str, rewards_path: str) -> tuple[dict[str, Relic], dict[str, RelicReward]]:
    rewards = _parse_csv_rewards(rewards_path)
    relics = {}
    with open(relics_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["relic_name"]
            tier = RelicTier.from_string(row["tier"])
            reward_slugs = row["reward_slugs"].split(";")
            relic_rewards = [rewards[s] for s in reward_slugs if s in rewards]
            relics[name] = Relic(name, tier, relic_rewards)
    return relics, rewards

def _parse_csv_rewards(file_path: str) -> dict[str, RelicReward]:
    rewards = {}
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            slug = row["slug"]
            rarity = RewardRarity.from_string(row["rarity"])
            ducats = row["ducats"]
            ducats = int(ducats) if ducats else None
            rewards[slug] = RelicReward(slug, rarity, ducats)
    return rewards

def _save_relics_to_csv(relics: dict[str, Relic], path: str, loading_bar: bool=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    total = len(relics)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["relic_name", "tier", "reward_slugs"])
        for i, relic in enumerate(relics.values(), 1):
            slugs = ";".join(r.slug for r in relic.rewards)
            writer.writerow([
                relic.name,
                relic.tier.name,
                slugs
            ])
            if loading_bar:
                _print_progress(i, total)
    if loading_bar:
        print()

def _save_rewards_to_csv(rewards: dict[str, RelicReward], path: str, loading_bar: bool=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    total = len(rewards)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["slug", "rarity", "ducats"])
        for i, reward in enumerate(rewards.values(), 1):
            writer.writerow([
                reward.slug,
                reward.rarity.name,
                reward.ducats if reward.ducats is not None else ""
            ])
            if loading_bar:
                _print_progress(i, total)
    if loading_bar:
        print()


def _fetch_relics_data(loading_bar: bool = True) -> tuple[dict[str, Relic], dict[str, RelicReward]]:
    raw_data = WarframeDropClient().get_category("relics")
    relics_data = {}
    rewards_data = {}

    total = len(raw_data)
    for i, raw_relic in enumerate(raw_data, 1):
        if raw_relic["tier"] not in ["Lith", "Meso", "Neo", "Axi"]:
            continue
        name = f"{raw_relic['tier']} {raw_relic['relicName']} relic"
        if name in relics_data or not raw_relic['rewards'] or raw_relic['state'] != "Intact":
            continue

        rewards = []
        for reward_data in raw_relic['rewards']:
            slug = reward_data['itemName'].strip().lower().replace(" ", "_").replace("&", "and")
            if slug in rewards_data:
                rewards.append(rewards_data[slug])
                continue
            rarity = RewardRarity.from_chance(reward_data['chance'], RelicRefinement.INTACT)
            ducats = _get_ducats_from_market(slug)
            reward = RelicReward(slug, rarity, ducats)
            rewards.append(reward)
            rewards_data[slug] = reward

        relic = Relic(name, RelicTier.from_string(raw_relic['tier']), rewards)
        relics_data[name] = relic
        if loading_bar:
            _print_progress(i, total)
    if loading_bar:
        print()

    return relics_data, rewards_data

def _print_progress(current, total, width=30):
    progress = current / total if total else 1
    filled = int(width * progress)
    bar = "#" * filled + "-" * (width - filled)
    percent = int(progress * 100)
    line = f"[{bar}] {percent:3d}% ({current}/{total})"
    print(f"\r\033[K{line}", end="", flush=True)


def _get_ducats_from_market(slug: str) -> int | None:
    if "forma_blueprint" in slug:
        return 0
    try:
        market_data = WarframeMarketClient().get_item_info(slug)
    except Exception as e:
        print(f"\nError fetching market data for {slug}: {e}")
        return None
    if not market_data:
        return None
    return market_data.get("ducats", None)