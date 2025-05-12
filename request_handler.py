from datetime import datetime
from enum import auto, Enum
from queue import Queue
from time import sleep
from typing import Any

import requests

import logger
from constants import (CALL_INTERVAL, DEFAULT_RETRIES, DEFAULT_RETRY_INTERVAL, END_TTIMESTAMP, MAX_ERRORS_PER_WINDOW,
                       MAX_TIMEOUTS_PER_WINDOW, PST_TIMEZONE, RIOT_API_KEY, START_TIMESTAMP, WINDOW_SIZE)
from db_models.static import (ItemOperationType, ObjectiveTypes, Ranks, Regions, Roles,
                              StructureTypes)

type Json = Any # Redundant but shows intention plz don't remove thx


HEADERS: Json = { 'X-Riot-Token': RIOT_API_KEY }
TRINKETS: list[int] = [3330, 3340, 3348, 3363, 3364]

last_call: datetime = datetime.now()
code_queue: Queue[int] = Queue(WINDOW_SIZE)
for _ in range(WINDOW_SIZE):
    code_queue.put_nowait(200)
error_count: int = 0
timeout_count: int = 0


class RequestType(Enum):
    GET_LEAGUE = auto()
    GET_MATCH = auto()
    GET_MATCH_LIST = auto()
    GET_RANK = auto()
    GET_TIMELINE = auto()


class Request:
    def __init__(self, type: RequestType, **kwargs):
        self.type: RequestType = type
        self._params: dict[str, Any] = kwargs
    

    def __getitem__(self, key: str):
        return self._params[key]


