from typing import Optional
from dataclasses import dataclass
from enum import Enum

class OfferType(Enum):

    MOD = True
    SIGIL = False
    SPECTER = False
    RELIC_PACK = False
    ARCHWEAPON_COMPONENT = True
    CONSUMABLE = False
    DECORATION = False  # sculpture, stencil
    WEAPON = True       # syndicate weapons
    SCENE = True
    SYANDANA = False
    ARMOR_SET = True
    EMOTE = True
    VOSFOR_CACHE = False
    SIMULACRUM = True
    EXILUS_WEAPON_ADAPTER = False


    def __init__(self, tradeable: bool):
        self.tradeable = tradeable

@dataclass
class Offer:
    def __init__(self, offer_type: OfferType, item_slug: str, price: int):
        self.offer_type = offer_type
        self.item_slug = item_slug
        self.standings_price = price

    def __repr__(self):
        return f"type={self.offer_type}, item_slug='{self.item_slug}', price={self.standings_price}"

    def is_tradeable(self):
        return self.offer_type.tradeable