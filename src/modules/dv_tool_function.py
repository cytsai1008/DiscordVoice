import asyncio
import contextlib
import datetime
import json
import os
import traceback

import psycopg2
import redis
from natsort import natsorted


def postgres_logging(logging_data: str):
    """Logging to postgres"""
    heroku_postgres = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
    cur = heroku_postgres.cursor()
    today_datetime = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    print(f"{today_datetime}: {logging_data}")
    if os.getenv("TEST_ENV"):
        return

    cur.execute(
        """
        INSERT INTO dv_log (datetime, log)
        VALUES (%s, %s);
        """,
        (today_datetime, logging_data),
    )
    heroku_postgres.commit()
    heroku_postgres.close()


def redis_client() -> redis.Redis:
    """Returns redis client"""
    return redis.Redis(
        host=os.environ["REDIS_DV_URL"],
        port=16704,
        username=os.environ["REDIS_USER"],
        password=os.environ["REDIS_DV_PASSWD"],
        decode_responses=True,
    )


def read_db_json(filename, path: str = ".") -> dict:
    """Reads json value from redis (key: filename, value: data)"""
    client = redis_client()
    return client.json().get(filename, path)


def read_local_json(filename) -> dict | list:
    """Returns dictionary from a json file"""
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def write_db_json(
    filename: str, data: dict, path: str = ".", ttl: int | None = None
) -> None:
    """Writes dictionary to redis json (key: filename, value: data)"""
    with contextlib.suppress(Exception):
        data = dict(natsorted(data.items()))
    redis_client().json().set(filename, path, data)
    if ttl:
        redis_client().expire(filename, ttl)


def write_local_json(filename: str, data: dict | list) -> None:
    """Writes dictionary to json file"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def check_dict_data(data: dict, arg) -> bool:
    """Check if arg is in data"""
    try:
        # postgres_logging(f"data in {arg} is {data[arg]}")
        _ = data[arg]
    except KeyError:
        return False
    else:
        return True


def check_db_file(filename) -> bool:
    """Check if filename exist in redis key"""
    return bool(redis_client().exists(filename))


def check_local_file(filename) -> bool:
    """Check if filename exist in file"""
    return os.path.isfile(filename)


def user_id_rename(self) -> str:
    """Return the id of the user or guild (user id start with `user_`)"""
    try:
        server_id = str(self.guild.id)
    except Exception:
        server_id = f"user_{str(self.author.id)}"
    return server_id


def check_guild_or_dm(self) -> bool:
    """Return if this is a guild or a DM"""
    try:
        _ = str(self.guild.id)
    except Exception:
        _ = f"user_{str(self.author.id)}"
        return False
    else:
        return True


def del_db_json(filename) -> None:
    """Delete json value from redis (key: filename)"""
    redis_client().delete(filename)


def _get_translate_lang(lang: str, locale_dict: dict) -> str:
    """Return i if lang is in locale_dict["lang_list"][i]"""
    for i in locale_dict["lang_list"]:
        for j in locale_dict["lang_list"][i]:
            if lang == j:
                return i
    return "en"


def convert_msg(
    locale_dict: dict,
    lang: str,
    msg_type: str,
    command: str,
    name: str,
    convert_text: list | None = None,
) -> str:
    """
    Convert message from locale
    """
    lang = _get_translate_lang(lang, locale_dict)
    a = "".join(locale_dict[msg_type][command][name][lang])
    if convert_text is not None:
        for i in range(0, len(convert_text), 2):
            a = a.replace(f"{{{{{convert_text[i]}}}}}", f"{convert_text[i + 1]}")
        return a
    return a


def check_db_lang(self) -> str:
    """Return the language of the user or guild (default: en)"""
    return (
        read_db_json(user_id_rename(self))["lang"]
        if (
            check_guild_or_dm(self)
            and check_db_file(user_id_rename(self))
            and check_dict_data(read_db_json(user_id_rename(self)), "lang")
        )
        else "en"
    )


async def auto_reconnect_vc(bot) -> str:
    """Reconnect to voice channel on reboot"""
    joined_vc = read_db_json("joined_vc")
    postgres_logging(f"joined_vc: \n" f"{joined_vc}")
    tasks = [
        _connect_vc(bot, server_id, channel_id)
        for server_id, channel_id in joined_vc.items()
    ]

    results = await asyncio.gather(*tasks)
    remove_vc = [result[1] for result in results if result[0] is False]
    # remove vc from `joined_vc` if failed to join and written into db
    for i in remove_vc:
        with contextlib.suppress(KeyError):
            del joined_vc[i]
        write_db_json("joined_vc", joined_vc)
    channel_list = "".join(f"{i}: {j}\n" for i, j in joined_vc.items())
    channel_list = f"```\n" f"{channel_list}\n" f"```"
    if remove_vc:
        new_line = "\n"
        channel_list += (
            f"Fail to connect to the following channels:\n```\n"
            f"{new_line.join(remove_vc)}\n"
            f"```"
        )
    return channel_list


async def _connect_vc(bot, server_id: int, channel_id: int) -> (bool, int | None):
    """Connect to voice channel"""
    try:
        # noinspection PyUnresolvedReferences
        await bot.get_channel(channel_id).connect()
    except Exception:
        postgres_logging(f"Failed to connect to {channel_id}.\n")
        postgres_logging(f"Reason: \n{traceback.format_exc()}")
        return False, server_id
    else:
        postgres_logging(f"Successfully connected to {channel_id}.\n")
        return True, None
