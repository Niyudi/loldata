import pandas

from queue import Queue
from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.registry import Players
from db_models.search import PlayerRanks


def initial_players(session: Session, rank_cooldown: int = 3) -> Queue[str]:
    # First, try players that are registered but without a rank in database
    stmt = (select(Players.id)
            .join(PlayerRanks, Players.id == PlayerRanks.player_id, isouter=True)
            .where(PlayerRanks.rank.is_(None))
            .limit(5))
    df = pandas.read_sql(stmt, session.connection())

    if len(df.index) > 0:
        queue = Queue()
        df['id'].apply(queue.put_nowait)
        return queue
    
    # Second, try players who have not had their ranks checked in the last rank_cooldown days
    # TODO

    raise Exception('No intial player candidates available in database!')