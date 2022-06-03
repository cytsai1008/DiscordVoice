import json
import os

import redis


# import load_command


def redis_client() -> redis.Redis:
    """Returns redis client"""
    return redis.Redis(
        host=os.environ["REDIS_DV_URL"],
        port=16704,
        username=os.environ["REDIS_USER"],
        password=os.environ["REDIS_DV_PASSWD"],
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


def write_json(filename: str, data: dict) -> None:
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


def id_check(self) -> str:
    try:
        server_id = str(self.guild.id)
    except Exception:
        server_id = f"user_{str(self.author.id)}"
    return server_id


def check_platform(
        user_platform_set: bool,
        user_id: [str, int],
        guild_platform_set: bool,
        guild_id: [str, int],
) -> str:
    user_id = f"user_{str(user_id)}"
    if user_platform_set and read_json(f"{user_id}")["platform"] == "Google":
        print("Init Google TTS API")
        return "Google"

    elif user_platform_set and read_json(f"{user_id}")["platform"] == "Azure":
        print("Init Azure TTS API")
        return "Azure"
    elif guild_platform_set and read_json(f"{guild_id}")["platform"] == "Google":
        print("Init Google TTS API")
        return "Google"
    elif guild_platform_set and read_json(f"{guild_id}")["platform"] == "Azure":
        print("Init Azure TTS API")
        return "Azure"
    elif not user_platform_set and not guild_platform_set:
        print("Init Google TTS API")
        return "Google"
    else:
        print(
            f"You found a bug\n"
            f"User platform: {user_platform_set}\n"
            f"User id: {user_id}\n"
            f"Guild platform: {guild_platform_set}\n"
            f"Guild id: {guild_id}\n"
        )
        return "Something wrong"


def del_json(filename) -> None:
    """Delete json value from redis (key: filename)"""
    redis_client().delete(filename)
