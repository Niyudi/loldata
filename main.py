import pandas

from queue import Queue
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from db_models.registry import Matches, MatchPlayers, Players
from db_models.search import PlayerRanks
from db_models.static import Champions, Ranks

import logger

from initial_players import initial_players
from request_handler import handle_request, Request, RequestType


def main():
    logger.init()
    engine = create_engine('postgresql://avnadmin:AVNS_O2iqSXw8Fkq1rn2Ycoc@pg-loldata-loldata.e.aivencloud.com:13374/defaultdb?sslmode=require')

    with Session(engine) as session:
        df_champions = pandas.read_sql(select(Champions), session.connection())

        players: Queue[tuple[int, str]] = initial_players(session)
        requests: Queue[Request] = Queue()

        while players.qsize() > 0:
            id, riot_id = players.get_nowait()
            requests.put_nowait(Request(RequestType.GET_RANK, id=id, riot_id=riot_id))
            while requests.qsize() > 0:
                request = requests.get_nowait()
                print(request.type)
                result = handle_request(request)

                match request.type:
                    case RequestType.GET_RANK:
                        stmt = (insert(PlayerRanks)
                                .values(result)
                                .on_conflict_do_update(index_elements=[PlayerRanks.player_id],
                                                       set_={PlayerRanks.rank: result['rank'],
                                                             PlayerRanks.lp: result['lp'],
                                                             PlayerRanks.last_update: func.current_timestamp()}))
                        session.execute(stmt)
                        session.commit()

                        if Ranks[result['rank']] >= Ranks.EMERALDIV:
                            requests.put_nowait(Request(RequestType.GET_MATCH_LIST, riot_id=riot_id))
                    case RequestType.GET_MATCH_LIST:
                        for entry in result:
                            requests.put_nowait(Request(RequestType.GET_MATCH, id=entry))
                    case RequestType.GET_MATCH:
                        match_players = result.pop('players')

                        stmt = (insert(Matches)
                                .values(result)
                                .on_conflict_do_nothing())
                        rowcount = session.execute(stmt).rowcount
                        if rowcount == 0 or result['is_blue_win'] is None:
                            session.commit()
                            continue

                        for i in range(len(match_players)):
                            # Adds match info to players
                            match_players[i]['region'] = result['region']
                            match_players[i]['match_id'] = result['id']

                            # Player registry
                            stmt = (select(Players)
                                    .where(Players.riot_id == match_players[i]['puuid']))
                            df = pandas.read_sql(stmt, session.connection())

                            if len(df.index) == 0:
                                # TODO GET_PLAYER request and db registry
                                pass

                            # Champion regsitry
                            df = df_champions[df_champions['name'] == match_players[i]['champion_name']]
                            
                            if len(df.index) == 0:
                                stmt = (insert(Champions)
                                        .values({'name': match_players[i]['champion_name']}))
                                session.execute(stmt)
                                df_champions = pandas.read_sql(select(Champions), session.connection())
                                df = df_champions[df_champions['name'] == match_players[i]['champion_name']]
                            
                            match_players[i]['champion_name'].pop()
                            match_players[i]['champion_id'] = df['id'].first()
                        
                        stmt = (insert(MatchPlayers)
                                .values(match_players))
                        session.execute(stmt)
                        session.commit()
                        
                            





if __name__ == '__main__':
    main()
