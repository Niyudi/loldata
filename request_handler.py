import requests

from datetime import datetime
from enum import auto, Enum
from queue import Queue
from time import sleep, time
from typing import Any

from db_models.static import Ranks, Regions, Roles

import logger

from constants import CALL_INTERVAL, DEFAULT_RETRIES, DEFAULT_RETRY_INTERVAL, MAX_ERRORS_PER_WINDOW, MAX_TIMEOUTS_PER_WINDOW, RIOT_API_KEY, WINDOW_SIZE


type Json = dict[str, Any] | list[Any]


HEADERS: Json = { 'X-Riot-Token': RIOT_API_KEY }

last_call: datetime = datetime.now()
code_queue: Queue[int] = Queue(WINDOW_SIZE)
for _ in range(WINDOW_SIZE):
    code_queue.put_nowait(200)
error_count: int = 0
timeout_count: int = 0


class RequestType(Enum):
    GET_MATCH = auto()
    GET_MATCH_LIST = auto()
    GET_PLAYER = auto()
    GET_RANK = auto()


class Request:
    def __init__(self, type: RequestType, **kwargs):
        self.type: RequestType = type
        self._params: dict[str, str] = kwargs
    

    def __getitem__(self, key: str):
        return self._params[key]


def handle_request(request: Request) -> Json:
    match request.type:
        case RequestType.GET_MATCH:
            logger.info(f'Received GET_MATCH request for match id "{request["riot_match_id"]}".')

            json = time_get_request(f'https://americas.api.riotgames.com/lol/match/v5/matches/{request["riot_match_id"]}')

            region, id = json['metadata']['matchId'].split('_')
            is_blue_win: bool = (None if bool(json['info']['participants'][0]['gameEndedInEarlySurrender']) else
                bool(json['info']['participants'][0]['win']) if json['info']['participants'][0]['teamId'] == '100' else
                not bool(json['info']['participants'][0]['win']))
            
            players = None
            if is_blue_win is not None:
                players = []
                missing_role_index = -1
                missing_role_is_blue = False
                for i, entry in enumerate(json['info']['participants']):
                    is_blue_team = entry['teamId'] == 100
                    if entry['teamPosition'] == '':
                        if missing_role_index > -1:
                            missing_role_index = 10
                            break
                        else:
                            missing_role_index = i
                            missing_role_is_blue = is_blue_team
                        players.append({
                            'puuid': entry['puuid'],
                            'champion_name': entry['championName'],
                            'is_blue_team': is_blue_team,
                        })
                    else:
                        players.append({
                            'puuid': entry['puuid'],
                            'champion_name': entry['championName'],
                            'role': Roles.from_riot_str(entry['teamPosition']),
                            'is_blue_team': is_blue_team,
                        })
            
                if missing_role_index == 10:
                    players = None
                    is_blue_win = None
                    logger.info('GET_MATCH fetched match with undetermined roles, registering as invalid...')
                elif missing_role_index > -1:
                    possible_roles = {Roles.Top, Roles.Jungle, Roles.Mid, Roles.Bot, Roles.Support}
                    for i in range(10):
                        if i != missing_role_index:
                            if players[i]['is_blue_team'] == missing_role_is_blue:
                                possible_roles.remove(players[i]['role'])
                                if len(possible_roles) == 1:
                                    players[missing_role_index]['role'] = possible_roles.pop()
                                    break
            else:
                logger.info('GET_MATCH fetched invalid match...')

            logger.info(f'GET_MATCH fetched match with id "{request["riot_match_id"]}".')
            
            return {
                'region': Regions[region],
                'id': int(id),
                'patch': int('{:02}{:02}'.format(*(int(x) for x in json['info']['gameVersion'].split('.')[:2]))),
                'time': int(json['info']['gameStartTimestamp']),
                'duration': int(json['info']['gameDuration']),
                'is_blue_win': is_blue_win,
                'players': players,
            }
        case RequestType.GET_MATCH_LIST:
            logger.info(f'Received GET_MATCH_LIST request for riot id "{request["riot_id"]}".')

            now = int(time())
            result = time_get_request('https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/'
                                    f'{request["riot_id"]}/ids?startTime={now - 1209600}&endTime={now}'
                                    '&type=ranked&start=0&count=100')
        
            logger.info(f'GET_MATCH_LIST fetched {len(result)} matches for riot id "{request["riot_id"]}".')

            return result
        case RequestType.GET_PLAYER:
            logger.info(f'Received GET_PLAYER request for riot id "{request["riot_id"]}".')

            json = time_get_request(f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-puuid/{request["riot_id"]}')

            logger.info(f'GET_PLAYER fetched player name "{json["gameName"]}#{json["tagLine"]}" for riot id "{request["riot_id"]}".')

            return {
                'riot_id': request["riot_id"],
                'name': json['gameName'],
                'tag': json['tagLine'],
            }
        case RequestType.GET_RANK:
            logger.info(f'Received GET_RANK request for riot id "{request["riot_id"]}".')

            json = time_get_request(f'https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{request["riot_id"]}')
            json = time_get_request(f'https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{json["id"]}')

            rank = Ranks['UNRANKED']
            lp = None
            for entry in json:
                if entry['queueType'] == 'RANKED_SOLO_5x5':
                    rank = Ranks[f'{entry["tier"]}{entry["rank"]}']
                    lp = int(entry['leaguePoints'])
                    break

            logger.info(f'GET_RANK fetched rank {rank.name} for riot id "{request["riot_id"]}".')
            
            return {
                'player_id': request["player_id"],
                'rank': rank,
                'lp': lp,
            }


def time_get_request(url: str) -> Json:
    global HEADERS

    global last_call
    global code_queue
    global error_count
    global timeout_count

    delta = (CALL_INTERVAL - (datetime.now() - last_call)).total_seconds()
    if delta > 0:
        sleep(delta)
    
    req = requests.get(url, headers=HEADERS)
    last_call = datetime.now()
    match code_queue.get_nowait():
        case 200:
            pass
        case 429:
            error_count -= 1
            timeout_count -= 1
        case _:
            error_count -= 1
    code_queue.put_nowait(req.status_code)

    i = 1
    while not req.ok:
        if i > DEFAULT_RETRIES:
            logger.error(f'Maximum number of retries ({DEFAULT_RETRIES}) reached!')
            req.raise_for_status()
        
        match req.status_code:
            case 429:
                error_count += 1
                timeout_count += 1

                if timeout_count == MAX_TIMEOUTS_PER_WINDOW:
                    raise Exception(f'Maximum timeout rate ({MAX_TIMEOUTS_PER_WINDOW}/{WINDOW_SIZE}) reached!')

                if 'Retry-After' in req.headers:
                    sleep_interval = float(req.headers['Retry-After'])
                else:
                    sleep_interval = DEFAULT_RETRY_INTERVAL
                logger.warning(f'Timeout happened! Waiting for {sleep_interval:.01f} seconds.')
                sleep(sleep_interval) 
            case _:
                error_count += 1

                if error_count == MAX_ERRORS_PER_WINDOW:
                    logger.error(f'Maximum error rate ({MAX_ERRORS_PER_WINDOW}/{WINDOW_SIZE}) reached!')
                    req.raise_for_status()
        
        req = requests.get(url, headers=HEADERS)
        last_call = datetime.now()
        match code_queue.get_nowait():
            case 200:
                pass
            case 429:
                error_count -= 1
                timeout_count -= 1
            case _:
                error_count -= 1
        code_queue.put_nowait(req.status_code)

        i += 1

    return req.json()
