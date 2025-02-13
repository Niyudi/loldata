import pandas

from queue import Queue
from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.registry import Players
from db_models.search import PlayerRanks

import logger


def initial_players(session: Session, rank_cooldown: int = 2) -> Queue[str]:
    # First, try players that are registered but without a rank in database
    logger.info('Fetching from database players without a registered rank...')

    stmt = (select(Players.id, Players.riot_id)
            .join(PlayerRanks, Players.id == PlayerRanks.player_id, isouter=True)
            .where(PlayerRanks.rank.is_(None))
            .limit(5))
    df = pandas.read_sql(stmt, session.connection())

    if len(df.index) > 0:
        queue = Queue()
        df.apply(lambda row: queue.put_nowait((row['id'], row['riot_id'])), axis=1)

        logger.info(f'Fetched {queue.qsize()} players for initial search.')
        return queue
    
    # Second, try players who have not had their ranks checked in the last rank_cooldown days
    logger.info(f'Fetching from database players with ranks registered more than {rank_cooldown} days ago...')
    # TODO

    raise Exception('No intial player candidates available in database!')