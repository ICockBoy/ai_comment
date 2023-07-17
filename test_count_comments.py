import dbm
import datetime


cache = dbm.open('comments_cache/comments_cache', 'c')

now = datetime.datetime.now()
start_day = datetime.datetime(
    year=now.year,
    month=now.month,
    day=now.day,
    hour=0,
    minute=0
)

start_day_dt = int(start_day.timestamp())

comments_today = []

for key in cache.keys():

    key = key.decode()

    owner_id, channel_id, timestamp = key.split('|')

    if start_day_dt < int(timestamp):
        comments_today.append(channel_id)

print(len(comments_today))