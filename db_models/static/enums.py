from enum import IntEnum


class Ranks(IntEnum):
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


class Regions(IntEnum):
    BR1 = 0
    EUN1 = 1
    EUW1 = 2
    JP1 = 3
    KR = 4
    LA1 = 5
    LA2 = 6
    ME1 = 7
    NA1 = 8
    OC1 = 9
    RU = 10
    SG2 = 11
    TR1 = 12
    TW2 = 13
    VN2 = 14


class Roles(IntEnum):
    Top = 0
    Jungle = 1
    Mid = 2
    Bot = 3
    Support = 4

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