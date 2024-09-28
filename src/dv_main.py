import asyncio
import contextlib
import datetime
import os
import re
import shutil
import signal
import subprocess
import time
import traceback

import discord
import discord.ext.commands
from discord.ext import commands

with contextlib.suppress(ImportError):
    import dotenv

import src.modules.dv_command_func as command_func
import src.modules.dv_tool_function as tool_function

# avoid wrong work dir
if "src" in os.getcwd():
    os.chdir("../")

# create temporary directory
tmp_dirs = ["tts_temp", "msg_temp", "queue_temp"]

for dirs in tmp_dirs:
    if not os.path.exists(dirs):
        os.mkdir(dirs)

# loading env from testenv
with contextlib.suppress(NameError):
    dotenv.load_dotenv()

# setup variables
config = {
    "prefix": f"{os.getenv('DISCORD_DV_PREFIX')}",
    "owner": int(os.getenv("DISCORD_OWNER")),
}

# setup command aliases
command_alias = {
    "help": ["h"],
    "join": ["j"],
    "leave": ["l", "dc", "disconnect"],
    "say": ["s"],
    "clear": ["c"],
    "move": ["m"],
    "say_lang": ["sl", "saylang", "say-lang"],
    "force_say": ["fs", "forcesay", "force-say"],
    "gpt_say": ["gs", "gptsay", "gpt-say", "gpt", "gemini-say", "gemini_say", "gemini", "geminisay"],
}

# setup global variables
LOCALE = tool_function.read_local_json("locale/dv_locale/locale_v2.json")
supported_platform = ("Google", "Azure")

# initialize bot
intents = discord.Intents.all()
intents.members = False
intents.presences = False

bot = commands.Bot(
    command_prefix=config["prefix"],
    help_command=None,
    case_insensitive=True,
    owner_ids=[
        config["owner"],
        890234177767755849,
        1089569346516439123,
        853578469979848714,
    ],
    intents=intents,
)

# remove default help command for more flexible help command
bot.remove_command("help")


