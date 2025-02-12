import requests

from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import insert
from time import sleep, time
from typing import Any

from db_models.static import Ranks, Roles

from constants import CALL_INTERVAL, DEFAULT_RETRIES, DEFAULT_RETRY_INTERVAL, RIOT_API_KEY

HEADERS = { 'X-Riot-Token': RIOT_API_KEY }

last_call: datetime = datetime.now()


class RequestType(Enum):
    GET_RANK = 1
    GET_MATCH_LIST = 2
    GET_MATCH = 3


class Request:
    def __init__(self, type: RequestType, **kwargs):
        self.type: RequestType = type
        self.params: dict[str, str] = kwargs


def handle_request(request: Request) -> dict[str, Any]:
    match request.type:
        case RequestType.GET_RANK:
            json = time_get_request(f'https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{request.params["id"]}', headers=HEADERS)
            json = time_get_request(f'https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{json["id"]}', headers=HEADERS)

            rank = Ranks.UNRANKED
            lp = None
            for entry in json:
                if entry['queueType'] == 'RANKED_SOLO_5x5':
                    rank = f'{entry["tier"]}{entry["rank"]}'
                    lp = int(entry['leaguePoints'])
                    break
            
            return {
                'player_id': request.params["id"],
                'rank': rank,
                'lp': lp,
            }
        case RequestType.GET_MATCH_LIST:
            now = int(time())
            return time_get_request('https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/'
                                    f'{request.params["id"]}/ids?startTime={now - 1209600}&endTime={now}'
                                    '&type=ranked&start=0&count=100')
        case RequestType.GET_MATCH:
            json = time_get_request(f'https://americas.api.riotgames.com/lol/match/v5/matches/{request.params["id"]}')

            region, id = json['metadata']['matchId'].split('_')
            is_blue_win: bool = (None if bool(json['info']['participants'][0]['gameEndedInEarlySurrender']) else
                bool(json['info']['participants'][0]['win']) if json['info']['participants'][0]['teamId'] == '100' else
                not bool(json['info']['participants'][0]['win']))
            players = [{
                'puuid': entry['puuid'],
                'champion_name': entry['champion_name'],
                'role': Roles.from_riot_str(entry['teamPosition']),
                'is_blue_team': entry['teamId'] == '100',
            } for entry in json['info']['participants']]

            return {
                'region': region,
                'id': int(id),
                'patch': '.'.join(json['info']['gameVersion'].split('.')[:2]),
                'time': int(json['info']['gameStartTimestamp']),
                'duration': int(json['info']['gameDuration']),
                'is_blue_win': is_blue_win,
                'players': players,
            }


def time_get_request(*args, **kwargs):
    global last_call

    sleep((CALL_INTERVAL - (datetime.now() - last_call)).total_seconds())
    
    req = requests.get(*args, **kwargs)
    last_call = datetime.now()
    i = 1

    while not req.ok:
        if i > DEFAULT_RETRIES:
            req.raise_for_status()
        
        if req.status_code == 429:
            if 'Retry-After' in req.headers:
                sleep(float(req.headers['Retry-After']))
            else:
                sleep(DEFAULT_RETRY_INTERVAL)
        else:
            req.raise_for_status()
        
        req = requests.get(*args, **kwargs)
        last_call = datetime.now()
        i += 1

    return req.json()
