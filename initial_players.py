import pandas

from datetime import datetime
from queue import Queue
from sqlalchemy import literal, select
from sqlalchemy.orm import Session

from db_models.registry import Players
from db_models.search import PlayerRanks

import logger

from constants import PLAYER_QUEUE_SIZE, RANK_COOLDOWN


def initial_players(session: Session) -> tuple[Queue[tuple[int, str]], set[str]]:
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