# clear tts folder's old file
def clear_old_file(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")


clear_old_file("tts_temp")


# Queue job function WIP
async def queue_job(ctx, lang: str, content: str, platform: str):
    # TODO: Queue todo
    # read queue file
    """
    guild_id = ctx.guild.id
    if tool_function.check_local_file(f"queue_temp/{guild_id}.json"):
        queue: list = tool_function.read_local_json(f"queue_temp/{guild_id}.json")
    else:
        queue = []
    queue.append({"lang": lang, "content": content, "platform": platform})
    tool_function.write_local_json(f"queue_temp/{guild_id}.json", queue)

    # get voice_client from ctx
    voice_client = ctx.voice_client
    if voice_client is None:
        os.remove(f"queue_temp/{guild_id}.json")
        return
    # check if voice_client is playing
    if voice_client.is_playing():
        # wait until voice_client is not playing by asyncio
        wait_task = asyncio.create_task(check_is_not_playing(ctx))
        await wait_task
    # reload queue file
    # todo: WIP
    """
    return


async def check_is_not_playing(ctx):
    while True:
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            await asyncio.sleep(0.2)
        else:
            break


@bot.event
# setup jobs on ready
async def on_ready():
    await tool_function.postgres_logging(f"Login as: {bot.user}")
    game = discord.Game(f"{config['prefix']}help")
    channel_list = ""

    # reconnect vc in "joined_vc" if not TEST_ENV
    if tool_function.check_db_file("joined_vc") and os.getenv("TEST_ENV") != "True":
        """
        #TODO: Fix it
        channel_list = await tool_function.auto_reconnect_vc(bot)
        """

    # connect to test server's vc (Internal Debug Usage)
    else:
        # noinspection PyUnresolvedReferences
        await bot.get_channel(928686912477216811).connect()
    await bot.change_presence(status=discord.Status.online, activity=game)

    # send result to owner
    owner = await bot.fetch_user(int(config["owner"]))
    await owner.send("bot online.\n" "Connect to:\n" f"{channel_list}")


@bot.event
# send server join welcome message
async def on_guild_join(guild):
    general = guild.system_channel
    if general and general.permissions_for(guild.me).send_messages:
        owner_data = await bot.fetch_user(config["owner"])
        owner_name = owner_data.name
        owner_discriminator = owner_data.discriminator
        if str(owner_discriminator) != "0":
            owner_full_id = f"{owner_name}#{owner_discriminator}"
        else:
            owner_full_id = f"@{owner_name}"
        await general.send(
            "Thanks for adding me!\n"
            f"Please set a channel by `{config['prefix']}setchannel`. (ex. {config['prefix']}setchannel <#{general.id}>)\n"
            f"Please set a language by `{config['prefix']}setlang`. (ex. `{config['prefix']}setlang en-us`)\n"
            f"To speak something, please use `{config['prefix']}say`. (ex. `{config['prefix']}say ABCD`)\n"
            f"To join a voice channel, please use `{config['prefix']}join`.\n"
            f"To leave a voice channel, please use `{config['prefix']}leave`.\n"
            f"For more information, please type `{config['prefix']}help`.\n"
            f"If you're facing any problem, please contact `{owner_full_id}`.\n"
            f"繁體中文使用說明請先`{config['prefix']}setlang zh-tw`後輸入`{config['prefix']}help`\n"
            f"简体中文使用说明请先`{config['prefix']}setlang zh-cn`后输入`{config['prefix']}help`"
        )
    # get guild name
    guild_name = guild.name
    guild_id = guild.id
    # send about new server to owner
    owner = await bot.fetch_user(int(config["owner"]))
    await owner.send(f"New server joined!\n" f"Guild Name: {guild_name}\n" f"Guild ID: {guild_id}\n")


@bot.event
# exception handling
async def on_command_error(ctx, error):  # sourcery no-metrics skip: remove-pass-elif
    # sourcery skip: low-code-quality, remove-pass-elif
    lang = tool_function.check_db_lang(ctx)
    command = ctx.invoked_with.lower()

    match error:
        # CommandNotFound or NotOwner
        case discord.ext.commands.errors.CommandNotFound() | discord.ext.commands.errors.NotOwner():
            await ctx.reply(
                tool_function.convert_msg(LOCALE, lang, "command", "on_command_error", "command_not_found", None)
            )
            await ctx.message.add_reaction("❌")
            return

        # UserMissingPermissions
        case discord.ext.commands.errors.MissingPermissions():
            await ctx.reply(
                tool_function.convert_msg(LOCALE, lang, "command", "on_command_error", "missing_permissions", None)
            )
            await ctx.message.add_reaction("❌")
            return

        # MissingRequiredArgument
        case discord.ext.commands.errors.MissingRequiredArgument():
            # Only add question emoji if exception really have problem (ex. join command no argument will join by user channel)
            wrong_cmd = True

            match command:
                case "setchannel":
                    guild_system_channel = ctx.guild.system_channel
                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "setchannel",
                            "setchannel_no_arg",
                            [
                                "prefix",
                                config["prefix"],
                                "sys_channel",
                                guild_system_channel.id,
                            ],
                        )
                    )

                case "setlang":
                    support_lang = tool_function.read_local_json("lang_list/google_languages.json")
                    azure_lang = tool_function.read_local_json("lang_list/azure_languages.json")

                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "setlang",
                            "setlang_no_arg",
                            [
                                "prefix",
                                config["prefix"],
                                "google_lang_list",
                                ", ".join(support_lang["Support_Language"]),
                                "azure_lang_list",
                                ", ".join(azure_lang["Support_Language"]),
                            ],
                        )
                    )

                case "say" | _ if command in command_alias["say"]:
                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "say",
                            "say_no_arg",
                            None,
                        )
                    )

                case "say_lang" | _ if command in command_alias["say_lang"]:
                    support_lang = tool_function.read_local_json("lang_list/google_languages.json")
                    azure_lang = tool_function.read_local_json("lang_list/azure_languages.json")

                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "say_lang",
                            "say_lang_no_arg",
                            [
                                "prefix",
                                config["prefix"],
                                "google_lang_list",
                                ", ".join(support_lang["Support_Language"]),
                                "azure_lang_list",
                                ", ".join(azure_lang["Support_Language"]),
                            ],
                        )
                    )

                case "setvoice":
                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "setvoice",
                            "setvoice_no_arg",
                            [
                                "prefix",
                                config["prefix"],
                                "data_support_platform",
                                ", ".join(list(supported_platform)),
                            ],
                        )
                    )

                case "join" | _ if command in command_alias["join"]:
                    try:
                        user_voice_channel = ctx.author.voice.channel
                    except AttributeError:
                        await ctx.reply(
                            tool_function.convert_msg(
                                LOCALE,
                                lang,
                                "command",
                                "join",
                                "join_not_in",
                                None,
                            )
                        )
                        await ctx.message.add_reaction("❌")
                        return
                    # trying to connect to vc
                    else:
                        join_cmd = bot.get_command("join")
                        await ctx.invoke(join_cmd, channel=user_voice_channel)
                        return

                case "move" | _ if command in command_alias["move"]:
                    # read "joined_vc" to del the old vc id
                    joined_vc = tool_function.read_db_json("joined_vc")
                    # trying to del the old vc id
                    with contextlib.suppress(KeyError):
                        del joined_vc[str(ctx.guild.id)]

                    # get if user is in vc or not
                    try:
                        user_voice_channel = ctx.author.voice.channel
                    except AttributeError:
                        await ctx.reply(
                            tool_function.convert_msg(
                                LOCALE,
                                lang,
                                "command",
                                "move",
                                "move_not_in",
                                None,
                            )
                        )
                        await ctx.message.add_reaction("❌")
                        return
                    else:
                        move_cmd = bot.get_command("move")
                        await ctx.invoke(move_cmd, channel=user_voice_channel)
                        return

                case "ban":
                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "ban",
                            "ban_no_arg",
                            [
                                "prefix",
                                config["prefix"],
                            ],
                        )
                    )

                case "unban":
                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "unban",
                            "unban_no_arg",
                            [
                                "prefix",
                                config["prefix"],
                            ],
                        )
                    )

                case "set_nochannel":
                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "set_nochannel",
                            "set_nochannel_no_arg",
                            [
                                "prefix",
                                config["prefix"],
                            ],
                        )
                    )

                case "wrong_msg":
                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "wrong_msg",
                            "wrong_msg_bad_arg",
                            [
                                "prefix",
                                config["prefix"],
                            ],
                        )
                    )

                case "set_noname":
                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "no_name",
                            "no_name_bad_arg",
                            [
                                "prefix",
                                config["prefix"],
                            ],
                        )
                    )

                case _:
                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "on_command_error",
                            "missing_required_argument",
                            None,
                        )
                    )

            if wrong_cmd:
                await ctx.message.add_reaction("❓")
            return

        case discord.ext.commands.errors.CommandOnCooldown():
            await ctx.reply(
                tool_function.convert_msg(
                    LOCALE,
                    lang,
                    "command",
                    "on_command_error",
                    "command_on_cooldown",
                    [
                        "cooldown_time",
                        str(round(error.retry_after)),
                    ],
                )
            )
            await ctx.message.add_reaction("⏳")
            return

        # Commands that use channel as type of argument may raise this error, but I already defined by error function
        case discord.ext.commands.errors.ChannelNotFound() if command in [
            "setchannel",
            "join",
            "move",
        ] or command in command_alias["join"] or command in command_alias["move"]:
            return

        # limited some commands to only be used in guilds because it wasn't designed to be used in DMs, group messages WIP
        # (May never work because I'm lazy)
        # (Imagine you're calling to a robot just to hear the robot voice)

        # NoPrivateMessage
        case discord.ext.commands.errors.NoPrivateMessage():
            await ctx.reply(
                tool_function.convert_msg(
                    LOCALE,
                    lang,
                    "command",
                    "on_command_error",
                    "no_private_message",
                    None,
                )
            )
            await ctx.message.add_reaction("❌")
            return

        # Seems nerver been used, but still keep it just in case
        # TooManyArguments
        case discord.ext.commands.errors.TooManyArguments():
            await ctx.reply(
                tool_function.convert_msg(
                    LOCALE,
                    lang,
                    "command",
                    "on_command_error",
                    "too_many_arguments",
                    None,
                )
            )
            await ctx.message.add_reaction("❌")
            return

        # BotMissingPermissions
        case discord.ext.commands.errors.BotMissingPermissions():
            await ctx.author.send(
                tool_function.convert_msg(
                    LOCALE,
                    lang,
                    "command",
                    "on_command_error",
                    "bot_missing_permissions",
                    None,
                )
            )
            return

        # Command raised an exception: Forbidden: 403 Forbidden (error code: 160002):
        # Cannot reply without permission to read message history
        case (
            discord.ext.commands.errors.CommandInvokeError()
        ) if "Cannot reply without permission to read message history" in str(error):
            try:
                await ctx.send(
                    tool_function.convert_msg(
                        LOCALE,
                        lang,
                        "command",
                        "on_command_error",
                        "bot_cannot_read_history",
                        None,
                    )
                )
            except Exception:
                await ctx.author.send(
                    tool_function.convert_msg(
                        LOCALE,
                        lang,
                        "command",
                        "on_command_error",
                        "bot_cannot_read_history",
                        None,
                    )
                )
            return

        # Auto report unknown command error to owner (fuck it my dm are fill with error msgs)
        case _:
            await tool_function.postgres_logging(error)
            try:
                server_name = ctx.guild.name
            except AttributeError:
                server_name = ""
            try:
                server_id = ctx.guild.id
            except AttributeError:
                server_id = ""
            sender_name = ctx.author.name
            command_name = ctx.invoked_with

            owner_data = await bot.fetch_user(config["owner"])
            owner_name = owner_data.name
            owner_discriminator = owner_data.discriminator
            """
            # Never used it anymore, discord change their username system
            # But keep it just for memorial
            if str(owner_discriminator) != "0":
                owner_full_id = f"{owner_name}#{owner_discriminator}"
            else:
                owner_full_id = f"@{owner_name}"
            """
            await owner_data.send(
                f"Unknown command error\n"
                "```"
                f"Command: {command_name}\n"
                f"Error: {error}\n"
                f"Error Type: {type(error)}\n"
                f"Server Name: {server_name}\n"
                f"Server ID: {server_id}\n"
                f"Sender: {sender_name}\n"
                "```"
            )
            await owner_data.send(ctx.message.content)
            raise error


