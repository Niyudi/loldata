from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import executor
import logger
from constants import DB_URI


def main():
    logger.init()
    try:
        engine = create_engine(DB_URI)

        with Session(engine) as session:
            executor.run(session)
    except KeyboardInterrupt:
        logger.info('Terminated through keyboard interruption!')
    except Exception as e:
        logger.error(f'{type(e).__name__}: {str(e)}', on_console=False)
        raise e


if __name__ == '__main__':
    main()
