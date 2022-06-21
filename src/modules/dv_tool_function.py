import json
import os
import re

import bs4
# import mechanize
import redis
import requests


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


def read_db_json(filename) -> dict:
    """Reads json value from redis (key: filename, value: data)"""
    client = redis_client()
    return client.json().get(filename)


def read_file_json(filename) -> dict:
    """Returns dictionary from a json file"""
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def write_db_json(filename: str, data: dict) -> None:
    """Writes dictionary to redis json (key: filename, value: data)"""
    redis_client().json().set(filename, ".", data)
    # return False if args is type(None)


def write_file_json(filename: str, data: dict) -> None:
    """Writes dictionary to json file"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def check_dict_data(data: dict, arg) -> bool:
    """Check if arg is in data"""
    try:
        print(f"data in {arg} is {data[arg]}")
    except KeyError:
        return False
    else:
        return True


def check_db_file(filename) -> bool:
    """Check if filename exist in redis key"""
    return bool(redis_client().exists(filename))


def check_file_file(filename) -> bool:
    """Check if filename exist in file"""
    return os.path.isfile(filename)


"""
def lang_command(lang: str, command: str) -> str:
    try:
        command_out = load_command.read_description(lang, command)
    except FileNotFoundError:
        command_out = load_command.read_description("en", command)
    finally:
        return command_out
"""


def get_id(self) -> str:
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


def check_platform(
    user_platform_set: bool,
    user_id: [str, int],
    guild_platform_set: bool,
    guild_id: [str, int],
    lang: str,
) -> str:
    """Return the platform of the user or guild (default: Google)"""
    if (
        lang in read_file_json("lang_list/languages.json")["Support_Language"]
        and lang
        not in read_file_json("lang_list/azure_languages.json")["Support_Language"]
    ):
        return "Google"
    if (
        lang in read_file_json("lang_list/azure_languages.json")["Support_Language"]
        and lang not in read_file_json("lang_list/languages.json")["Support_Language"]
    ):
        return "Azure"
    user_id = f"user_{str(user_id)}"
    if (
        user_platform_set
        and read_db_json("user_config")[user_id]["platform"] == "Google"
    ):
        print("Init Google TTS API 1")
        return "Google"

    elif (
        user_platform_set
        and read_db_json("user_config")[user_id]["platform"] == "Azure"
    ):
        print("Init Azure TTS API 1")
        return "Azure"
    elif guild_platform_set and read_db_json(f"{guild_id}")["platform"] == "Google":
        print("Init Google TTS API 2")
        return "Google"
    elif guild_platform_set and read_db_json(f"{guild_id}")["platform"] == "Azure":
        print("Init Azure TTS API 2")
        return "Azure"
    elif not user_platform_set and not guild_platform_set:
        print("Init Google TTS API 3")
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
    convert_text: [list, None],
) -> str:
    """
    Convert message from locale\n
    ex.\n
    ```
    convert_msg(locale, 'en','variable', 'help', 'channel_msg_default', ['prefix', config['prefix'], 'sys_channel', guild_system_channel.id])```\n
    ```convert_msg(locale, 'en', 'command', 'say', 'say_queue_not_support', None)```
    """
    lang = get_translate_lang(lang, locale_dict)
    a = "".join(locale_dict[lang][msg_type][command][name])
    if convert_text is not None:
        for i in range(0, len(convert_text), 2):
            a = a.replace(f"{{{{{convert_text[i]}}}}}", f"{convert_text[i + 1]}")
        return a
    return a


def get_lang_in_db(self) -> str:
    """Return the language of the user or guild (default: en)"""
    return (
        read_db_json(get_id(self))["lang"]
        if (
            check_guild_or_dm(self)
            and check_db_file(get_id(self))
            and check_dict_data(read_db_json(get_id(self)), "lang")
        )
        else "en"
    )


def fetch_link_head(content: str, lang, locale: dict) -> str:
    """Return the head in the link if content has links"""

    # clear localhost 0.0.0.0 127.0.0.1
    local_list = [
        re.findall("(https?://127.0.0.1:\d{1,5}/?[^ ]+)", content),
        re.findall("(https?://localhost:\d{1,5}/?[^ ]+)", content, flags=re.IGNORECASE),
        re.findall("(https?://0.0.0.0:\d{1,5}/?[^ ]+)", content),
    ]

    for i in local_list:
        for j in i:
            content = content.replace(j, "")

    if not re.findall(
        "(https?://(?:www\.|(?!www))[a-zA-Z\d][a-zA-Z\d-]+[a-zA-Z\d]\.\S{2,}|www\.[a-zA-Z\d][a-zA-Z\d-]+[a-zA-Z\d]\.\S{2,}|https?://(?:www\.|(?!www))[a-zA-Z\d]+\.\S{2,}|www\.[a-zA-Z\d]+\.\S{2,})",
        content,
        flags=re.IGNORECASE,
    ):
        return content

    url = re.findall(
        "(https?://(?:www\.|(?!www))[a-zA-Z\d][a-zA-Z\d-]+[a-zA-Z\d]\.\S{2,}|www\.[a-zA-Z\d][a-zA-Z\d-]+[a-zA-Z\d]\.\S{2,}|https?://(?:www\.|(?!www))[a-zA-Z\d]+\.\S{2,}|www\.[a-zA-Z\d]+\.\S{2,})",
        content,
        flags=re.IGNORECASE,
    )
    if len(url) <= 3:
        for i in url:
            headers = {'user-agent': "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
            try:
                r = requests.get(i, headers=headers)
                soup = bs4.BeautifulSoup(r.text, "lxml")
                title = soup.title.text
            except Exception:
                content = content.replace(i, "")
            else:
                convert_text = convert_msg(
                    locale,
                    lang,
                    "variable",
                    "say",
                    "link",
                    [
                        "data_link",
                        title,
                    ],
                )
                content = content.replace(i, convert_text)

    else:
        for i in url:
            content = content.replace(i, "")

    return content
