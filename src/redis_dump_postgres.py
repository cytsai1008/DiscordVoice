import json
import os

import dotenv
import psycopg2
import redis

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

with open("db_dump/wfnm_dump_data.json", "w") as f:
    json.dump(wfnm_dump_data, f, indent=2)

# create table if not exists
cur.execute("CREATE TABLE IF NOT EXISTS dv_dump_data (data TEXT);")
cur.execute("CREATE TABLE IF NOT EXISTS wfnm_dump_data (data TEXT);")
heroku_postgres.commit()

print("Dumping DV data to Postgres")
postgres_dv_data = json.dumps(dv_dump_data)
# clear old data
cur.execute("DELETE FROM dv_dump_data;")
cur.execute("INSERT INTO dv_dump_data (data) VALUES (%s)", (postgres_dv_data,))
heroku_postgres.commit()

print("Dumping WFNM data to Postgres")
postgres_wfnm_data = json.dumps(wfnm_dump_data)
# clear old data
cur.execute("DELETE FROM wfnm_dump_data;")
cur.execute("INSERT INTO wfnm_dump_data (data) VALUES (%s)", (postgres_wfnm_data,))
heroku_postgres.commit()

heroku_postgres.close()
