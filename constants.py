from datetime import timedelta

CALL_INTERVAL: timedelta = timedelta(seconds=0.6)
DB_URI = 'postgresql://avnadmin:AVNS_O2iqSXw8Fkq1rn2Ycoc@pg-loldata-loldata.e.aivencloud.com:13374/defaultdb?sslmode=require'
DEFAULT_RETRY_INTERVAL: float = 10 # in seconds
DEFAULT_RETRIES: int = 3
MAX_TIMEOUTS_PER_WINDOW: int = 3
RANK_COOLDOWN: timedelta = timedelta(days=3.0)
TIMEOUT_WINDOW_SIZE: int = 200

with open('RIOT_API_KEY', 'r') as file:
    RIOT_API_KEY: str = file.read().strip()
