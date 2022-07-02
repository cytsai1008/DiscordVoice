import datetime
import re
import time

import bs4
import requests
from discord.ext import commands

import src.modules.dv_tool_function as tool_function
from src.modules import tts_func


async def content_convert(ctx, lang: str, locale: dict, content: str) -> str:
    content = await commands.clean_content(
        fix_channel_mentions=True, use_nicknames=True
    ).convert(ctx, content)

    # Emoji Replace
    if re.findall("<a?:[^:]+:\d+>", content):
        emoji_id = re.findall("<a?:[^:]+:\d+>", content)
        emoji_text = re.findall("<a?:([^:]+):\d+>", content)
        for i in range(len(emoji_id)):
            content = content.replace(
                emoji_id[i],
                tool_function.convert_msg(
                    locale,
                    lang,
                    "variable",
                    "say",
                    "emoji",
                    ["data_emoji", emoji_text[i]],
                ),
            )

    content = content_link_replace(content, lang, locale)
    return content


def content_link_replace(content: str, lang, locale: dict) -> str:
    """Return the head in the link if content has links"""

    # clear localhost 0.0.0.0 127.0.0.1
    local_list = [
        re.findall("(https?://127.0.0.1:\d{1,5}/?[^ ]+)", content),
        re.findall("(localhost:\d{1,5}/?[^ ]+)", content, flags=re.IGNORECASE),
        re.findall("(https?://0.0.0.0:\d{1,5}/?[^ ]+)", content),
        re.findall("(127.0.0.1:\d{1,5}/?[^ ]+)", content),
        re.findall("(0.0.0.1:\d{1,5}/?[^ ]+)", content),
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
            headers = {
                "user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
            }
            try:
                r = requests.get(i, headers=headers)
                soup = bs4.BeautifulSoup(r.text, "lxml")
                title = soup.title.text
            except Exception:
                content = content.replace(i, "")
            else:
                convert_text = tool_function.convert_msg(
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


def check_platform(
    user_platform_set: bool,
    user_id: [str, int],
    guild_platform_set: bool,
    guild_id: [str, int],
    lang: str,
) -> str:
    """Return the platform of the user or guild (default: Google)"""
    if (
        lang
        in tool_function.read_local_json("lang_list/google_languages.json")[
            "Support_Language"
        ]
        and lang
        not in tool_function.read_local_json("lang_list/azure_languages.json")[
            "Support_Language"
        ]
    ):
        return "Google"
    if (
        lang
        in tool_function.read_local_json("lang_list/azure_languages.json")[
            "Support_Language"
        ]
        and lang
        not in tool_function.read_local_json("lang_list/google_languages.json")[
            "Support_Language"
        ]
    ):
        return "Azure"
    user_id = f"user_{str(user_id)}"
    if (
        user_platform_set
        and tool_function.read_db_json("user_config")[user_id]["platform"] == "Google"
    ):
        tool_function.postgres_logging("Init Google TTS API 1")
        return "Google"

    elif (
        user_platform_set
        and tool_function.read_db_json("user_config")[user_id]["platform"] == "Azure"
    ):
        tool_function.postgres_logging("Init Azure TTS API 1")
        return "Azure"
    elif (
        guild_platform_set
        and tool_function.read_db_json(f"{guild_id}")["platform"] == "Google"
    ):
        tool_function.postgres_logging("Init Google TTS API 2")
        return "Google"
    elif (
        guild_platform_set
        and tool_function.read_db_json(f"{guild_id}")["platform"] == "Azure"
    ):
        tool_function.postgres_logging("Init Azure TTS API 2")
        return "Azure"
    elif not user_platform_set and not guild_platform_set:
        tool_function.postgres_logging("Init Google TTS API 3")
        return "Google"
    else:
        tool_function.postgres_logging(
            f"You found a bug\n"
            f"User platform: {user_platform_set}\n"
            f"User id: {user_id}\n"
            f"Guild platform: {guild_platform_set}\n"
            f"Guild id: {guild_id}\n"
        )
        return "Something wrong"


def name_convert(ctx, lang: str, locale: dict, content: str) -> str:
    user_id = ctx.author.id
    guild_id = ctx.guild.id

    try:
        username = ctx.author.display_name
    except AttributeError:
        username = ctx.author.name
    # get username length
    no_name = False
    send_time = int(
        time.mktime(datetime.datetime.now(datetime.timezone.utc).timetuple())
    )
    if tool_function.check_local_file(f"msg_temp/{guild_id}.json"):
        old_msg_temp = tool_function.read_local_json(f"msg_temp/{guild_id}.json")
        if old_msg_temp["1"] == user_id and send_time - int(old_msg_temp["0"]) <= 15:
            no_name = True
    id_too_long = False
    if len(username) > 20:
        if len(ctx.author.name) > 20:
            id_too_long = True
        else:
            username = ctx.author.name

    if id_too_long:
        username = tool_function.convert_msg(
            locale,
            lang,
            "variable",
            "say",
            "someone_name",
            None,
        )
        if ctx.author.voice is not None:
            content = tool_function.convert_msg(
                locale,
                lang,
                "variable",
                "say",
                "inside_said",
                [
                    "user",
                    username,
                    "data_content",
                    content,
                ],
            )
        else:
            content = tool_function.convert_msg(
                locale,
                lang,
                "variable",
                "say",
                "outside_said",
                [
                    "user",
                    username,
                    "data_content",
                    content,
                ],
            )
    elif not no_name:
        content = (
            tool_function.convert_msg(
                locale,
                lang,
                "variable",
                "say",
                "inside_said",
                [
                    "user",
                    username,
                    "data_content",
                    content,
                ],
            )
            if ctx.author.voice is not None
            else tool_function.convert_msg(
                locale,
                lang,
                "variable",
                "say",
                "outside_said",
                [
                    "user",
                    username,
                    "data_content",
                    content,
                ],
            )
        )
    else:
        content = content
    return content


async def tts_convert(ctx, lang: str, content: str, platform_result: str) -> [bool]:
    guild_id = ctx.guild.id
    if platform_result == "Azure":
        tool_function.postgres_logging("Init Azure TTS API")
        await tts_func.azure_tts_converter(content, lang, f"{guild_id}.mp3")
        return True

    elif platform_result == "Google":
        tool_function.postgres_logging("Init Google TTS API")
        await tts_func.google_tts_converter(content, lang, f"{guild_id}.mp3")
        return True

    else:
        tool_function.postgres_logging("Something Wrong")
        # send to owner
        await tts_func.google_tts_converter(content, lang, f"{guild_id}.mp3")
        return False
