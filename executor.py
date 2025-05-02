from datetime import datetime
from enum import auto, Enum
from queue import Queue
from typing import Any

import pandas
from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

import logger
from constants import PLAYER_QUEUE_SIZE, RANK_COOLDOWN
from db_models.registry import Matches, MatchPlayers, Players
from db_models.search import PlayerRanks
from db_models.static import Champions, Ranks
from request_handler import handle_request, Request, RequestType


def run(session: Session):
    df_champions = pandas.read_sql(select(Champions), session.connection())

    players: Queue[tuple[int, str]] = Queue(PLAYER_QUEUE_SIZE)
    players_set: set[str] = {}
    operations: Queue[Operation] = Queue()

    while True:
        if players.qsize() == 0:
            players, players_set = _initial_players(session)
        
        player_id, riot_id = players.get_nowait()
        players_set.remove(riot_id)
        operations.put_nowait(Operation(OperationType.REGISTER_RANK))

        logger.info(f'Starting operations for player with id "{player_id}".')
        while operations.qsize() > 0:
            operation = operations.get_nowait()
            match operation.type:
                # FETCH_MATCH_LIST: Requests history of match id's for a given player id.
                case OperationType.FETCH_MATCH_LIST:
                    logger.info(f'Making request for match list of player with id {player_id}...')
                    result = handle_request(Request(RequestType.GET_MATCH_LIST, riot_id=riot_id))
                    
                    for riot_match_id in result:
                        operations.put_nowait(Operation(OperationType.REGISTER_MATCH, riot_match_id=riot_match_id))
                # REGISTER_MATCH: Saves match in databse.
                case OperationType.REGISTER_MATCH:
                    logger.info(f'Making request for match of id {operation["riot_match_id"]}...')
                    result = handle_request(Request(RequestType.GET_MATCH, riot_match_id=operation['riot_match_id']))

                    match_players = result.pop('players')
                    stmt = (insert(Matches)
                            .values(result)
                            .on_conflict_do_nothing())
                    rowcount = session.execute(stmt).rowcount
                    logger.info(f'Inserting match with id {result["region"].name}_{result["id"]} into database.')
                    if rowcount == 0:
                        session.commit()
                        logger.info('Match already in databse! Skipping...')
                        continue
                    if result['is_blue_win'] is None:
                        session.commit()
                        logger.info('Invalid match! Skipping...')
                        continue
                    
                    for i in range(len(match_players)):
                        # Adds match info to players
                        match_players[i]['region'] = result['region']
                        match_players[i]['match_id'] = result['id']

                        # Player registry
                        stmt = (select(Players.id, PlayerRanks.rank, PlayerRanks.last_update)
                                .join(PlayerRanks, Players.id == PlayerRanks.player_id, isouter=True)
                                .where(Players.riot_id == match_players[i]['puuid']))
                        df = pandas.read_sql(stmt, session.connection())

                        if len(df.index) == 0:
                            logger.info(f'Player with riot id "{match_players[i]["puuid"]}" not registered. Making request...')
                            player_result = handle_request(Request(RequestType.GET_PLAYER, riot_id=match_players[i]['puuid']))
                            stmt = (insert(Players)
                                    .values(player_result))
                            session.execute(stmt)

                            stmt = (select(Players.id)
                                .where(Players.riot_id == match_players[i]['puuid']))
                            df = pandas.read_sql(stmt, session.connection())
                            df['rank'] = None
                            df['last_update'] = None
                        
                        if not players.full() and match_players[i]['puuid'] not in players_set and (df['rank'].iloc[0] is None or datetime.now().astimezone() - df['last_update'].iloc[0] >= RANK_COOLDOWN):
                            players.put_nowait((int(df['id'].iloc[0]), match_players[i]['puuid']))
                            players_set.add(match_players[i]['puuid'])
                            logger.info(f'Player with id {df["id"].iloc[0]} rank check has expired! Placed in queue for recheck,')

                        match_players[i].pop('puuid')
                        match_players[i]['player_id'] = int(df['id'].iloc[0])

                        # Champion regsitry
                        df = df_champions[df_champions['name'] == match_players[i]['champion_name']]
                        
                        if len(df.index) == 0:
                            stmt = (insert(Champions)
                                    .values({'name': match_players[i]['champion_name']}))
                            session.execute(stmt)
                            df_champions = pandas.read_sql(select(Champions), session.connection())
                            df = df_champions[df_champions['name'] == match_players[i]['champion_name']]
                            logger.warning(f'New champion "{match_players[i]["champion_name"]}" inserted! Now there are {len(df_champions.index)} champions registered.')
                        
                        match_players[i].pop('champion_name')
                        match_players[i]['champion_id'] = int(df['id'].iloc[0])

                    stmt = (insert(MatchPlayers)
                            .values(match_players))
                    session.execute(stmt)
                    session.commit()
                    logger.info('Inserted match-player info into database.')
                # REGISTER_RANK: Requests and saves rank for given player id in database.
                case OperationType.REGISTER_RANK:
                    logger.info(f'Making request for rank of player with id {player_id}...')
                    result = handle_request(Request(RequestType.GET_RANK, player_id=player_id, riot_id=riot_id))

                    stmt = (insert(PlayerRanks)
                            .values(result)
                            .on_conflict_do_update(index_elements=[PlayerRanks.player_id],
                                                set_={PlayerRanks.rank: result['rank'],
                                                        PlayerRanks.lp: result['lp'],
                                                        PlayerRanks.last_update: func.current_timestamp()}))
                    session.execute(stmt)
                    session.commit()

                    if result['rank'] >= Ranks.EMERALDIV:
                        operations.put_nowait(Operation(OperationType.FETCH_MATCH_LIST))
                        logger.info(f'PLayer with id {player_id} ranked emerald or above! Queued for match regsitering.')