# noinspection PyShadowingBuiltins
# help command
@bot.command(Name="help", aliases=command_alias["help"])
async def help(ctx):  # sourcery skip: low-code-quality
    # define language by db or default
    locale_lang = tool_function.check_db_lang(ctx)
    guild_msg = tool_function.check_guild_or_dm(ctx)
    # messages for guilds which already set up settings
    if guild_msg and tool_function.check_db_file(f"{ctx.guild.id}"):
        data = tool_function.read_db_json(f"{ctx.guild.id}")

        # lang help text change to current if settings exist
        match tool_function.check_dict_data(data, "lang"):
            case True:
                lang_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "lang_msg_current",
                    ["prefix", config["prefix"], "data_lang", data["lang"]],
                )
            case False:
                lang_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "lang_msg_default",
                    [
                        "prefix",
                        config["prefix"],
                    ],
                )

        # channel help text change to current if settings exist
        match tool_function.check_dict_data(data, "channel"):
            case True:
                channel_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "channel_msg_current",
                    ["prefix", config["prefix"], "data_channel", data["channel"]],
                )
            case False:
                # default channel command text
                guild_system_channel = ctx.guild.system_channel
                channel_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "channel_msg_default",
                    ["prefix", config["prefix"], "sys_channel", guild_system_channel.id],
                )

        # voice platform help text change to current if settings exist
        match tool_function.check_dict_data(data, "platform"):
            case True:
                platform_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "platform_msg_current",
                    ["prefix", config["prefix"], "data_platform", data["platform"]],
                )
            case False:
                platform_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "platform_msg_default",
                    [
                        "prefix",
                        config["prefix"],
                        "data_support_platform",
                        ", ".join(list(supported_platform)),
                    ],
                )

        # nochannel help text change to current if settings exist
        match tool_function.check_dict_data(data, "nochannel"):
            case True:
                nochannel_status = "on" if data["nochannel"] else "off"
                nochannel_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "nochannel_msg_current",
                    ["prefix", config["prefix"], "data_nochannel", nochannel_status],
                )
            case False:
                nochannel_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "nochannel_msg_default",
                    ["prefix", config["prefix"]],
                )

        # noname help text change to current if settings exist
        match tool_function.check_dict_data(data, "no_name"):
            case True:
                noname_status = "on" if data["no_name"] else "off"
                noname_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "noname_msg_current",
                    ["prefix", config["prefix"], "data_noname", noname_status],
                )
            case False:
                noname_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "noname_msg_default",
                    ["prefix", config["prefix"]],
                )

        # mix all together and send
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                locale_lang,
                "command",
                "help",
                "help",
                [
                    "prefix",
                    config["prefix"],
                    "channel_msg",
                    channel_msg,
                    "lang_msg",
                    lang_msg,
                    "platform_msg",
                    platform_msg,
                    "nochannel_msg",
                    nochannel_msg,
                    "noname_msg",
                    noname_msg,
                ],
            )
        )

    # messages for not guilds and user settings exists (private message)
    elif (
        not guild_msg
        and tool_function.check_dict_data(
            tool_function.read_db_json("user_config"),
            f"user_{int(ctx.author.id)}",
        )
        and tool_function.check_dict_data(
            tool_function.read_db_json("user_config")[f"user_{int(ctx.author.id)}"],
            "platform",
        )
    ):
        # read user config
        data = tool_function.read_db_json("user_config")[f"user_{int(ctx.author.id)}"]

        # voice platform help text change to current if settings exist
        match tool_function.check_dict_data(data, "platform"):
            case True:
                platform_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "platform_msg_current",
                    ["prefix", config["prefix"], "data_platform", data["platform"]],
                )
            case False:
                platform_msg = tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "help",
                    "platform_msg_default",
                    [
                        "prefix",
                        config["prefix"],
                        "data_support_platform",
                        ", ".join(list(supported_platform)),
                    ],
                )

        channel_msg = tool_function.convert_msg(
            LOCALE,
            locale_lang,
            "variable",
            "help",
            "channel_msg_else",
            [
                "prefix",
                config["prefix"],
            ],
        )

        lang_msg = tool_function.convert_msg(
            LOCALE,
            locale_lang,
            "variable",
            "help",
            "lang_msg_default",
            [
                "prefix",
                config["prefix"],
            ],
        )

        nochannel_msg = tool_function.convert_msg(
            LOCALE,
            locale_lang,
            "variable",
            "help",
            "nochannel_msg_default",
            ["prefix", config["prefix"]],
        )

        noname_msg = tool_function.convert_msg(
            LOCALE,
            locale_lang,
            "variable",
            "help",
            "noname_msg_default",
            ["prefix", config["prefix"]],
        )

        # mix all together and send
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                locale_lang,
                "command",
                "help",
                "help",
                [
                    "prefix",
                    config["prefix"],
                    "platform_msg",
                    platform_msg,
                    "channel_msg",
                    channel_msg,
                    "lang_msg",
                    lang_msg,
                    "nochannel_msg",
                    nochannel_msg,
                    "noname_msg",
                    noname_msg,
                ],
            )
        )

    # send default message if no settings
    else:
        # support_lang = tool_function.read_local_json("google_languages.json")
        # azure_lang = tool_function.read_local_json("azure_languages.json")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                locale_lang,
                "command",
                "help",
                "help",
                [
                    "prefix",
                    config["prefix"],
                    "platform_msg",
                    tool_function.convert_msg(
                        LOCALE,
                        locale_lang,
                        "variable",
                        "help",
                        "platform_msg_default",
                        [
                            "prefix",
                            config["prefix"],
                            "data_support_platform",
                            ", ".join(list(supported_platform)),
                        ],
                    ),
                    "channel_msg",
                    tool_function.convert_msg(
                        LOCALE,
                        locale_lang,
                        "variable",
                        "help",
                        "channel_msg_else",
                        [
                            "prefix",
                            config["prefix"],
                        ],
                    ),
                    "lang_msg",
                    tool_function.convert_msg(
                        LOCALE,
                        locale_lang,
                        "variable",
                        "help",
                        "lang_msg_default",
                        [
                            "prefix",
                            config["prefix"],
                        ],
                    ),
                    "nochannel_msg",
                    tool_function.convert_msg(
                        LOCALE,
                        locale_lang,
                        "variable",
                        "help",
                        "nochannel_msg_default",
                        ["prefix", config["prefix"]],
                    ),
                    "noname_msg",
                    tool_function.convert_msg(
                        LOCALE,
                        locale_lang,
                        "variable",
                        "help",
                        "noname_msg_default",
                        ["prefix", config["prefix"]],
                    ),
                ],
            )
        )


