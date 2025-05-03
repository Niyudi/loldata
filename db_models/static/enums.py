from enum import auto, Enum
from functools import total_ordering

@total_ordering
class Ranks(Enum):
    UNRANKED = 0
    IRONIV = 1
    IRONIII = 2
    IRONII = 3
    IRONI = 4
    BRONZEIV = 5
    BRONZEIII = 6
    BRONZEII = 7
    BRONZEI = 8
    SILVERIV = 9
    SILVERIII = 10
    SILVERII = 11
    SILVERI = 12
    GOLDIV = 13
    GOLDIII = 14
    GOLDII = 15
    GOLDI = 16
    PLATINUMIV = 17
    PLATINUMIII = 18
    PLATINUMII = 19
    PLATINUMI = 20
    EMERALDIV = 21
    EMERALDIII = 22
    EMERALDII = 23
    EMERALDI = 24
    DIAMONDIV = 25
    DIAMONDIII = 26
    DIAMONDII = 27
    DIAMONDI = 28
    MASTERI = 29
    GRANDMASTERI = 30
    CHALLENGERI = 31


    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class Regions(Enum):
    BR1 = auto()
    EUN1 = auto()
    EUW1 = auto()
    JP1 = auto()
    KR = auto()
    LA1 = auto()
    LA2 = auto()
    ME1 = auto()
    NA1 = auto()
    OC1 = auto()
    RU = auto()
    SG2 = auto()
    TR1 = auto()
    TW2 = auto()
    VN2 = auto()


class Roles(Enum):
    Top = auto()
    Jungle = auto()
    Mid = auto()
    Bot = auto()
    Support = auto()

    def from_riot_str(string: str) -> 'Roles':
        match string:
            case 'TOP':
                return Roles.Top
            case 'JUNGLE':
                return Roles.Jungle
            case 'MIDDLE':
                return Roles.Mid
            case 'BOTTOM':
                return Roles.Bot
            case 'UTILITY':
                return Roles.Support
        
        raise Exception(f'{string} is not a valid role!')