def handle_request(request: Request) -> Json:
    match request.type:
        case RequestType.GET_LEAGUE:
            logger.info(f'Received GET_LEAGUE request for rank {request["rank"].name}.')
            tier, rank = request['rank'].tier_rank()

            i = 1
            timestamp = int(datetime.now(PST_TIMEZONE).timestamp())
            json = _time_get_request(f'https://br1.api.riotgames.com/lol/league-exp/v4/entries/RANKED_SOLO_5x5/{tier}/{rank}?page={i}')
            players = [{'riot_id': entry['puuid'], 'timestamp': timestamp, 'rank': request['rank'], 'lp': entry['leaguePoints']} for entry in json]
            while len(json) == 205:
                logger.info(f'GET_LEAGUE fetching {len(players)} players...')
                i += 1
                timestamp = int(datetime.now(PST_TIMEZONE).timestamp())
                json = _time_get_request(f'https://br1.api.riotgames.com/lol/league-exp/v4/entries/RANKED_SOLO_5x5/{tier}/{rank}?page={i}')
                players.extend([{'riot_id': entry['puuid'], 'timestamp': timestamp, 'rank': request['rank'], 'lp': entry['leaguePoints']} for entry in json])
            
            logger.info(f'GET_LEAGUE fetched {len(players)} players in total from rank {request["rank"].name}!')
            return players
        case RequestType.GET_MATCH:
            logger.info(f'Received GET_MATCH request for match id "{request["riot_match_id"]}".')

            json = _time_get_request(f'https://americas.api.riotgames.com/lol/match/v5/matches/{request["riot_match_id"]}')

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
                'patch': int('{:02}{:02}'.format(*(int(x) for x in json['info']['gameVersion'].split('.')[:2]))),
                'time': int(json['info']['gameStartTimestamp']),
                'duration': int(json['info']['gameDuration']),
                'is_blue_win': is_blue_win,
                'players': players,
            }
        case RequestType.GET_MATCH_LIST:
            logger.info(f'Received GET_MATCH_LIST request for riot id "{request["riot_id"]}".')

            i = 0
            result = []
            while True:
                result_one = _time_get_request('https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/'
                                               f'{request["riot_id"]}/ids?startTime={START_TIMESTAMP}&endTime={END_TTIMESTAMP}'
                                               f'&queue=420&start={i}&count=100')
                result.extend(result_one)
                if len(result_one) < 100:
                    break
                i += 100

            logger.info(f'GET_MATCH_LIST fetched {len(result)} matches for riot id "{request["riot_id"]}".')

            return [{'region': Regions[region], 'riot_id': int(riot_id)} for region, riot_id in [x.split('_') for x in result]]
        case RequestType.GET_RANK:
            logger.info(f'Received GET_RANK request for riot id "{request["riot_id"]}".')

            timestamp = int(datetime.now(PST_TIMEZONE).timestamp())
            json = _time_get_request(f'https://br1.api.riotgames.com/lol/league/v4/entries/by-puuid/{request["riot_id"]}')

            rank = Ranks['UNRANKED']
            lp = None
            for entry in json:
                if entry['queueType'] == 'RANKED_SOLO_5x5':
                    if entry['tier'] in ('MASTER', 'GRANDMASTER', 'CHALLENGER'):
                        rank = Ranks[entry['tier']]
                    else:
                        rank = Ranks[f'{entry["tier"]}{entry["rank"]}']
                    lp = int(entry['leaguePoints'])
                    break

            logger.info(f'GET_RANK fetched rank {rank.name}{"" if lp is None else f" {lp}LP"} for riot id "{request["riot_id"]}".')
            
            return {
                'timestamp': timestamp,
                'rank': rank,
                'lp': lp,
            }
        case RequestType.GET_TIMELINE:
            logger.info(f'Received GET_TIMELINE request for match id "{request["riot_match_id"]}".')

            json = _time_get_request(f'https://americas.api.riotgames.com/lol/match/v5/matches/{request["riot_match_id"]}/timeline')['info']

            participants: dict[int, (Roles, bool)] = {}
            for participant_dict in json['participants']:
                participants[participant_dict['participantId']] = request['riot_id_role_dict'][participant_dict['puuid']]
            
            result = {
                'ITEM': [],
                'KILL': [],
                'OBJECTIVE': [],
                'SNAPSHOT': [],
                'STRUCTURE': [],
            }
            for frame in json['frames']:
                for participant_id, snapshot in frame['participantFrames'].items():
                    result['SNAPSHOT'].append({
                        'timeline_id': request['timelines_dict'][participants[int(participant_id)]],
                        'timestamp': frame['timestamp'],
                        'crowd_control_time': snapshot['timeEnemySpentControlled'],
                        'damage_magic': snapshot['damageStats']['magicDamageDone'],
                        'damage_magic_champions': snapshot['damageStats']['magicDamageDoneToChampions'],
                        'damage_magic_taken': snapshot['damageStats']['magicDamageTaken'],
                        'damage_physical': snapshot['damageStats']['physicalDamageDone'],
                        'damage_physical_champions': snapshot['damageStats']['physicalDamageDoneToChampions'],
                        'damage_physical_taken': snapshot['damageStats']['physicalDamageTaken'],
                        'damage_true': snapshot['damageStats']['trueDamageDone'],
                        'damage_true_champions': snapshot['damageStats']['trueDamageDoneToChampions'],
                        'damage_true_taken': snapshot['damageStats']['trueDamageTaken'],
                        'experience': snapshot['xp'],
                        'minions_killed': snapshot['minionsKilled'],
                        'minions_killed_jungle': snapshot['jungleMinionsKilled'],
                        'position_x': snapshot['position']['x'],
                        'position_y': snapshot['position']['y'],
                        'total_gold': snapshot['totalGold'],
                    })

                for event in frame['events']:
                    match event['type']:
                        case 'BUILDING_KILL':
                            result['STRUCTURE'].append({
                                'timeline_id': request['timelines_dict'][participants[event['killerId']] if event['killerId'] != 0
                                                                         else (None, event['teamId'] == '100')],
                                'timestamp': event['timestamp'],
                                'type': StructureTypes.from_riot_type(event['buildingType'],
                                                                      event['laneType'],
                                                                      event['towerType'] if 'towerType' in event else None),
                                'assist_timeline_ids': set(request['timelines_dict'][participants[participant_id]]
                                                           for participant_id in event['assistingParticipantIds'])
                                                           if 'assistingParticipantIds' in event else set(),
                            })
                        case 'CHAMPION_KILL':
                            result['KILL'].append({
                                'timeline_id': request['timelines_dict'][participants[event['killerId']] if event['killerId'] != 0
                                                                         else (None, not participants[event['victimId']][1])],
                                'timestamp': event['timestamp'],
                                'target_role': participants[event['victimId']][0],
                                'assist_timeline_ids': set(request['timelines_dict'][participants[participant_id]]
                                                           for participant_id in event['assistingParticipantIds'])
                                                           if 'assistingParticipantIds' in event else set(),
                            })
                        case 'ELITE_MONSTER_KILL':
                            result['OBJECTIVE'].append({
                                'timeline_id': request['timelines_dict'][participants[event['killerId']] if event['killerId'] != 0
                                                                         else (None, event['killerTeamId'] == '100')],
                                'timestamp': event['timestamp'],
                                'type': ObjectiveTypes.from_riot_type(event['monsterType'],
                                                                      event['monsterSubType'] if 'monsterSubType' in event else None),
                                'assist_timeline_ids': set(request['timelines_dict'][participants[participant_id]]
                                                           for participant_id in event['assistingParticipantIds'])
                                                           if 'assistingParticipantIds' in event else set(),
                            })
                        case 'ITEM_DESTROYED':
                            result['ITEM'].append({
                                'timeline_id': request['timelines_dict'][participants[event['participantId']]],
                                'timestamp': event['timestamp'],
                                'item_id': event['itemId'],
                                'operation_type': ItemOperationType.DESTROYED,
                            })
                        case 'ITEM_PURCHASED':
                            result['ITEM'].append({
                                'timeline_id': request['timelines_dict'][participants[event['participantId']]],
                                'timestamp': event['timestamp'],
                                'item_id': event['itemId'],
                                'operation_type': ItemOperationType.PURCHASED,
                            })
                        case 'ITEM_SOLD':
                            result['ITEM'].append({
                                'timeline_id': request['timelines_dict'][participants[event['participantId']]],
                                'timestamp': event['timestamp'],
                                'item_id': event['itemId'],
                                'operation_type': ItemOperationType.SOLD,
                            })
                        case 'ITEM_UNDO':
                            if event['afterId'] != 0:
                                result['ITEM'].append({
                                    'timeline_id': request['timelines_dict'][participants[event['participantId']]],
                                    'timestamp': event['timestamp'],
                                    'item_id': event['afterId'],
                                    'operation_type': ItemOperationType.UNDO_DESTROY,
                                })
                            elif event['beforeId'] != 0:
                                result['ITEM'].append({
                                    'timeline_id': request['timelines_dict'][participants[event['participantId']]],
                                    'timestamp': event['timestamp'],
                                    'item_id': event['beforeId'],
                                    'operation_type': ItemOperationType.UNDO_CREATE,
                                })
                            else:
                                raise Exception('OLHA ISSO AQUI PAE')
            
            return result
            

