from dataclasses import dataclass
from enum import Enum
from math import isclose


class RewardRarity(Enum):
    COMMON = 0
    UNCOMMON = 1
    RARE = 2

    @staticmethod
    def from_chance(chance: float, refinement: 'RelicRefinement') -> 'RewardRarity':
        for rarity, prob in refinement.get_probabilities().items():
            if isclose(chance, prob * 100):
                return RewardRarity(rarity)
    @staticmethod
    def from_string(s: str) -> 'RewardRarity':
        s = s.lower()
        for rarity in RewardRarity:
            if rarity.name.lower() == s:
                return rarity

class RelicRefinement(Enum):
    INTACT = {RewardRarity.COMMON: 0.2533, RewardRarity.UNCOMMON: 0.11, RewardRarity.RARE: 0.02}, 0
    EXCEPTIONAL = {RewardRarity.COMMON: 0.2333, RewardRarity.UNCOMMON: 0.13, RewardRarity.RARE: 0.04}, 25
    FLAWLESS = {RewardRarity.COMMON: 0.20, RewardRarity.UNCOMMON: 0.17, RewardRarity.RARE: 0.06}, 50
    RADIANT = {RewardRarity.COMMON: 0.1667, RewardRarity.UNCOMMON: 0.20, RewardRarity.RARE: 0.10}, 100

    def get_probabilities(self) -> dict[RewardRarity, float]:
        return self.value[0]
    def get_probability(self, rarity: RewardRarity) -> float:
        return self.get_probabilities()[rarity]
    def get_traces_cost(self) -> int:
        return self.value[1]

class RelicTier(Enum):
    LITH = 0
    MESO = 1
    NEO = 2
    AXI = 3

    @staticmethod
    def from_string(s: str) -> 'RelicTier':
        s = s.lower()
        if s == 'lith':
            return RelicTier.LITH
        elif s == 'meso':
            return RelicTier.MESO
        elif s == 'neo':
            return RelicTier.NEO
        elif s == 'axi':
            return RelicTier.AXI
        else:
            raise ValueError(f'Unknown relic tier: {s}')


@dataclass
class RelicReward:
    slug: str
    rarity: RewardRarity
    ducats: int | None

@dataclass
class Relic:
    name: str
    tier: RelicTier
    rewards: list[RelicReward]