# join command
@bot.command(Name="join", aliases=command_alias["join"])
@commands.guild_only()
@commands.cooldown(1, 10, commands.BucketType.user)
# @commands.bot_has_permissions(connect=True, speak=True)
async def join(ctx, *, channel: discord.VoiceChannel):
    # define language by db or default
    locale_lang = tool_function.check_db_lang(ctx)
    # get user send channel id
    user_voice_channel = channel

    # attempt to join voice channel
    try:
        await user_voice_channel.connect()
    except discord.errors.ClientException:
        # join failed, mostly because of bot already joined other channel (still buggy in 2.0)
        bot_voice_channel = ctx.guild.voice_client.channel
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                locale_lang,
                "command",
                "join",
                "join_already_in",
                ["prefix", config["prefix"], "join_vc", bot_voice_channel.id],
            )
        )
    except Exception:
        await tool_function.postgres_logging(
            f"Join Failed:\n" f"{ctx.guild.id}\n" f"{ctx.message.author.id}\n" f"{traceback.format_exc()}"
        )

        await ctx.message.add_reaction("❌")
    else:
        # join success
        await ctx.message.add_reaction("✅")
        # write channel id to joined_vc dict for restart rejoin
        joined_vc = tool_function.read_db_json("joined_vc")
        joined_vc[ctx.guild.id] = user_voice_channel.id
        tool_function.write_db_json("joined_vc", joined_vc)


@join.error
async def join_error(ctx, error):
    if isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "join",
                "join_bad_arg",
                ["prefix", config["prefix"]],
            )
        )

        await ctx.message.add_reaction("❌")
        return


@bot.command(Name="leave", aliases=command_alias["leave"])
async def leave(ctx, emoji: bool = True):
    try:
        await ctx.voice_client.disconnect()
    except AttributeError:
        pass
    else:
        if emoji:
            await ctx.message.add_reaction("🖐")
        # delete channel id from joined_vc dict
    joined_vc = tool_function.read_db_json("joined_vc")
    with contextlib.suppress(KeyError):
        del joined_vc[str(ctx.guild.id)]
    tool_function.write_db_json("joined_vc", joined_vc)


# TODO: Migrate to settings command
@bot.command(Name="setchannel")
@commands.cooldown(1, 20, commands.BucketType.user)
@commands.guild_only()
async def setchannel(ctx, channel: discord.TextChannel | discord.VoiceChannel | discord.ForumChannel):
    # get channel id
    channel_id = channel.id
    # get guild id
    guild_id = ctx.guild.id
    # write to db folder with guild id filename
    if tool_function.check_db_file(f"{guild_id}"):
        data = tool_function.read_db_json(f"{guild_id}")
        data["channel"] = channel_id
    else:
        data = {"channel": channel_id}

    tool_function.write_db_json(f"{guild_id}", data)
    await ctx.reply(
        tool_function.convert_msg(
            LOCALE,
            tool_function.check_db_lang(ctx),
            "command",
            "setchannel",
            "setchannel_success",
            [
                "data_channel",
                channel.id,
            ],
        )
    )


@setchannel.error
async def setchannel_error(ctx, error):
    if isinstance(error, commands.BadUnionArgument):
        # get guild system channel
        guild_system_channel = ctx.guild.system_channel
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "setchannel",
                "setchannel_bad_arg",
                ["prefix", config["prefix"], "sys_channel", guild_system_channel.id],
            )
        )
        await ctx.message.add_reaction("❌")
        return


@bot.command(Name="say", aliases=command_alias["say"])
@commands.guild_only()
async def say(ctx, *, content: str):  # sourcery no-metrics skip: for-index-replacement
    # sourcery skip: low-code-quality

    locale_lang = tool_function.check_db_lang(ctx)
    # get guild id
    guild_id = ctx.guild.id
    if tool_function.check_db_file(f"{guild_id}"):
        # read db file
        db = tool_function.read_db_json(f"{guild_id}")

        if langissetup := tool_function.check_dict_data(db, "lang"):
            say_lang_cmd = bot.get_command("say_lang")
            await ctx.invoke(say_lang_cmd, lang=db["lang"], content=content)

        else:
            errormsg = ""
            if not langissetup:
                errormsg += tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "say",
                    "err_no_lang_set",
                    [
                        "prefix",
                        config["prefix"],
                    ],
                )
            await ctx.reply(errormsg)
            await ctx.message.add_reaction("❌")
    else:
        await ctx.send(
            tool_function.convert_msg(
                LOCALE,
                locale_lang,
                "command",
                "say",
                "say_no_setting",
                [
                    "prefix",
                    config["prefix"],
                ],
            )
        )


# TODO: Migrate to settings command
@bot.command(Name="setlang")
@commands.guild_only()
async def setlang(ctx, lang: str):
    # get guild id
    locale_lang = tool_function.check_db_lang(ctx)
    guild_id = ctx.guild.id
    support_lang = tool_function.read_local_json("lang_list/google_languages.json")
    azure_lang = tool_function.read_local_json("lang_list/azure_languages.json")
    lang = lang.lower()
    lang = lang.replace("_", "-")
    if lang in support_lang["Support_Language"] or lang in azure_lang["Support_Language"]:
        if tool_function.check_db_file(f"{guild_id}"):
            # read db file
            db = tool_function.read_db_json(f"{guild_id}")
            # add lang to db
            db["lang"] = lang
            # write to db file
            tool_function.write_db_json(f"{guild_id}", db)
        else:
            tool_function.write_db_json(f"{guild_id}", {"lang": lang})
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                lang,
                "command",
                "setlang",
                "setlang_success",
                [
                    "data_lang",
                    lang,
                ],
            )
        )
        await ctx.message.add_reaction("✅")
    elif lang == "supported-languages":
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                locale_lang,
                "command",
                "setlang",
                "setlang_lang_list",
                [
                    "google_lang_list",
                    ", ".join(support_lang["Support_Language"]),
                    "azure_lang_list",
                    ", ".join(azure_lang["Support_Language"]),
                ],
            )
        )
    else:
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                "en",
                "command",
                "setlang",
                "setlang_bad_arg",
                [
                    "current_lang",
                    lang,
                    "google_lang_list",
                    ", ".join(support_lang["Support_Language"]),
                    "azure_lang_list",
                    ", ".join(azure_lang["Support_Language"]),
                ],
            )
        )
        await ctx.message.add_reaction("❌")


