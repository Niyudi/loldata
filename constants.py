from datetime import timedelta


##########
# CONFIG #
##########


TARGET_PATCH: int | None = None  # Patch within which search matches.


###################
# Other constants #
###################


CALL_INTERVAL: timedelta = timedelta(seconds=0.6)
DEFAULT_RETRIES: int = 5
DEFAULT_RETRY_INTERVAL: float = 10 # in seconds
MAX_ERRORS_PER_WINDOW: int = 10
MAX_TIMEOUTS_PER_WINDOW: int = 5
PLAYER_QUEUE_SIZE: int = 20
RANK_COOLDOWN: timedelta = timedelta(days=3.0)
WINDOW_SIZE: int = 200

with open('keys/DB_URI', 'r') as file:
    DB_URI: str = file.read().strip()
with open('keys/RIOT_API_KEY', 'r') as file:
    RIOT_API_KEY: str = file.read().strip()
