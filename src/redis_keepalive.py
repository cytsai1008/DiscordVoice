"""Keeps the Redis DB active with read-only GETs. Separate from the website."""

import os
import time

import redis

INTERVAL = 3600  # seconds between reads

client = redis.Redis(
    host=os.environ["REDIS_DV_URL"],
    port=16704,
    username=os.environ["REDIS_USER"],
    password=os.environ["REDIS_DV_PASSWD"],
    socket_timeout=10,
)

while True:
    try:
        # read-only: GET does not change the value or its TTL
        if key := client.randomkey():
            client.get(key)
        print(f"redis keepalive: read ok (key: {key})", flush=True)
    except redis.RedisError as e:
        print(f"redis keepalive: read failed: {e}", flush=True)
    time.sleep(INTERVAL)