###########
# Private #
###########


def _time_get_request(url: str) -> Json:
    global HEADERS

    global last_call
    global code_queue
    global error_count
    global timeout_count

    delta = (CALL_INTERVAL - (datetime.now() - last_call)).total_seconds()
    if delta > 0:
        sleep(delta)
    
    attempts = 0
    while True:
        attempts += 1
        if attempts > 5:
            req = requests.get(url, headers=HEADERS)
            break
        try:
            req = requests.get(url, headers=HEADERS)
            break
        except requests.exceptions.ChunkedEncodingError:
            sleep(1.0)

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
        
        if req.status_code == 429:
            error_count += 1
            timeout_count += 1

            if timeout_count == MAX_TIMEOUTS_PER_WINDOW:
                logger.error(f'Maximum timeout rate ({MAX_TIMEOUTS_PER_WINDOW}/{WINDOW_SIZE}) reached!')
                req.raise_for_status()

            if 'Retry-After' in req.headers:
                sleep_interval = float(req.headers['Retry-After'])
            else:
                sleep_interval = DEFAULT_RETRY_INTERVAL
            logger.warning(f'Timeout happened! Waiting for {sleep_interval:.01f} seconds.')
            
            sleep(sleep_interval)
        elif req.status_code == 400 and req.json()['status']['message'] == 'Unknown apikey':
            raise Exception('Invalid Riot API key!')
        else:
            error_count += 1

            if error_count == MAX_ERRORS_PER_WINDOW:
                logger.error(f'Maximum error rate ({MAX_ERRORS_PER_WINDOW}/{WINDOW_SIZE}) reached!')
                req.raise_for_status()
            
            try:
                req.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.warning(f'HTTP error: {str(e)}. Retrying...')
            
            sleep(DEFAULT_RETRY_INTERVAL)
        
        attempts = 0
        while True:
            attempts += 1
            if attempts > 5:
                req = requests.get(url, headers=HEADERS)
                break
            try:
                req = requests.get(url, headers=HEADERS)
                break
            except requests.exceptions.ChunkedEncodingError:
                sleep(1.0)
        
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
