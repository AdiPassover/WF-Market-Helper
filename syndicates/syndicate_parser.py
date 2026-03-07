import re
from dataclasses import dataclass

from syndicates.offer import Offer, OfferType
from syndicates.wf_metadata import ARCHWEAPON_PART_TYPES, SYNDICATE_WEAPON_SERIES



def parse_syndicate(syndicate_name) -> list[Offer]:
    file_path = f"syndicates/data/{syndicate_name}.txt"
    offers = []

    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            parts = OfferParts(_get_next_offer(line))
            if parts:
                offers.append(_parse_parts_to_offer(parts))

    return offers

def _get_next_offer(line) -> list[str] | None:
    m = re.search(r"\{\{SynOfferBox\|(.+?)\}\}", line)
    if not m:
        return None
    return [p.strip() for p in m.group(1).split("|")]

def _parse_parts_to_offer(parts) -> Offer:
    offer_type = _parse_offer_type(parts)
    item_slug = _parse_item_slug(parts)
    price = _parse_price(parts)
    return Offer(offer_type, item_slug, price)


@dataclass
class OfferParts:
    png: str
    link: str
    slug: str
    price: str
    rank: str
    def __init__(self, parts):
        self.png = parts[0]
        self.link = parts[1]
        self.slug = parts[2]
        self.price = parts[3]
        self.rank = parts[4]
    def __str__(self):
        return f"png='{self.png}', link='{self.link}', slug='{self.slug}', price='{self.price}', rank='{self.rank}'"


def _parse_offer_type(parts: OfferParts) -> OfferType:
    if parts.png.endswith("Mod.png"):
        return OfferType.MOD
    if parts.link == "Sigils":
        return OfferType.SIGIL
    if parts.png.endswith("Specter.png"):
        return OfferType.SPECTER
    if parts.slug.endswith("Random Void Relics)"):
        return OfferType.RELIC_PACK
    if parts.slug.endswith("Syandana"):
        return OfferType.SYANDANA
    if any(parts.slug.endswith(part) for part in ARCHWEAPON_PART_TYPES):
        return OfferType.ARCHWEAPON_COMPONENT
    if "restore" in parts.slug.lower():
        return OfferType.CONSUMABLE
    if parts.png.endswith("Sculpture.png") or parts.png.endswith("Stencil.png"):
        return OfferType.DECORATION
    if any(series in parts.slug for series in SYNDICATE_WEAPON_SERIES.values()):
        return OfferType.WEAPON
    if parts.png.endswith("Scene.png"):
        return OfferType.SCENE
    if parts.link == "Armor (Cosmetic)":
        return OfferType.ARMOR_SET
    if parts.png.endswith("Emote.png"):
        return OfferType.EMOTE
    if parts.link == "Vosfor":
        return OfferType.VOSFOR_CACHE
    if parts.link == "Simulacrum":
        return OfferType.SIMULACRUM
    if parts.png == "ExilusWeaponAdapter.png":
        return OfferType.EXILUS_WEAPON_ADAPTER
    raise ValueError(f"Unknown offer type for slug '{parts}'")

def _parse_item_slug(parts: OfferParts) -> str:
    name = re.sub(r"\(.*?\)", "", parts.slug)  # remove "(Warframe/Weapon)"
    name = name.replace("'", "").replace("&", "and").strip()
    return name.lower().replace(" ", "_")

def _parse_price(parts: OfferParts) -> int:
    return int(parts.price.replace(",", ""))