@bot.command(Name="ping")
@commands.cooldown(1, 5, commands.BucketType.user)
async def ping(ctx):
    await ctx.reply(f"Pong! {round(bot.latency * 1000)}ms")


@bot.command(Name="reboot")
@commands.is_owner()
async def reboot(ctx):
    await ctx.reply("Rebooting...")
    await bot.close()


@bot.command(Name="shutdown")
@commands.is_owner()
async def shutdown(ctx):
    await ctx.reply("Shutting down...")
    # send SIGTERM to the bot process
    os.kill(os.getpid(), signal.SIGTERM)


@bot.command(Name="clear", aliases=["c"])
@commands.guild_only()
async def clear(ctx):
    # TODO: Json Remove
    await ctx.reply(
        tool_function.convert_msg(
            LOCALE,
            tool_function.check_db_lang(ctx),
            "command",
            "clear",
            "clear",
            None,
        )
    )


@bot.command(Name="stop")
@commands.guild_only()
async def stop(ctx):
    # TODO: Json Remove
    # stop playing from voice channel
    try:
        ctx.voice_client.is_connected()
    except AttributeError:
        is_connected = False
    else:
        is_connected = True

    if is_connected and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.message.add_reaction("⏹")


@bot.command(Name="invite")
async def invite(ctx):
    await ctx.reply(
        tool_function.convert_msg(
            LOCALE,
            tool_function.check_db_lang(ctx),
            "command",
            "invite",
            "invite",
            [
                "invite_link",
                f"{discord.utils.oauth_url(client_id='960004225713201172', permissions=discord.Permissions(139690626112), scopes=('bot', 'applications.commands'))}",
            ],
        )
    )


# TODO: Migrate to settings command
@bot.command(name="set_noname")
@commands.guild_only()
async def set_noname(ctx, value: str):
    if tool_function.check_db_file(f"{ctx.guild.id}"):
        db = tool_function.read_db_json(f"{ctx.guild.id}")
        if value in {"on", "off"}:
            db["no_name"] = True if value == "on" else False
            tool_function.write_db_json(f"{ctx.guild.id}", db)
            if db["no_name"]:
                reply_msg = tool_function.convert_msg(
                    LOCALE,
                    tool_function.check_db_lang(ctx),
                    "command",
                    "no_name",
                    "no_name_on",
                    None,
                )
            elif not db["no_name"]:
                reply_msg = tool_function.convert_msg(
                    LOCALE,
                    tool_function.check_db_lang(ctx),
                    "command",
                    "no_name",
                    "no_name_off",
                    None,
                )
            else:
                reply_msg = "How did you trigger this?"
            await ctx.reply(f"{reply_msg}")
            await ctx.message.add_reaction("✅")
        else:
            await ctx.reply(
                tool_function.convert_msg(
                    LOCALE,
                    tool_function.check_db_lang(ctx),
                    "command",
                    "no_name",
                    "no_name_bad_arg",
                    [
                        "prefix",
                        config["prefix"],
                    ],
                )
            )
            await ctx.message.add_reaction("❌")
    else:
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "no_name",
                "no_name_no_setting",
                None,
            )
        )
        await ctx.message.add_reaction("🤔")


# TODO: Migrate to settings command
@bot.command(Name="wrong_msg")
@commands.guild_only()
async def wrong_msg(ctx, msg: str):
    if tool_function.check_db_file(f"{ctx.guild.id}"):
        db = tool_function.read_db_json(f"{ctx.guild.id}")
        if msg in {"on", "off"}:
            db["not_this_channel_msg"] = msg
            tool_function.write_db_json(f"{ctx.guild.id}", db)
            if msg == "on":
                reply_msg = tool_function.convert_msg(
                    LOCALE,
                    tool_function.check_db_lang(ctx),
                    "command",
                    "wrong_msg",
                    "wrong_msg_on",
                    None,
                )
            elif msg == "off":
                reply_msg = tool_function.convert_msg(
                    LOCALE,
                    tool_function.check_db_lang(ctx),
                    "command",
                    "wrong_msg",
                    "wrong_msg_off",
                    None,
                )
            else:
                reply_msg = "How did you trigger this?"
            await ctx.reply(f"{reply_msg}")
            await ctx.message.add_reaction("✅")
        else:
            await ctx.reply(
                tool_function.convert_msg(
                    LOCALE,
                    tool_function.check_db_lang(ctx),
                    "command",
                    "wrong_msg",
                    "wrong_msg_bad_arg",
                    [
                        "prefix",
                        config["prefix"],
                    ],
                )
            )
            await ctx.message.add_reaction("❌")
    else:
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "wrong_msg",
                "wrong_msg_no_setting",
                None,
            )
        )
        await ctx.message.add_reaction("🤔")


# TODO: rewrite to disconnect & connect
@bot.command(Name="move", aliases=command_alias["move"])
@commands.cooldown(1, 10, commands.BucketType.user)
@commands.guild_only()
async def move(ctx, *, channel: discord.VoiceChannel):
    leave_cmd = bot.get_command("leave")
    join_cmd = bot.get_command("join")
    await ctx.invoke(leave_cmd, emoji=False)
    await asyncio.sleep(0.5)
    await ctx.invoke(join_cmd, channel=channel)


@move.error
async def move_error(ctx, error):
    if isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "move",
                "move_bad_arg",
                ["prefix", config["prefix"]],
            )
        )

        await ctx.message.add_reaction("❌")
        return


