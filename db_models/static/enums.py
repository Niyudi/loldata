from enum import auto, Enum
from functools import total_ordering


class ObjectiveTypes(Enum):
    ATHAKAN = auto()
    BARON = auto()
    DRAKE_CHEMTECH = auto()
    DRAKE_CLOUD = auto()
    DRAKE_HEXTECH = auto()
    DRAKE_INFERNAL = auto()
    DRAKE_MOUNTAIN = auto()
    DRAKE_OCEAN = auto()
    ELDER_DRAKE = auto()
    GRUBS = auto()
    HERALD = auto()


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
    MASTER = 29
    GRANDMASTER = 30
    CHALLENGER = 31


    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    
    
    def previous(self) -> 'Ranks':
        if self == Ranks.UNRANKED:
            return None
        else:
         return Ranks(self.value - 1)
    

    def tier_rank(self) -> tuple[str, str | None]:
        match self:
            case Ranks.UNRANKED:
                return ('UNRANKED', None)
            case Ranks.IRONIV:
                return ('IRON', 'IV')
            case Ranks.IRONIII:
                return ('IRON', 'III')
            case Ranks.IRONII:
                return ('IRON', 'II')
            case Ranks.IRONI:
                return ('IRON', 'I')
            case Ranks.BRONZEIV:
                return ('BRONZE', 'IV')
            case Ranks.BRONZEIII:
                return ('BRONZE', 'III')
            case Ranks.BRONZEII:
                return ('BRONZE', 'II')
            case Ranks.BRONZEI:
                return ('BRONZE', 'I')
            case Ranks.SILVERIV:
                return ('SILVER', 'IV')
            case Ranks.SILVERIII:
                return ('SILVER', 'III')
            case Ranks.SILVERII:
                return ('SILVER', 'II')
            case Ranks.SILVERI:
                return ('SILVER', 'I')
            case Ranks.GOLDIV:
                return ('GOLD', 'IV')
            case Ranks.GOLDIII:
                return ('GOLD', 'III')
            case Ranks.GOLDII:
                return ('GOLD', 'II')
            case Ranks.GOLDI:
                return ('GOLD', 'I')
            case Ranks.PLATINUMIV:
                return ('PLATINUM', 'IV')
            case Ranks.PLATINUMIII:
                return ('PLATINUM', 'III')
            case Ranks.PLATINUMII:
                return ('PLATINUM', 'II')
            case Ranks.PLATINUMI:
                return ('PLATINUM', 'I')
            case Ranks.EMERALDIV:
                return ('EMERALD', 'IV')
            case Ranks.EMERALDIII:
                return ('EMERALD', 'III')
            case Ranks.EMERALDII:
                return ('EMERALD', 'II')
            case Ranks.EMERALDI:
                return ('EMERALD', 'I')
            case Ranks.DIAMONDIV:
                return ('DIAMOND', 'IV')
            case Ranks.DIAMONDIII:
                return ('DIAMOND', 'III')
            case Ranks.DIAMONDII:
                return ('DIAMOND', 'II')
            case Ranks.DIAMONDI:
                return ('DIAMOND', 'I')
            case Ranks.MASTER:
                return ('MASTER', 'I')
            case Ranks.GRANDMASTER:
                return ('GRANDMASTER', 'I')
            case Ranks.CHALLENGER:
                return ('CHALLENGER', 'I')


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


class StructureTypes(Enum):
    TURRET_T1_TOP = auto()
    TURRET_T1_MID = auto()
    TURRET_T1_BOT = auto()
    TURRET_T2_TOP = auto()
    TURRET_T2_MID = auto()
    TURRET_T2_BOT = auto()
    TURRET_T3_TOP = auto()
    TURRET_T3_MID = auto()
    TURRET_T3_BOT = auto()
    INHIBITOR_TOP = auto()
    INHIBITOR_MID = auto()
    INHIBITOR_BOT = auto()
    TURRET_NEXUS = auto()
