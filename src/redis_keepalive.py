"""Keeps the Redis DB active with read-only PING and GET. Separate from the website."""

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
        client.ping()
        # read-only: GET does not change the value or its TTL
        if key := client.randomkey():
            client.get(key)
        print(f"redis keepalive: ping + read ok (key: {key})", flush=True)
    except redis.RedisError as e:
        print(f"redis keepalive: ping/read failed: {e}", flush=True)
    time.sleep(INTERVAL)
