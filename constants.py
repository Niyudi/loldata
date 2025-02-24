from datetime import timedelta

CALL_INTERVAL: timedelta = timedelta(seconds=0.75)
DB_URI = 'postgresql://avnadmin:AVNS_O2iqSXw8Fkq1rn2Ycoc@pg-loldata-loldata.e.aivencloud.com:13374/defaultdb?sslmode=require'
DEFAULT_RETRY_INTERVAL: float = 10 # in seconds
DEFAULT_RETRIES: int = 3
MAX_TIMEOUTS: int = 5
RANK_COOLDOWN: timedelta = timedelta(days=3.0)

with open('RIOT_API_KEY', 'r') as file:
    RIOT_API_KEY: str = file.read().strip()