###########
# Private #
###########


class OperationType(Enum):
    FETCH_MATCH_LIST = auto()
    REGISTER_MATCH = auto()
    REGISTER_RANK = auto()


class Operation:
    def __init__(self, type: OperationType, **kwargs):
        self.type: OperationType = type
        self._params: dict[str, Any] = kwargs
    
    
    def __getitem__(self, key: str):
        return self._params[key]


def _initial_players(session: Session) -> tuple[Queue[tuple[int, str]], set[str]]:
    # First, try players that are registered but without a rank in database
    logger.info('Fetching from database players without a registered rank...')

    stmt = (select(Players.id, Players.riot_id)
            .join(PlayerRanks, Players.id == PlayerRanks.player_id, isouter=True)
            .where(PlayerRanks.rank.is_(None))
            .limit(literal(PLAYER_QUEUE_SIZE)))
    df = pandas.read_sql(stmt, session.connection())

    if len(df.index) > 0:
        queue = Queue(PLAYER_QUEUE_SIZE)
        df.apply(lambda row: queue.put_nowait((row['id'], row['riot_id'])), axis=1)

        logger.info(f'Fetched {queue.qsize()} players for initial search.')
        return queue, set(df['riot_id'])
    
    logger.info(f'No candidates found!')

    # Second, try players who have not had their ranks checked in the last rank_cooldown days
    logger.info(f'Fetching from database players with ranks registered more than {RANK_COOLDOWN.days} days ago...')
    stmt = (select(Players.id, Players.riot_id)
            .join(PlayerRanks, Players.id == PlayerRanks.player_id, isouter=True)
            .where(PlayerRanks.last_update < literal(datetime.now().astimezone() - RANK_COOLDOWN))
            .limit(literal(PLAYER_QUEUE_SIZE)))
    df = pandas.read_sql(stmt, session.connection())

    if len(df.index) > 0:
        queue = Queue(PLAYER_QUEUE_SIZE)
        df.apply(lambda row: queue.put_nowait((row['id'], row['riot_id'])), axis=1)

        logger.info(f'Fetched {queue.qsize()} players for initial search.')
        return queue, set(df['riot_id'])

    logger.info(f'No candidates found!')

    raise Exception('No intial player candidates available in database!')