@bot.command(Name="say_lang", aliases=command_alias["say_lang"])
# @commands.cooldown(1, 3, commands.BucketType.user)
@commands.guild_only()
async def say_lang(ctx, lang: str, *, content: str, gpt: bool = False):  # sourcery no-metrics
    # sourcery skip: low-code-quality
    # get message channel id

    locale_lang = tool_function.check_db_lang(ctx)

    user_id = ctx.author.id
    user_platform_set = bool(
        tool_function.check_dict_data(tool_function.read_db_json("user_config"), f"user_{user_id}")
        and tool_function.check_dict_data(tool_function.read_db_json("user_config")[f"user_{user_id}"], "platform")
    )

    channel_id = ctx.channel.id
    # get guild id
    guild_id = ctx.guild.id
    if tool_function.check_db_file(f"{guild_id}"):
        # read db file
        db = tool_function.read_db_json(f"{guild_id}")
        # check channel id
        # check if is in voice channel

        guild_platform_set = bool(tool_function.check_dict_data(db, "platform"))
        try:
            ctx.voice_client.is_connected()
        except AttributeError:
            is_connected = False
        else:
            is_connected = True

        if not is_connected:
            joined_vc = tool_function.read_db_json("joined_vc")
            with contextlib.suppress(KeyError):
                del joined_vc[str(guild_id)]
            tool_function.write_db_json("joined_vc", joined_vc)

        google_lang_code_list = tool_function.read_local_json("lang_list/google_languages.json")["Support_Language"]
        azure_lang_code_list = tool_function.read_local_json("lang_list/azure_languages.json")["Support_Language"]

        lang = lang.lower()
        lang = lang.replace("_", "-")

        lang_code_is_right = lang in google_lang_code_list or lang in azure_lang_code_list
        channelissetup = tool_function.check_dict_data(db, "channel")

        if (
            is_connected
            and channelissetup
            and lang_code_is_right
            and (channel_id == db["channel"] or (tool_function.check_dict_data(db, "nochannel") and db["nochannel"]))
        ):
            # export content to mp3 by google tts api
            # get username

            """
            Discord User ID RegExp
            <@![0-9]{18}>
            <@[0-9]{18}>
            Role ID
            <@&[0-9]{18}>
            """

            # check if user is being Banned
            if command_func.is_banned(user_id, guild_id):
                await ctx.message.add_reaction("🔇")
                return

            content = await command_func.content_convert(ctx, lang, LOCALE, content)

            if gpt:
                content = await command_func.gpt_process(db["lang"], content, LOCALE)

            text_split = re.split(r"\s|\n", content)

            too_long = any(len(i) > 50 for i in text_split) or len(text_split) > 30 or len(content) > 300

            say_this = (
                not os.getenv("TEST_ENV") and ctx.author.id in (int(config["owner"]), 890234177767755849)
            ) or not too_long

            if gpt or not tool_function.check_dict_data(db, "no_name") or not db["no_name"]:
                content = command_func.name_convert(ctx, lang, LOCALE, content, gpt)

            if say_this:
                if not ctx.voice_client.is_playing():
                    await tool_function.postgres_logging(
                        f"Playing content: \n" f"{content}\n" f"From {ctx.author.name}\n" f"In {ctx.guild.name}"
                    )

                    platform_result = await command_func.check_voice_platform(
                        user_platform_set, user_id, guild_platform_set, guild_id, lang
                    )

                    # process tts file (false if went wrong)
                    if not await command_func.tts_convert(ctx, lang, content, platform_result):
                        owner = await bot.fetch_user(int(config["owner"]))
                        await owner.send(
                            f"Something went wrong return triggered!\n"
                            f"Guild ID: {guild_id}\n"
                            f"User ID: {user_id}\n"
                            f"User Platform Set: {user_platform_set}\n"
                            f"Guild Platform Set: {guild_platform_set}\n"
                        )
                        # add bug emoji reaction
                        await ctx.message.add_reaction("🐛")

                    voice_file = await discord.FFmpegOpusAudio.from_probe(f"tts_temp/{guild_id}.mp3")
                    ctx.voice_client.play(
                        voice_file,
                        after=await queue_job(ctx, lang, content, platform_result),
                    )
                    await ctx.message.add_reaction("🔊")
                    send_time = int(time.mktime(datetime.datetime.now(datetime.timezone.utc).timetuple()))
                    msg_tmp = {0: send_time, 1: user_id}
                    tool_function.write_local_json(f"msg_temp/{guild_id}.json", msg_tmp)

                elif tool_function.check_dict_data(db, "queue") and db["queue"]:
                    # TODO: Write json
                    # add reaction
                    await ctx.message.add_reaction("⏯")
                    await queue_job(
                        ctx,
                        lang,
                        content,
                        await command_func.check_voice_platform(
                            user_platform_set,
                            user_id,
                            guild_platform_set,
                            guild_id,
                            lang,
                        ),
                    )
                else:
                    if gpt:
                        await ctx.reply(
                            f"""
                                {tool_function.convert_msg(
                                LOCALE,
                                db["lang"],
                                "command",
                                "say",
                                "say_queue_not_support",
                                None,
                            )}\n```\n{content}```
                                                """
                        )
                    else:
                        await ctx.reply(
                            tool_function.convert_msg(
                                LOCALE,
                                lang,
                                "command",
                                "say",
                                "say_queue_not_support",
                                None,
                            )
                        )

            else:
                if not gpt:
                    await ctx.reply(
                        tool_function.convert_msg(
                            LOCALE,
                            lang,
                            "command",
                            "say",
                            "say_too_long",
                            None,
                        )
                    )
                else:
                    await ctx.reply(
                        f"""
                        {tool_function.convert_msg(
                        LOCALE,
                        db["lang"],
                        "command",
                        "say",
                        "say_too_long",
                        None,
                    )}\n```\n{content}```
                    """
                    )

        elif (
            channelissetup
            and channel_id != db["channel"]
            and (not tool_function.check_dict_data(db, "not_this_channel_msg") or db["not_this_channel_msg"] != "off")
        ):
            channel_msg = tool_function.convert_msg(
                LOCALE,
                locale_lang,
                "variable",
                "say",
                "wrong_channel",
                [
                    "data_channel",
                    db["channel"],
                ],
            )
            await ctx.reply(
                tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "command",
                    "say",
                    "say_wrong_channel",
                    [
                        "prefix",
                        config["prefix"],
                        "channel_msg",
                        channel_msg,
                        "current_channel",
                        channel_id,
                    ],
                )
            )
            await ctx.message.add_reaction("🤔")

        elif tool_function.check_dict_data(db, "not_this_channel_msg") and db["not_this_channel_msg"] == "off":
            return
            # reply to sender
        else:
            errormsg = ""
            if not is_connected:
                errormsg += tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "say",
                    "err_not_join",
                    [
                        "prefix",
                        config["prefix"],
                    ],
                )
            if not channelissetup:
                errormsg += tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "say",
                    "err_no_channel_set",
                    [
                        "prefix",
                        config["prefix"],
                    ],
                )
            if not lang_code_is_right:
                errormsg += tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "say_lang",
                    "err_lang_not_in_list",
                    [
                        "current_lang",
                        lang,
                        "google_lang_list",
                        ", ".join(google_lang_code_list),
                        "azure_lang_list",
                        ", ".join(azure_lang_code_list),
                    ],
                )
            await ctx.reply(errormsg)
            await ctx.message.add_reaction("❌")
    else:
        await ctx.send(
            tool_function.convert_msg(
                LOCALE,
                locale_lang,
                "command",
                "say_lang",
                "say_lang_no_setting",
                [
                    "prefix",
                    config["prefix"],
                ],
            )
        )


