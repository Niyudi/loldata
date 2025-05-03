from datetime import datetime
from enum import auto, Enum
from queue import Queue
from typing import Any

import pandas
from sqlalchemy import delete, func, literal, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import logger
from constants import IS_FINISHED_PATCH, MAX_UNREGISTERED_MATCHES, PLAYER_QUEUE_SIZE, RANK_COOLDOWN, TARGET_PATCH
from db_models.registry import Matches, MatchPlayers, Players
from db_models.search import PatchPlayers, PlayerRanks, TakenMatches
from db_models.static import Champions, Ranks, Regions
from request_handler import handle_request, Request, RequestType


def run(session: Session):
    df_champions = pandas.read_sql(select(Champions), session.connection())

    taken_matches: list[tuple[Regions, int]] = []
    try:
        operations: Queue[Operation] = Queue()
        while True:
            operations.put_nowait(Operation(OperationType.GET_UNREGISTERED_MATCHES))
            while operations.qsize() > 0:
                operation = operations.get_nowait()
                match operation.type:
                    # FETCH_MATCH_LIST: Requests history of match id's for a given player id.
                    case OperationType.FETCH_MATCH_LIST:
                        player_id = int(operation["player_id"])
                        
                        logger.info(f'Making request for match list of player with id {player_id}...')
                        
                        if IS_FINISHED_PATCH:
                            stmt = select(PatchPlayers).where(PatchPlayers.patch == TARGET_PATCH, PatchPlayers.player_id == player_id)
                            df = pandas.read_sql(stmt, session.connection())

                            if len(df.index) != 0:
                                continue

                        result = handle_request(Request(RequestType.GET_MATCH_LIST, riot_id=operation["riot_id"]))
                        stmt = insert(Matches).values(result).on_conflict_do_nothing()
                        session.execute(stmt)
                        session.commit()

                        if IS_FINISHED_PATCH:
                            stmt = insert(PatchPlayers).values({'patch': TARGET_PATCH, 'player_id': player_id}).on_conflict_do_nothing()
                            session.execute(stmt)
                            session.commit()

                        operations.put_nowait(Operation(OperationType.GET_UNREGISTERED_MATCHES))
                    # GET_PLAYER: TODO description
                    case OperationType.GET_PLAYER:
                        # First, try player that is registered but without a rank in database
                        logger.info('Getting from database player without a registered rank...')

                        stmt = (select(Players.id, Players.riot_id)
                                .join(PlayerRanks, Players.id == PlayerRanks.player_id, isouter=True)
                                .where(PlayerRanks.rank.is_(None))
                                .limit(1))
                        df = pandas.read_sql(stmt, session.connection())

                        if len(df.index) > 0:
                            logger.info(f'Got player with id {df.at[0, "id"]} for search.')
                            operations.put_nowait(Operation(OperationType.REGISTER_RANK, player_id=df.at[0, "id"], riot_id=df.at[0, "riot_id"]))
                            continue

                        # Second, try player who have not had their rank checked in the last RANK_COOLDOWN days
                        logger.info(f'Getting from database player with rank registered more than {RANK_COOLDOWN.days} days ago...')
                        stmt = (select(Players.id, Players.riot_id)
                                .join(PlayerRanks, Players.id == PlayerRanks.player_id, isouter=True)
                                .where(PlayerRanks.last_update < literal(datetime.now().astimezone() - RANK_COOLDOWN))
                                .limit(1))
                        df = pandas.read_sql(stmt, session.connection())

                        if len(df.index) > 0:
                            logger.info(f'Got player with id {df.at[0, "id"]} for search.')
                            operations.put_nowait(Operation(OperationType.REGISTER_RANK, player_id=df.at[0, "id"], riot_id=df.at[0, "riot_id"]))
                            continue

                        raise Exception('No player candidate for search available in database!')
                    # GET_UNREGISTERED_MATCHES: Gets matches from db that have id's, but no data.
                    case OperationType.GET_UNREGISTERED_MATCHES:
                        logger.info(f'Getting matches from db with no data...')

                        stmt = select(Matches.region, Matches.id).where(Matches.patch.is_(None)).limit(MAX_UNREGISTERED_MATCHES)
                        df = pandas.read_sql(stmt, session.connection())

                        if len(df.index) == 0:
                            logger.info(f'No ungegistered mathces in db! Getting new player to fetch matches...')
                            operations.put_nowait(Operation(OperationType.GET_PLAYER))
                        else:
                            taken_matches = list(df.itertuples(index=False, name=None))

                            stmt = insert(TakenMatches).values(df.to_dict(orient='records'))
                            try:
                                session.execute(stmt)
                                session.commit()
                            except IntegrityError as e:
                                session.rollback()
                                operations.put_nowait(Operation(OperationType.GET_UNREGISTERED_MATCHES))
                                continue

                            logger.info(f'Got {len(df.index)} matches wihtout data. Queueing data requests...')

                            for riot_match_id in df.apply(lambda row: f'{row["region"].name}_{row["id"]}', axis=1):
                                operations.put_nowait(Operation(OperationType.REGISTER_MATCH, riot_match_id=riot_match_id))
                    # REGISTER_MATCH: Saves match in database.
                    case OperationType.REGISTER_MATCH:
                        logger.info(f'Making request for match of id {operation["riot_match_id"]}...')
                        result = handle_request(Request(RequestType.GET_MATCH, riot_match_id=operation['riot_match_id']))

                        region, id, match_players = result.pop('region'), result.pop('id'), result.pop('players')
                        stmt = update(Matches).where(Matches.region == region, Matches.id == id).values(result)
                        session.execute(stmt)
                        logger.info(f'Inserting match with id {region}_{id} into database.')
                        if result['is_blue_win'] is None:
                            session.commit()
                            logger.info('Invalid match! Skipping match_players info...')
                            continue
                        
                        for i in range(len(match_players)):
                            # Adds match info to players
                            match_players[i]['region'] = region
                            match_players[i]['match_id'] = id

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

                        stmt = delete(TakenMatches).where(TakenMatches.region == region, TakenMatches.id == id)
                        session.execute(stmt)

                        session.commit()
                        logger.info('Inserted match-player info into database.')
                    # REGISTER_RANK: Requests and saves rank for given player id in database.
                    case OperationType.REGISTER_RANK:
                        player_id = int(operation["player_id"])

                        logger.info(f'Making request for rank of player with id {player_id}...')

                        result = handle_request(Request(RequestType.GET_RANK, player_id=player_id, riot_id=operation["riot_id"]))

                        stmt = (insert(PlayerRanks).values(result)
                                .on_conflict_do_update(index_elements=[PlayerRanks.player_id],
                                                    set_={PlayerRanks.rank: result['rank'],
                                                            PlayerRanks.lp: result['lp'],
                                                            PlayerRanks.last_update: func.current_timestamp()}))
                        session.execute(stmt)
                        session.commit()

                        if result['rank'] >= Ranks.EMERALDIV:
                            operations.put_nowait(Operation(OperationType.FETCH_MATCH_LIST, player_id=player_id, riot_id=operation["riot_id"]))
                            logger.info(f'Player with id {player_id} ranked emerald or above! Queued for match regsitering.')
                        else:
                            operations.put_nowait(Operation(OperationType.GET_PLAYER))
                            logger.info(f'Player with id {player_id} ranked lower than emerald. Getting new player...')
    finally:
        session.rollback()
        for region, id in taken_matches:
            session.execute(delete(TakenMatches).where(TakenMatches.region == region, TakenMatches.id == id))
        session.commit()

###########
# Private #
###########


class OperationType(Enum):
    FETCH_MATCH_LIST = auto()
    GET_PLAYER = auto()
    GET_UNREGISTERED_MATCHES = auto()
    REGISTER_MATCH = auto()
    REGISTER_RANK = auto()


class Operation:
    def __init__(self, type: OperationType, **kwargs):
        self.type: OperationType = type
        self._params: dict[str, Any] = kwargs
    
    
    def __getitem__(self, key: str):
        return self._params[key]
