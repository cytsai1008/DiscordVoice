import re

import bs4
import requests
from discord.ext import commands

import src.modules.dv_tool_function as tool_function


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
        in tool_function.read_local_json("lang_list/languages.json")["Support_Language"]
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
        not in tool_function.read_local_json("lang_list/languages.json")[
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