@bot.command(name="force_say", aliases=command_alias["force_say"])
@commands.guild_only()
@commands.is_owner()
async def force_say(ctx, *, content: str):  # sourcery no-metrics skip: for-index-replacement
    # sourcery skip: low-code-quality
    # get message channel id

    locale_lang = tool_function.check_db_lang(ctx)

    # get guild id
    guild_id = ctx.guild.id
    if tool_function.check_db_file(f"{guild_id}"):
        # read db file
        db = tool_function.read_db_json(f"{guild_id}")

        if langissetup := tool_function.check_dict_data(db, "lang"):
            stop_cmd = bot.get_command("stop")
            say_lang_cmd = bot.get_command("say_lang")
            await ctx.invoke(stop_cmd)
            await ctx.invoke(say_lang_cmd, lang=db["lang"], content=content)

        else:
            errormsg = ""
            if not langissetup:
                errormsg += tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "say",
                    "err_no_lang_set",
                    [
                        "prefix",
                        config["prefix"],
                    ],
                )
            await ctx.reply(errormsg)
            await ctx.message.add_reaction("❌")
    else:
        await ctx.send(
            tool_function.convert_msg(
                LOCALE,
                locale_lang,
                "command",
                "say",
                "say_no_setting",
                [
                    "prefix",
                    config["prefix"],
                ],
            )
        )


@bot.command(Name="gpt_say", aliases=command_alias["gpt_say"])
# @commands.is_owner()
@commands.cooldown(1, 10, commands.BucketType.user)
async def gpt_say(ctx, *, content: str):  # sourcery no-metrics skip: for-index-replacement
    # sourcery skip: low-code-quality

    locale_lang = tool_function.check_db_lang(ctx)
    # get guild id
    guild_id = ctx.guild.id
    if tool_function.check_db_file(f"{guild_id}"):
        # read db file
        db = tool_function.read_db_json(f"{guild_id}")

        if langissetup := tool_function.check_dict_data(db, "lang"):
            say_lang_cmd = bot.get_command("say_lang")
            await ctx.invoke(say_lang_cmd, lang=db["lang"], content=content, gpt=True)

        else:
            errormsg = ""
            if not langissetup:
                errormsg += tool_function.convert_msg(
                    LOCALE,
                    locale_lang,
                    "variable",
                    "say",
                    "err_no_lang_set",
                    [
                        "prefix",
                        config["prefix"],
                    ],
                )
            await ctx.reply(errormsg)
            await ctx.message.add_reaction("❌")
    else:
        await ctx.send(
            tool_function.convert_msg(
                LOCALE,
                locale_lang,
                "command",
                "say",
                "say_no_setting",
                [
                    "prefix",
                    config["prefix"],
                ],
            )
        )


# TODO: Migrate to settings command
@bot.command(name="setvoice")
@commands.cooldown(1, 20, commands.BucketType.user)
async def setvoice(ctx, platform: str):
    if platform.capitalize() not in supported_platform and platform.lower() != "reset":
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "setvoice",
                "setvoice_arg_not_supported",
                [
                    "prefix",
                    config["prefix"],
                    "data_support_platform",
                    ", ".join(supported_platform),
                ],
            )
        )
        return
    is_guild = tool_function.check_guild_or_dm(ctx)
    guild_id = tool_function.user_id_rename(ctx)

    if platform.lower() == "reset":
        if not is_guild and (
            not tool_function.check_dict_data(tool_function.read_db_json("user_config"), guild_id)
            or not tool_function.check_dict_data(tool_function.read_db_json("user_config")[guild_id], "platform")
        ):
            await ctx.reply(
                tool_function.convert_msg(
                    LOCALE,
                    tool_function.check_db_lang(ctx),
                    "command",
                    "setvoice",
                    "setvoice_reset_no_setting",
                    None,
                )
            )
            return

        if is_guild and (
            not tool_function.check_db_file(guild_id)
            or not tool_function.check_dict_data(tool_function.read_db_json(guild_id), "platform")
        ):
            await ctx.reply(
                tool_function.convert_msg(
                    LOCALE,
                    tool_function.check_db_lang(ctx),
                    "command",
                    "setvoice",
                    "setvoice_reset_no_setting",
                    None,
                )
            )
            return

        if is_guild:
            data = tool_function.read_db_json(guild_id)
            del data["platform"]
            tool_function.write_db_json(guild_id, data)
        else:
            data = tool_function.read_db_json("user_config")
            del data[guild_id]["platform"]
            if data[guild_id] == {}:
                del data[guild_id]
            tool_function.write_db_json("user_config", data)

        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "setvoice",
                "setvoice_reset_success",
                None,
            )
        )
        return
    platform = platform.capitalize()
    if tool_function.check_db_file(guild_id) and is_guild:
        data = tool_function.read_db_json(guild_id)
        data["platform"] = platform
        tool_function.write_db_json(guild_id, data)
    elif not is_guild:
        data = tool_function.read_db_json("user_config")
        data[guild_id] = {
            "platform": platform,
        }
        tool_function.write_db_json("user_config", data)
    else:
        data = {"platform": platform}
        tool_function.write_db_json(guild_id, data)

    await ctx.reply(
        tool_function.convert_msg(
            LOCALE,
            tool_function.check_db_lang(ctx),
            "command",
            "setvoice",
            "setvoice_success",
            [
                "data_voice",
                platform,
            ],
        )
    )


# TODO: Migrate to settings command
@bot.command(name="set_nochannel")
@commands.guild_only()
@commands.cooldown(1, 20, commands.BucketType.user)
async def set_nochannel(ctx, setup: str):
    """set not locking channel in settings ~~(history problem)~~"""
    guild_id = ctx.guild.id
    setup = setup.lower()
    if setup not in {"on", "off"}:
        await ctx.message.add_reaction("❌")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "set_nochannel",
                "set_nochannel_bad_arg",
                ["prefix", config["prefix"]],
            )
        )

        return
    if tool_function.check_db_file(guild_id):
        data = tool_function.read_db_json(guild_id)
        data["nochannel"] = setup == "on"
        tool_function.write_db_json(guild_id, data)
        await ctx.message.add_reaction("✅")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "set_nochannel",
                "set_nochannel_success",
                ["status", setup],
            )
        )

    else:
        await ctx.message.add_reaction("❌")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "set_nochannel",
                "set_nochannel_no_settings",
            )
        )

    return


