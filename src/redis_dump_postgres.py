import contextlib
import datetime
import json
import os

from natsort import natsorted

with contextlib.suppress(ImportError):
    import dotenv

import psycopg2
import redis

with contextlib.suppress(NameError):
    dotenv.load_dotenv()

dv_redis = redis.Redis(
    host=os.environ["REDIS_DV_URL"],
    port=16704,
    username=os.environ["REDIS_USER"],
    password=os.environ["REDIS_DV_PASSWD"],
    decode_responses=True,
)

wfnm_redis = redis.Redis(
    host=os.environ["REDIS_WFNM_URL"],
    port=16062,
    username=os.environ["REDIS_USER"],
    password=os.environ["REDIS_WFNM_PASSWD"],
    decode_responses=True,
)

heroku_postgres = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
cur = heroku_postgres.cursor()

today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
time = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")

this_datetime = f"{today} {time}"

if os.getenv("TEST_ENV"):
    print("Running in test environment")
else:
    print("Running in production environment")
    print("This should be a scheduled job")

if not os.path.exists("db_dump"):
    os.mkdir("db_dump")

dv_dump_data = {}
print("Dumping DV data")
keys = dv_redis.keys("*")
for key in keys:
    key_type = dv_redis.type(key)
    if key_type == "ReJSON-RL":
        data: dict = dv_redis.json().get(key)

        # append data to dump_data
        dv_dump_data[key] = data

dv_dump_data = dict(natsorted(dv_dump_data.items()))
with open("db_dump/dv_dump_data.json", "w") as f:
    json.dump(dv_dump_data, f, indent=2)

wfnm_dump_data = {}
print("Dumping WFNM data")
keys = wfnm_redis.keys("*")
for key in keys:
    key_type = wfnm_redis.type(key)
    if key_type == "ReJSON-RL":
        data: dict = wfnm_redis.json().get(key)

        # append data to dump_data
        wfnm_dump_data[key] = data

wfnm_dump_data = dict(natsorted(wfnm_dump_data.items()))
with open("db_dump/wfnm_dump_data.json", "w") as f:
    json.dump(wfnm_dump_data, f, indent=2)

# create table if not exists
# create table name dv_dump_data with datetime and data column
'''
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS dv_dump_data (
        datetime timestamp,
        data text
    );
    """
)
# create table name wfnm_dump_data with datetime and data column
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS wfnm_dump_data (
        datetime timestamp,
        data text
    );
    """
)

heroku_postgres.commit()
'''

print("Dumping DV data to Postgres")
postgres_dv_data = json.dumps(dv_dump_data)
cur.execute(
    """
    INSERT INTO dv_dump_data (datetime, data)
    VALUES (%s, %s);
    """,
    (this_datetime, postgres_dv_data),
)
heroku_postgres.commit()

print("Dumping WFNM data to Postgres")
postgres_wfnm_data = json.dumps(wfnm_dump_data)
cur.execute(
    """
    INSERT INTO wfnm_dump_data (datetime, data)
    VALUES (%s, %s);
    """,
    (this_datetime, postgres_wfnm_data),
)
heroku_postgres.commit()


# if `dv_log` table row larger than 3000, truncate it
cur.execute(
    """
    SELECT COUNT(*) FROM dv_log;
    """
)
print("Counting rows in dv_log")

count = cur.fetchone()[0]
print(f"Count: {count}")

if count > 3000:
    print("Truncating dv_log")
    cur.execute(
        """
        TRUNCATE TABLE dv_log;
        """
    )
    heroku_postgres.commit()


# delete dv_dump_data longer than 1 month

print("Starting to auto delete dump data for longer than 1 month")

cur.execute(
    """
    DELETE FROM dv_dump_data WHERE datetime < (NOW() - INTERVAL '1 month');
    """
)
heroku_postgres.commit()

# delete wfnm_dump_data longer than 1 month
cur.execute(
    """
    DELETE FROM wfnm_dump_data WHERE datetime < (NOW() - INTERVAL '1 month');
    """
)
heroku_postgres.commit()

heroku_postgres.close()
