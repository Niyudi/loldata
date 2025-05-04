from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas

from config import TARGET_PATCH


CALL_INTERVAL: timedelta = timedelta(seconds=0.6)
DEFAULT_RETRIES: int = 5
DEFAULT_RETRY_INTERVAL: float = 10 # in seconds
MATCH_BATCH_SIZE: int = 5
MAX_ERRORS_PER_WINDOW: int = 10
MAX_TIMEOUTS_PER_WINDOW: int = 5
PST_TIMEZONE: ZoneInfo = ZoneInfo('US/Pacific')
WINDOW_SIZE: int = 200

with open('keys/DB_URI', 'r') as file:
    DB_URI: str = file.read().strip()
with open('keys/RIOT_API_KEY', 'r') as file:
    RIOT_API_KEY: str = file.read().strip()

# Target patch logic
df_patch_history = pandas.read_csv('data/patch_history.csv')
df_patch_history['patch'] = df_patch_history['patch'].astype(int)
df_patch_history['date'] = df_patch_history['date'].apply(lambda x: int(datetime.strptime(x, '%Y-%m-%d').replace(tzinfo=PST_TIMEZONE).timestamp()))

curr_patch = df_patch_history.loc[df_patch_history['date'] < int(datetime.now().timestamp()), 'patch'].max()
if TARGET_PATCH is None:
    TARGET_PATCH = curr_patch
elif TARGET_PATCH > curr_patch:
    raise Exception('Target patch is greater than current patch!')

IS_FINISHED_PATCH: bool = False if curr_patch == TARGET_PATCH else True

patch_index = df_patch_history[df_patch_history['patch'] == TARGET_PATCH].index[0]

START_TIMESTAMP: int = int(df_patch_history.at[patch_index, 'date'])
END_TTIMESTAMP: int = int(df_patch_history.at[patch_index + 1, 'date'])

del curr_patch, df_patch_history, patch_index