@bot.command(name="ban")
@commands.guild_only()
@commands.cooldown(1, 20, commands.BucketType.user)
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: str | int | discord.Member, expire: int = 300):
    """temporary block someone's speak permission for this bot"""
    if type(member) not in {str, int, discord.Member} or type(expire) != int:
        await ctx.message.add_reaction("❌")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "ban",
                "ban_bad_arg",
                [
                    "prefix",
                    config["prefix"],
                ],
            )
        )
        return
    try:
        if type(member) in {str, int} and type(member) != discord.Member:
            member = await commands.MemberConverter().convert(ctx, member)
    except discord.ext.commands.MemberNotFound:
        # unknown user
        await ctx.message.add_reaction("❓")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "ban",
                "ban_unknown_user",
                None,
            )
        )
        return

    if member.id in {config["owner"], bot.user.id, 890234177767755849}:
        await ctx.message.add_reaction("❌")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "ban",
                "ban_owner",
                None,
            )
        )
        return

    server_id = str(ctx.guild.id)
    member_id = str(member.id)
    user_id = str(ctx.author.id)
    ban_list = tool_function.read_db_json("ban")
    now_sec = int(time.mktime(datetime.datetime.now(datetime.timezone.utc).timetuple()))
    expire_sec = int(now_sec + expire)
    if (
        user_id in ban_list
        and tool_function.check_dict_data(ban_list[user_id], server_id)
        and now_sec <= ban_list[user_id][server_id]["expire"]
    ):
        await ctx.message.add_reaction("❌")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "ban",
                "ban_not_allowed",
                [
                    "ban_time",
                    str(int(ban_list[member_id][server_id]["expire"]) - now_sec),
                ],
            )
        )
        return

    if member_id not in ban_list:
        ban_list[member_id] = {
            server_id: {
                "expire": expire_sec,
            }
        }
    elif server_id in ban_list[member_id] and ban_list[member_id][server_id]["expire"] > now_sec:
        ban_list[member_id][server_id]["expire"] = ban_list[member_id][server_id]["expire"] + expire
    else:
        ban_list[member_id][server_id] = {
            "expire": expire_sec,
        }
    if ban_list[member_id][server_id]["expire"] - now_sec >= 216000:
        ban_list[member_id][server_id]["expire"] = int(now_sec + 216000)
    tool_function.write_db_json("ban", ban_list)
    if str(member.discriminator) != "0":
        user_name = f"{member.name}#{member.discriminator}"
    else:
        user_name = f"@{member.name}"
    await ctx.message.add_reaction("🚫")
    await ctx.reply(
        tool_function.convert_msg(
            LOCALE,
            tool_function.check_db_lang(ctx),
            "command",
            "ban",
            "ban_success",
            [
                "ban_time",
                str(ban_list[member_id][server_id]["expire"] - now_sec),
                "username",
                user_name,
            ],
        )
    )


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "ban",
                "ban_bad_arg",
                ["prefix", config["prefix"]],
            )
        )

        await ctx.message.add_reaction("❌")
        return


@bot.command(name="unban")
@commands.guild_only()
@commands.cooldown(1, 20, commands.BucketType.user)
@commands.has_permissions(ban_members=True)
async def unban(ctx, member: str | int | discord.Member):
    """unblock someone's speak permission for this bot"""
    if type(member) not in {str, int, discord.Member}:
        await ctx.message.add_reaction("❌")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "unban",
                "unban_bad_arg",
                [
                    "prefix",
                    config["prefix"],
                ],
            )
        )
        return

    try:
        if type(member) in {str, int} and type(member) != discord.Member:
            member = await commands.MemberConverter().convert(ctx, member)
    except discord.ext.commands.MemberNotFound:
        # unknown user
        await ctx.message.add_reaction("❓")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "ban",
                "ban_unknown_user",
                None,
            )
        )
        return

    if member.id in {config["owner"], bot.user.id, 890234177767755849}:
        await ctx.message.add_reaction("❌")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "unban",
                "unban_owner",
                None,
            )
        )
        return

    server_id = str(ctx.guild.id)
    member_id = str(member.id)
    user_id = str(ctx.author.id)
    now_sec = int(time.mktime(datetime.datetime.now(datetime.timezone.utc).timetuple()))
    ban_list = tool_function.read_db_json("ban")
    if user_id in ban_list and server_id in ban_list[user_id] and now_sec <= ban_list[user_id][server_id]["expire"]:
        await ctx.message.add_reaction("❌")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "unban",
                "unban_not_allowed",
                [
                    "ban_time",
                    str(int(ban_list[user_id][server_id]["expire"]) - now_sec),
                ],
            )
        )
        return

    if (
        member_id not in ban_list
        or server_id not in ban_list[member_id]
        or ban_list[member_id][server_id]["expire"] < now_sec
    ):
        if member_id in ban_list and server_id in ban_list[member_id]:
            with contextlib.suppress(Exception):
                del ban_list[f"{member_id}"][f"{server_id}"]
            if not ban_list[f"{member_id}"]:
                with contextlib.suppress(Exception):
                    del ban_list[f"{member_id}"]
            tool_function.write_db_json("ban", ban_list)
        await ctx.message.add_reaction("❓")
        await ctx.reply(
            tool_function.convert_msg(
                LOCALE,
                tool_function.check_db_lang(ctx),
                "command",
                "unban",
                "unban_not_banned",
                None,
            )
        )
        return

    with contextlib.suppress(Exception):
        del ban_list[f"{member_id}"][f"{server_id}"]
    if not ban_list[f"{member_id}"]:
        with contextlib.suppress(Exception):
            del ban_list[f"{member_id}"]
    tool_function.write_db_json("ban", ban_list)
    if str(member.discriminator) != "0":
        user_name = f"{member.name}#{member.discriminator}"
    else:
        user_name = f"@{member.name}"
    await ctx.message.add_reaction("⭕")
    await ctx.reply(
        tool_function.convert_msg(
            LOCALE,
            tool_function.check_db_lang(ctx),
            "command",
            "unban",
            "unban_success",
            ["username", user_name],
        )
    )


# TODO: Migrate this
@bot.command(name="settings")
async def settings(ctx, key, *, value):
    raise NotImplementedError


if __name__ == "__main__":
    if os.getenv("TEST_ENV"):
        print("Running on test environment")
        test_env = True
    else:
        print("Running on production environment")
        test_env = False

    subprocess.call(["python3", "src/gcp-token-generator.py"])
    if test_env:
        bot.run(os.environ["DISCORD_DV_TEST_TOKEN"])
    else:
        subprocess.call(["python3", "src/gcp-token-generator.py"])
        subprocess.call(["python3", "src/get_lang_code.py"])
        bot.run(os.environ["DISCORD_DV_TOKEN"])

"""
Note:

`os.getenv()` does not raise an exception, but returns None
`os.environ.get()` similarly returns None
`os.environ[]` raises an exception if the environmental variable does not exist

"""

# TODO: `say_del` command (delete msg after say)
