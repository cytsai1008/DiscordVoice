import datetime
import json
import os

import psycopg2
import redis


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


def read_db_json(filename) -> dict:
    """Reads json value from redis (key: filename, value: data)"""
    client = redis_client()
    return client.json().get(filename)


def read_local_json(filename) -> dict | list:
    """Returns dictionary from a json file"""
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def write_db_json(filename: str, data: dict) -> None:
    """Writes dictionary to redis json (key: filename, value: data)"""
    redis_client().json().set(filename, ".", data)
    # return False if args is type(None)


def write_local_json(filename: str, data: dict | list) -> None:
    """Writes dictionary to json file"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def check_dict_data(data: dict, arg) -> bool:
    """Check if arg is in data"""
    try:
        postgres_logging(f"data in {arg} is {data[arg]}")
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


def get_translate_lang(lang: str, locale_dict: dict) -> str:
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
    lang = get_translate_lang(lang, locale_dict)
    a = "".join(locale_dict[lang][msg_type][command][name])
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
