import pandas

from datetime import datetime
from enum import auto, Enum
from queue import Queue
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from typing import Any

from db_models.registry import Matches, MatchPlayers, Players
from db_models.search import PlayerRanks
from db_models.static import Champions, Ranks

import logger

from constants import DB_URI, RANK_COOLDOWN
from initial_players import initial_players
from request_handler import handle_request, Request, RequestType


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


def main():
    logger.init()
    try:
        engine = create_engine(DB_URI)

        with Session(engine) as session:
            df_champions = pandas.read_sql(select(Champions), session.connection())

            players: Queue[tuple[int, str]] = Queue(50)
            players_set: set[str] = {}
            operations: Queue[Operation] = Queue()

            while True:
                if players.qsize() == 0:
                    players, players_set = initial_players(session)
                
                player_id, riot_id = players.get_nowait()
                players_set.remove(riot_id)
                operations.put_nowait(Operation(OperationType.REGISTER_RANK))

                logger.info(f'Starting operations for player with id "{player_id}".')
                while operations.qsize() > 0:
                    operation = operations.get_nowait()
                    match operation.type:
                        case OperationType.FETCH_MATCH_LIST:
                            logger.info(f'Making request for match list of player with id {player_id}...')
                            result = handle_request(Request(RequestType.GET_MATCH_LIST, riot_id=riot_id))
                            
                            for riot_match_id in result:
                                operations.put_nowait(Operation(OperationType.REGISTER_MATCH, riot_match_id=riot_match_id))
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
    except Exception as e:
        logger.error(f'{type(e).__name__}: {str(e)}', on_console=False)
        raise e


if __name__ == '__main__':
    main()
