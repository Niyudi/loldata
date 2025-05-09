from enum import auto, Enum
from queue import Queue
from typing import Any

import pandas
from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import logger
from config import GET_PLAYERS, MINIMUM_RANK
from constants import IS_FINISHED_PATCH, MATCH_BATCH_SIZE, TARGET_PATCH
from db_models.match_data import Timelines
from db_models.registry import Matches, MatchPlayers, Players, PlayerRanks
from db_models.search import PatchPlayers, TakenMatches
from db_models.static import Champions, Ranks, Regions, Roles
from request_handler import Request, RequestType
from request_handler import handle_request


def run(session: Session):
    df_champions = pandas.read_sql(select(Champions), session.connection())

    if GET_PLAYERS:
        logger.info('Fetching players from leagues to begin search.')
        rank = Ranks.CHALLENGER
        total = 0
        while rank >= MINIMUM_RANK:
            result = handle_request(Request(RequestType.GET_LEAGUE, rank=rank))
            df = pandas.DataFrame.from_records(result).drop_duplicates('riot_id', keep='last')

            rowcount = session.execute(insert(Players)
                                       .values(df[['riot_id']].to_dict(orient='records'))
                                       .on_conflict_do_nothing()).rowcount
            total += rowcount
            logger.info(f'Regsitered {rowcount} new players in database!')
            
            stmt = select(Players).where(Players.riot_id.in_(df['riot_id']))
            df_players = pandas.read_sql(stmt, session.connection()).rename(columns={'id': 'player_id'})
            df = pandas.merge(df, df_players, on='riot_id').drop(columns='riot_id')

            session.execute(insert(PlayerRanks).values(df.to_dict(orient='records')).on_conflict_do_nothing())
            session.commit()

            rank = rank.previous()
        logger.info(f'Fetched and registered {total} players!')
        del df, df_players, rank, result, rowcount, stmt, total

    taken_matches: list[tuple[Regions, int]] = []
    operations: Queue[Operation] = Queue()
    try:
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

                        if IS_FINISHED_PATCH:
                            stmt = insert(PatchPlayers).values({'patch': TARGET_PATCH, 'player_id': player_id}).on_conflict_do_nothing()
                            session.execute(stmt)
                        
                        session.commit()

                        operations.put_nowait(Operation(OperationType.GET_UNREGISTERED_MATCHES))
                    # GET_PLAYER: Gets players from database that have not had their matches registered yet and are within search criteria.
                    case OperationType.GET_PLAYER:
                        logger.info('Getting from database player to register matches...')

                        q1 = (select(Players.id, Players.riot_id, PlayerRanks.rank,
                                     func.rank().over(partition_by=(Players.id, Players.riot_id),
                                                      order_by=PlayerRanks.timestamp.desc()).label('time'))
                              .join(PlayerRanks, Players.id == PlayerRanks.player_id, isouter=True)
                              .subquery())
                        q2 = select(PatchPlayers).where(PatchPlayers.patch == TARGET_PATCH).subquery()
                        stmt = (select(q1.c.id, q1.c.riot_id)
                                .join(q2, q1.c.id == q2.c.player_id, isouter=True)
                                .where(q1.c.time == 1, q1.c.rank >= MINIMUM_RANK, q2.c.patch.is_(None))
                                .limit(1))
                        df = pandas.read_sql(stmt, session.connection())

                        if len(df.index) == 0:
                            raise Exception(f'No players that weren\'t searched for patch {TARGET_PATCH} and are ranked {MINIMUM_RANK.name} or above! Ending search.')
                        
                        logger.info(f'Got player with id {df.at[0, "id"]} for search.')
                        operations.put_nowait(Operation(OperationType.FETCH_MATCH_LIST, player_id=df.at[0, "id"], riot_id=df.at[0, "riot_id"]))
                    # GET_UNREGISTERED_MATCHES: Gets matches from db that have id's, but no data.
                    case OperationType.GET_UNREGISTERED_MATCHES:
                        logger.info(f'Getting matches from db with no data...')

                        stmt = (select(Matches.region, Matches.id)
                                .join(TakenMatches, and_(Matches.region == TakenMatches.region, Matches.id == TakenMatches.id), isouter=True)
                                .where(Matches.patch.is_(None), TakenMatches.id.is_(None))
                                .limit(MATCH_BATCH_SIZE))
                        df = pandas.read_sql(stmt, session.connection())

                        if len(df.index) == 0:
                            logger.info(f'No ungegistered mathces in db! Getting new player to fetch matches...')
                            operations.put_nowait(Operation(OperationType.GET_PLAYER))
                            continue
                        
                        taken_matches = list(df.itertuples(index=False, name=None))

                        stmt = insert(TakenMatches).values(df.to_dict(orient='records'))
                        try:
                            session.execute(stmt)
                            session.commit()
                        except IntegrityError as e:
                            logger.info(f'Matches already taken (probably due to concurrent request)! Retrying...')
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
                        logger.info(f'Inserting match with id {region.name}_{id} into database.')
                        if result['is_blue_win'] is None:
                            session.commit()
                            logger.info('Invalid match! Skipping aditional match info...')
                            continue
                        
                        riot_id_role_dict: dict[str, (Roles, bool)] = {}
                        for i in range(len(match_players)):
                            # Makes riot_id -> role dicitonary
                            riot_id_role_dict[match_players[i]['puuid']] = (match_players[i]['role'], match_players[i]['is_blue_team'])

                            # Adds match info to players
                            match_players[i]['region'] = region
                            match_players[i]['match_id'] = id

                            # Player registry
                            match_players[i]['player_id'] = session.execute(select(Players.id).where(Players.riot_id == match_players[i]['puuid'])).scalar()

                            if match_players[i]['player_id'] is None:
                                logger.info(f'Player with riot id "{match_players[i]["puuid"]}" not registered! Regsitering...')
                                session.execute(insert(Players).values({'riot_id': match_players[i]['puuid']}))

                                rank_result = handle_request(Request(RequestType.GET_RANK, riot_id=match_players[i]['puuid']))
                                rank_result['player_id'] = session.execute(select(Players.id).where(Players.riot_id == match_players[i]['puuid'])).scalar()
                                session.execute(insert(PlayerRanks).values(rank_result))

                                match_players[i]['player_id'] = rank_result['player_id']
                            
                            match_players[i].pop('puuid')

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

                        session.execute(insert(MatchPlayers).values(match_players))

                        timelines = []
                        for is_blue_team in (True, False):
                            for role in (Roles.Top, Roles.Jungle, Roles.Mid, Roles.Bot, Roles.Support, None):
                                timelines.append({
                                    'region': region,
                                    'match_id': id,
                                    'role': role,
                                    'is_blue_team': is_blue_team,
                                })
                        
                        session.execute(insert(Timelines).values(timelines))

                        df = pandas.read_sql(select(Timelines.id, Timelines.role, Timelines.is_blue_team)
                                             .where(Timelines.region == region, Timelines.match_id == id), session.connection())
                        role_timelines_dict = {}
                        for _, row in df.iterrows():
                            role_timelines_dict[(row['role'], row['is_blue_team'])] = row['id']

                        result = handle_request(Request(RequestType.GET_TIMELINE,
                                                        riot_match_id=operation['riot_match_id'],
                                                        riot_id_role_dict=riot_id_role_dict,
                                                        role_timelines_dict=role_timelines_dict))
                        
                        for event in result:  # TODO handle all cases
                            match event['timeline_type']:
                                case 'ITEM':
                                    pass
                                case 'KILL':
                                    pass
                                case 'OBJECTIVE':
                                    pass
                                case 'STRUCTURE':
                                    pass


                        session.execute(delete(TakenMatches).where(TakenMatches.region == region, TakenMatches.id == id))

                        session.commit()
                        logger.info('Inserted match-player info into database.')
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


class Operation:
    def __init__(self, type: OperationType, **kwargs):
        self.type: OperationType = type
        self._params: dict[str, Any] = kwargs
    
    
    def __getitem__(self, key: str):
        return self._params[key]
