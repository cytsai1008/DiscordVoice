"""Keeps the Redis DB active with read-only PINGs. Separate from the website."""

import os
import time

import redis

INTERVAL = 3600  # seconds between pings

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
        print("redis keepalive: ping ok", flush=True)
    except redis.RedisError as e:
        print(f"redis keepalive: ping failed: {e}", flush=True)
    time.sleep(INTERVAL)
