from queue import Queue
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from db_models.search import PlayerRanks
from db_models.static import Ranks

from initial_players import initial_players
from request_handler import handle_request, Request, RequestType


def main():
    engine = create_engine('postgresql://postgres:1408@localhost:5432/postgres')

    with Session(engine) as session:
        players: Queue[str] = initial_players(session)
        requests: Queue[Request] = Queue()

        while players.qsize() > 0:
            player_id = players.get_nowait()
            requests.put_nowait(Request(RequestType.GET_RANK, id=player_id))
            while requests.qsize() > 0:
                request = requests.get_nowait()
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

                        if result['rank'] >= Ranks.EMERALDIV:
                            requests.put_nowait(Request(RequestType.GET_MATCH_LIST, id=player_id))
                    case RequestType.GET_MATCH_LIST:
                        for entry in result:
                            requests.put_nowait(Request(RequestType.GET_MATCH, id=entry))
                    case RequestType.GET_MATCH:
                        pass


if __name__ == '__main__':
    main()
