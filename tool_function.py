import json
import os

import redis


# import load_command


def redis_client() -> redis.Redis:
    """Returns redis client"""
    return redis.Redis(
        host=os.environ["REDIS_URL"],
        port=16704,
        username=os.environ["REDIS_USER"],
        password=os.environ["REDIS_PASSWD"],
        decode_responses=True,
    )


def read_json(filename) -> dict:
    """Reads json value from redis (key: filename, value: data)"""
    client = redis_client()
    return client.json().get(filename)


def new_read_json(filename) -> dict:
    """Returns dictionary from a json file"""
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def write_json(filename, data) -> None:
    """Writes dictionary to redis json (key: filename, value: data)"""
    redis_client().json().set(filename, ".", data)
    # return False if args is type(None)


def check_dict_data(data: dict, arg) -> bool:
    """Check if arg is in data"""
    try:
        print(f"data in {arg} is {data[arg]}")
    except KeyError:
        return False
    else:
        return True


def check_file(filename) -> bool:
    """Check if filename exist in redis key"""
    return bool(redis_client().exists(filename))


"""
def lang_command(lang: str, command: str) -> str:
    try:
        command_out = load_command.read_description(lang, command)
    except FileNotFoundError:
        command_out = load_command.read_description("en", command)
    finally:
        return command_out
"""
