from datetime import timedelta

CALL_INTERVAL: timedelta = timedelta(seconds=1.0)
DB_URI = 'postgresql://avnadmin:AVNS_O2iqSXw8Fkq1rn2Ycoc@pg-loldata-loldata.e.aivencloud.com:13374/defaultdb?sslmode=require'
DEFAULT_RETRY_INTERVAL: float = 10 # in seconds
DEFAULT_RETRIES: int = 3
MAX_TIMEOUTS: int = 5
RIOT_API_KEY: str = 'RGAPI-bbacd277-c8a6-4d8d-b0dc-d76e982e5a77'
