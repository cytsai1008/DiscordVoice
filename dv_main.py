import asyncio
import contextlib
import datetime
import os
import queue
import re
import shutil
import signal
import subprocess
import time
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv

import dv_tool_function
import tts_func

if not os.path.exists("tts_temp"):
    os.mkdir("tts_temp")

if not os.path.exists("msg_temp"):
    os.mkdir("msg_temp")

load_dotenv()
# check file
config = {
    "prefix": f"{os.getenv('DISCORD_DV_PREFIX')}",
    "owner": int(os.getenv("DISCORD_OWNER")),
}

command_alias = {
    "help": ["h"],
    "join": ["j"],
    "leave": ["l", "dc", "disconnect"],
    "say": ["s"],
    "clear": ["c"],
    "move": ["m"],
    "say_lang": ["sl", "saylang", "say-lang"],
    "force_say": ["fs", "forcesay", "force-say"],
}

bot = commands.Bot(
    command_prefix=config["prefix"],
    help_command=None,
    case_insensitive=True,
    owner_ids=[config["owner"], 890234177767755849],
)

# initialize some variable
bot.remove_command("help")
bot.Intent = discord.Intents.default()

folder = "tts_temp"
for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print(f"Failed to delete {file_path}. Reason: {e}")


# load command
# help_zh_tw = load_command.read_description("help", "zh-tw")

# init google tts api
# tts_client = texttospeech.TextToSpeechClient()

# add_zh_tw = load_command.read_description("add", "zh-tw")
# remove_zh_tw = load_command.read_description("remove", "zh-tw")
# list_zh_tw = load_command.read_description("list", "zh-tw")
# random_zh_tw = load_command.read_description("random", "zh-tw")


def remove_file(file_name):
    os.remove(f"tts_temp/{file_name}")


def convert_tts(content: str, lang_code: str, file_name: str):
    print("init google tts api")
    print("play mp3")
    asyncio.run(tts_func.process_voice(content, lang_code, f"{file_name}.mp3"))


def playnext(ctx, lang_id: str, guild_id, list_id: queue.Queue):
    if list_id.empty():
        with contextlib.suppress(Exception):
            if os.path.exists(f"tts_temp/{guild_id}.mp3"):
                os.remove("tts_temp/{guild_id}.mp3")
    elif ctx.voice_client is not None and not ctx.voice_client.is_playing():
        convert_tts(list_id.get(), lang_id, guild_id)
        song = discord.FFmpegPCMAudio(f"tts_temp/{guild_id}.mp3")
        ctx.voice_client.play(song, after=playnext(ctx, lang_id, guild_id, list_id))


async def check_is_not_playing(ctx):
    while True:
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            await asyncio.sleep(0.5)
        else:
            break


@bot.event
async def on_ready():
    print("目前登入身份：", bot.user)
    game = discord.Game(f"{config['prefix']}help")
    # discord.Status.<狀態>，可以是online,offline,idle,dnd,invisible    # get all guilds
    print("目前登入的伺服器：")
    for guild in bot.guilds:
        print(guild.name + "\n")
    channel_list = ""
    if dv_tool_function.check_db_file("joined_vc") and os.getenv("TEST_ENV") != "True":
        remove_vc = []
        joined_vc = dv_tool_function.read_db_json("joined_vc")
        print(f"joined_vc: \n" f"{joined_vc}")
        for i, j in joined_vc.items():
            # join the vc
            try:
                # noinspection PyUnresolvedReferences
                await bot.get_channel(int(j)).connect()
            except Exception:
                remove_vc.append(str(i))
                print(f"Failed to connect to {j} in {i}.\n")
                print(f"Reason: \n{traceback.format_exc()}")
            else:
                print(f"Successfully connected to {j} in {i}.\n")
        for i in remove_vc:
            del joined_vc[i]
            dv_tool_function.write_db_json("joined_vc", joined_vc)
        for i, j in joined_vc.items():
            channel_list += f"{i}: {j}\n"
        channel_list = f"```\n" f"{channel_list}\n" f"```"
        if remove_vc:
            new_line = "\n"
            channel_list += (
                f"Fail to connect to the following channels:\n```\n"
                f"{new_line.join(remove_vc)}\n"
                f"```"
            )
    await bot.change_presence(status=discord.Status.online, activity=game)
    owner = await bot.fetch_user(int(config["owner"]))
    await owner.send("bot online.\n" "Connect to:\n" f"{channel_list}")


@bot.event
async def on_guild_join(guild):
    general = guild.system_channel
    if general and general.permissions_for(guild.me).send_messages:
        await general.send(
            "Thanks for adding me!\n"
            f"Please set a channel by `{config['prefix']}setchannel`. (ex. {config['prefix']}setchannel <#{general.id}>)\n"
            f"Please set a language by `{config['prefix']}setlang`. (ex. `{config['prefix']}setlang en-us`)\n"
            f"To speak something, please use `{config['prefix']}say`. (ex. `{config['prefix']}say ABCD`)\n"
            f"To join a voice channel, please use `{config['prefix']}join`.\n"
            f"To leave a voice channel, please use `{config['prefix']}leave`.\n"
            f"For more information, please type `{config['prefix']}help`.\n"
            f"Warning: Current not support text channel in voice channel.\n"
        )
    # get guild name
    guild_name = guild.name
    guild_id = guild.id
    # send to owner dm
    owner = await bot.fetch_user(int(config["owner"]))
    await owner.send(
        f"New server joined!\n" f"Guild Name: {guild_name}\n" f"Guild ID: {guild_id}\n"
    )


@bot.event
async def on_command_error(ctx, error):  # sourcery no-metrics skip: remove-pass-elif
    # sourcery skip: low-code-quality, remove-pass-elif
    command = ctx.invoked_with.lower()

    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.reply("Command not found.")
        await ctx.message.add_reaction("❌")

    elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        wrong_cmd = True

        if command == "setchannel":
            guild_system_channel = ctx.guild.system_channel
            await ctx.reply(
                f"No channel providing, please set by {config['prefix']}setchannel <#{guild_system_channel.id}>"
            )

        elif command == "setlang":
            support_lang = dv_tool_function.read_file_json("languages.json")
            azure_lang = dv_tool_function.read_file_json("azure_languages.json")
            await ctx.reply(
                f"No language providing, please set by `{config['prefix']}setlang some-lang-code`.\n"
                f"Google supported languages: \n"
                f"```\n{', '.join(support_lang['Support_Language'])}```\n"
                f"Azure supported languages: \n"
                f"```\n{', '.join(azure_lang['Support_Language'])}```"
            )

        elif command == "say" or command in command_alias["say"]:
            await ctx.reply("What can I say? :(")

        elif command == "say_lang" or command in command_alias["say_lang"]:
            await ctx.reply(
                "What can I say? :(\n"
                f"`{config['prefix']}say_lang some-lang-code say-something`"
            )

        elif command == "setvoice":
            await ctx.reply(
                f"No voice platform providing, please set by `{config['prefix']}setvoice platform-name` or `{config['prefix']}setvoice reset` to reset.\n"
                f"Current supported platforms: \n"
                f"```\nAzure, Google```"
            )

        elif command == "join" or command in command_alias["join"]:
            wrong_cmd = False
            try:
                user_voice_channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.reply("Please join a voice channel first.")
                await ctx.message.add_reaction("❌")
            # join
            else:
                try:
                    await user_voice_channel.connect()
                except discord.errors.ClientException:
                    bot_voice_channel = ctx.guild.voice_client.channel
                    await ctx.reply(
                        f"I'm already in <#{bot_voice_channel.id}>.\n"
                        f"To move, please use `{config['prefix']}move`."
                    )
                    await ctx.message.add_reaction("❌")
                else:
                    await ctx.message.add_reaction("✅")
                    # write channel id to joined_vc dict
                    joined_vc = dv_tool_function.read_db_json("joined_vc")
                    joined_vc[ctx.guild.id] = user_voice_channel.id
                    dv_tool_function.write_db_json("joined_vc", joined_vc)

        elif command == "move" or command in command_alias["move"]:
            wrong_cmd = False
            joined_vc = dv_tool_function.read_db_json("joined_vc")
            with contextlib.suppress(KeyError):
                del joined_vc[str(ctx.guild.id)]
            # get user voice channel
            try:
                user_voice_channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.reply("Please join a voice channel first.")
                await ctx.message.add_reaction("❌")
                return
            else:
                try:
                    with contextlib.suppress(AttributeError):
                        await ctx.voice_client.disconnect()
                    await user_voice_channel.connect()
                except discord.errors.ClientException:
                    pass
                else:
                    await ctx.message.add_reaction("✅")
                # get joined_vc
                if user_voice_channel is not None:
                    joined_vc[ctx.guild.id] = user_voice_channel.id
            dv_tool_function.write_db_json("joined_vc", joined_vc)

        else:
            await ctx.reply("Missing required argument.")
        if wrong_cmd:
            await ctx.message.add_reaction("❓")

    elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.reply(
            f"You're too fast! Please wait for {round(error.retry_after)} seconds."
        )
        await ctx.message.add_reaction("⏳")

    elif (
            command in ["setchannel", "join", "move"]
            or command in command_alias["join"]
            or command_alias["move"]
            and isinstance(error, discord.ext.commands.errors.ChannelNotFound)
    ):
        pass

    elif isinstance(error, discord.ext.commands.errors.NoPrivateMessage):
        await ctx.reply("This command cannot be used in private messages.")
        await ctx.message.add_reaction("❌")

    elif isinstance(error, discord.ext.commands.errors.TooManyArguments):
        await ctx.reply("Too many arguments.")
        await ctx.message.add_reaction("❌")

    elif isinstance(error, discord.ext.commands.errors.NotOwner):
        pass

    else:
        not_able_reply = ""
        not_able_send = ""
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
        try:
            # get owner name
            owner_data = await bot.fetch_user(config["owner"])
            owner_name = owner_data.name
            owner_discriminator = owner_data.discriminator
            owner_full_id = f"{owner_name}#{owner_discriminator}"
            await ctx.reply(
                f"Unknown command error, please report to developer (<@{config['owner']}> or `{owner_full_id}`).\n"
                "```"
                f"Error: {error}\n"
                f"Error Type: {type(error)}\n"
                "```"
            )
        except Exception:
            not_able_reply = traceback.format_exc()
            owner_data = await bot.fetch_user(config["owner"])
            owner_name = owner_data.name
            owner_discriminator = owner_data.discriminator
            owner_full_id = f"{owner_name}#{owner_discriminator}"
            try:
                await ctx.send(
                    f"Unknown command error, please report to developer (<@{config['owner']}> or `{owner_full_id}`).\n"
                    "```"
                    f"Error: {error}\n"
                    f"Error Type: {type(error)}\n"
                    "```"
                )
            except Exception:
                not_able_send = traceback.format_exc()
        owner_data = await bot.fetch_user(config["owner"])
        owner_name = owner_data.name
        owner_discriminator = owner_data.discriminator
        owner_full_id = f"{owner_name}#{owner_discriminator}"
        await owner_data.send(
            f"Unknown command error, please report to developer (<@{config['owner']}> or `{owner_full_id}`).\n"
            "```"
            f"Command: {command_name}\n"
            f"Error: {error}\n"
            f"Error Type: {type(error)}\n"
            f"Unable to reply: {not_able_reply}\n"
            f"Unable to send: {not_able_send}\n"
            f"Server Name: {server_name}\n"
            f"Server ID: {server_id}\n"
            f"Sender: {sender_name}#{ctx.author.discriminator}\n"
            "```"
        )


"""
@bot.event
async def on_error(event, *args, **kwargs):
    with open("error.log", "a") as f:
        f.write(f"{datetime.now()}\n")
        f.write(f"{event}\n")
        f.write(f"{args}\n")
        f.write(f"{kwargs}\n")
        f.write("\n")
    # send message to owner
    owner = await bot.fetch_user(int(config["owner"]))
    await owner.send(
        f"Error event on: {event}\n"
        f"Error args on: {args}\n"
        f"Error kwargs on: {kwargs}\n"
        f"Error type: {type(event)}"
    )
"""


@bot.command(Name="help", aliases=command_alias["help"])
async def help(ctx):  # sourcery skip: low-code-quality
    try:
        _ = ctx.guild.id
    except Exception:
        guild_msg = False
    else:
        guild_msg = True
    if guild_msg and dv_tool_function.check_db_file(f"{ctx.guild.id}"):
        data = dv_tool_function.read_db_json(f"{ctx.guild.id}")
        if dv_tool_function.check_dict_data(data, "lang"):
            lang_msg = f"Use `{config['prefix']}setlang` to set a language. (Current: `{data['lang']}`)\n"
        else:
            # support_lang = dv_tool_function.read_file_json("languages.json")
            # azure_lang = dv_tool_function.read_file_json("azure_languages.json")
            lang_msg = (
                f"Use `{config['prefix']}setlang` to set a language. (ex. `{config['prefix']}setlang en-us`)\n"
                f"Please use `{config['prefix']}setlang` to get a list of supported languages list.\n"
            )

        if dv_tool_function.check_dict_data(data, "channel"):
            channel_msg = f"Use `{config['prefix']}setchannel` to set a channel. (Current: <#{data['channel']}>)\n"
        else:
            guild_system_channel = ctx.guild.system_channel
            channel_msg = f"Use `{config['prefix']}setchannel` to set a channel. (ex. {config['prefix']}setchannel <#{guild_system_channel.id}>)\n"

        if dv_tool_function.check_dict_data(data, "platform"):
            platform_msg = f"Use `{config['prefix']}setvoice` to set a platform. (Current: `{data['platform']}`)\n"
        else:
            platform_msg = (
                f"Use `{config['prefix']}setvoice` to set a platform. (ex. `{config['prefix']}setvoice Google`)\n"
                f"Current supported platforms: \n"
                f"```\nGoogle, Azure```\n"
            )

        await ctx.reply(
            f"Use `{config['prefix']}help` to see the help message.\n"
            f"{channel_msg}"
            f"{lang_msg}"
            f"{platform_msg}"
            f"Use `{config['prefix']}say` to speak in voice channel. (ex. `{config['prefix']}say ABCD`)\n"
            f"Use `{config['prefix']}say_lang` to speak in voice channel with another language. (ex. `{config['prefix']}say_lang en-us ABCD`)\n"
            f"Use `{config['prefix']}stop` to stop speaking.\n"
            f"Use `{config['prefix']}join` to let me join to a voice channel.\n"
            f"Use `{config['prefix']}move` to let me move to another voice channel.\n"
            f"Use `{config['prefix']}leave` to let me leave the voice channel.\n"
            f"Use `{config['prefix']}ping` to check my latency.\n"
            f"Use `{config['prefix']}invite` to get the bot's invite link.\n"
        )
    elif (
            not guild_msg
            and dv_tool_function.check_dict_data(
        dv_tool_function.read_db_json("user_config"),
        f"user_{int(ctx.author.id)}",
    )
            and dv_tool_function.check_dict_data(
        dv_tool_function.read_db_json("user_config")[f"user_{int(ctx.author.id)}"],
        "platform",
    )
    ):
        # support_lang = dv_tool_function.read_file_json("languages.json")
        # azure_lang = dv_tool_function.read_file_json("azure_languages.json")
        data = dv_tool_function.read_db_json("user_config")[
            f"user_{int(ctx.author.id)}"
        ]

        if dv_tool_function.check_dict_data(data, "platform"):
            platform_msg = f"Use `{config['prefix']}setvoice` to set a platform. (Current: `{data['platform']}`)\n"
        else:
            platform_msg = (
                f"Use `{config['prefix']}setvoice` to set a platform. (ex. `{config['prefix']}setvoice Google`)\n"
                f"Current supported platforms: \n"
                f"```\nGoogle, Azure```\n"
            )

        await ctx.reply(
            f"Use `{config['prefix']}help` to see the help message.\n"
            f"Use `{config['prefix']}setchannel` to set a channel. (ex. `{config['prefix']}setchannel #general`)\n"
            f"Use `{config['prefix']}setlang` to set a language. (ex. `{config['prefix']}setlang en-us`)\n"
            f"Please use `{config['prefix']}setlang` to get a list of supported languages list.\n"
            f"{platform_msg}"
            f"Use `{config['prefix']}say` to speak in voice channel. (ex. `{config['prefix']}say ABCD`)\n"
            f"Use `{config['prefix']}say_lang` to speak in voice channel with another language. (ex. `{config['prefix']}say_lang en-us ABCD`)\n"
            f"Use `{config['prefix']}stop` to stop speaking.\n"
            f"Use `{config['prefix']}join` to let me join to a voice channel.\n"
            f"Use `{config['prefix']}move` to let me move to another voice channel.\n"
            f"Use `{config['prefix']}leave` to let me leave the voice channel.\n"
            f"Use `{config['prefix']}ping` to check my latency.\n"
            f"Use `{config['prefix']}invite` to get the bot's invite link.\n"
        )

    else:
        # support_lang = dv_tool_function.read_file_json("languages.json")
        # azure_lang = dv_tool_function.read_file_json("azure_languages.json")
        await ctx.reply(
            f"Use `{config['prefix']}help` to see the help message.\n"
            f"Use `{config['prefix']}setchannel` to set a channel. (ex. `{config['prefix']}setchannel #general`)\n"
            f"Use `{config['prefix']}setlang` to set a language. (ex. `{config['prefix']}setlang en-us`)\n"
            f"Please use `{config['prefix']}setlang` to get a list of supported languages list.\n"
            f"Use `{config['prefix']}setvoice` to set a platform. (ex. `{config['prefix']}setvoice Google`)\n"
            f"Current supported platforms: \n"
            f"```\nGoogle, Azure```\n"
            f"Use `{config['prefix']}say` to speak in voice channel. (ex. `{config['prefix']}say ABCD`)\n"
            f"Use `{config['prefix']}say_lang` to speak in voice channel with another language. (ex. `{config['prefix']}say_lang en-us ABCD`)\n"
            f"Use `{config['prefix']}stop` to stop speaking.\n"
            f"Use `{config['prefix']}join` to let me join to a voice channel.\n"
            f"Use `{config['prefix']}move` to let me move to another voice channel.\n"
            f"Use `{config['prefix']}leave` to let me leave the voice channel.\n"
            f"Use `{config['prefix']}ping` to check my latency.\n"
            f"Use `{config['prefix']}invite` to get the bot's invite link.\n"
        )


@bot.command(Name="join", aliases=command_alias["join"])
@commands.guild_only()
# @commands.bot_has_permissions(connect=True, speak=True)
async def join(ctx, *, channel: discord.VoiceChannel):
    # join
    user_voice_channel = channel
    try:
        await user_voice_channel.connect()
    except discord.errors.ClientException:
        bot_voice_channel = ctx.guild.voice_client.channel
        await ctx.reply(
            f"I'm already in <#{bot_voice_channel.id}>.\n"
            f"To move, please use `{config['prefix']}move`."
        )
        await ctx.message.add_reaction("❌")
    else:
        await ctx.message.add_reaction("✅")
        # write channel id to joined_vc dict
        joined_vc = dv_tool_function.read_db_json("joined_vc")
        joined_vc[ctx.guild.id] = user_voice_channel.id
        dv_tool_function.write_db_json("joined_vc", joined_vc)


@join.error
async def join_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        # get guild system channel
        await ctx.reply(
            f"Please enter a valid voice channel or join a voice channel and type `{config['prefix']}join` directly.\n"
        )
        await ctx.message.add_reaction("❌")


@bot.command(Name="leave", aliases=command_alias["leave"])
async def leave(ctx):
    try:
        await ctx.voice_client.disconnect()
    except AttributeError:
        pass
    else:
        await ctx.message.add_reaction("🖐")
        # delete channel id from joined_vc dict
    joined_vc = dv_tool_function.read_db_json("joined_vc")
    with contextlib.suppress(KeyError):
        del joined_vc[str(ctx.guild.id)]
    dv_tool_function.write_db_json("joined_vc", joined_vc)


@bot.command(Name="setchannel")
@commands.guild_only()
async def setchannel(ctx, channel: discord.TextChannel):
    # get channel id
    channel_id = channel.id
    # get guild id
    guild_id = ctx.guild.id
    # write to db folder with guild id filename
    if dv_tool_function.check_db_file(f"{guild_id}"):
        data = dv_tool_function.read_db_json(f"{guild_id}")
        data["channel"] = channel_id
    else:
        data = {"channel": channel_id}

    dv_tool_function.write_db_json(f"{guild_id}", data)
    await ctx.reply(f"channel set to <#{channel.id}>")


@setchannel.error
async def setchannel_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        # get guild system channel
        guild_system_channel = ctx.guild.system_channel
        await ctx.reply(
            f"Please enter a valid channel. (Must have blue background and is clickable, ex. {config['prefix']}setchannel "
            f"<#{guild_system_channel.id}>)"
        )
        await ctx.message.add_reaction("❌")


@bot.command(Name="say", aliases=command_alias["say"])
@commands.cooldown(1, 3, commands.BucketType.user)
@commands.guild_only()
async def say(ctx, *, content: str):  # sourcery no-metrics skip: for-index-replacement
    # sourcery skip: low-code-quality
    # get message channel id

    user_id = ctx.author.id
    user_platform_set = bool(
        dv_tool_function.check_dict_data(
            dv_tool_function.read_db_json("user_config"), f"user_{user_id}"
        )
        and dv_tool_function.check_dict_data(
            dv_tool_function.read_db_json("user_config")[f"user_{user_id}"], "platform"
        )
    )

    channel_id = ctx.channel.id
    # get guild id
    guild_id = ctx.guild.id
    if dv_tool_function.check_db_file(f"{guild_id}"):
        # read db file
        db = dv_tool_function.read_db_json(f"{guild_id}")
        # check channel id
        # check if is in voice channel

        guild_platform_set = bool(dv_tool_function.check_dict_data(db, "platform"))
        try:
            ctx.voice_client.is_connected()
        except AttributeError:
            is_connected = False
        else:
            is_connected = True

        if not is_connected:
            joined_vc = dv_tool_function.read_db_json("joined_vc")
            with contextlib.suppress(KeyError):
                del joined_vc[str(guild_id)]
            dv_tool_function.write_db_json("joined_vc", joined_vc)

        channelissetup = dv_tool_function.check_dict_data(db, "channel")
        langissetup = dv_tool_function.check_dict_data(db, "lang")

        if (
                is_connected
                and channelissetup
                and langissetup
                and channel_id == db["channel"]
        ):

            # use cld to detect language
            """
            _, _, _, language = pycld2.detect(content, returnVector=True, debugScoreAsQuads=True)
            # separate multiple tuples as list
            language = list(language)
            # find unknown language as english in all key
            for i in range(len(language)):
                if language[i][4] == "un":
                    language[i][4] = "en"
                    language[i][3] = "ENGLISH"
                # merge if adjacent key are same
                if i != 0 and language[i][4] == language[i - 1][4]:
                    language[i - 1][2] += language[i][2]

            # separate text language
            # TODO: Multiple language split ( I can't split by number )
            """
            # export content to mp3 by google tts api
            # get username

            """
            Discord User ID RegExp
            <@![0-9]{18}>
            <@[0-9]{18}>
            Role ID
            <@&[0-9]{18}>
            """

            content = await commands.clean_content(
                fix_channel_mentions=True, use_nicknames=True
            ).convert(ctx, content)

            # Animate Emoji Replace
            if re.findall("<a:[^:]+:\d+>", content):
                emoji_id = re.findall("<a:[^:]+:\d+>", content)
                emoji_text = re.findall("<a:([^:]+):\d+>", content)
                for i in range(len(emoji_id)):
                    content = content.replace(emoji_id[i], f" Emoji:{emoji_text[i]} ")

            # Standard Emoji Replace
            if re.findall("<:[^:]+:\d+>", content):
                emoji_id = re.findall("<:[^:]+:\d+>", content)
                emoji_text = re.findall("<:([^:]+):\d+>", content)
                for i in range(len(emoji_id)):
                    content = content.replace(emoji_id[i], f" Emoji:{emoji_text[i]} ")

            say_this = (
                    ctx.author.id in (int(config["owner"]), 890234177767755849)
                    or len(content) < 30
            )
            try:
                username = ctx.author.display_name
            except AttributeError:
                username = ctx.author.name
            # get username length
            no_name = False
            send_time = int(
                time.mktime(datetime.datetime.now(datetime.timezone.utc).timetuple())
            )
            if dv_tool_function.check_file_file(f"msg_temp/{guild_id}.json"):
                old_msg_temp = dv_tool_function.read_file_json(
                    f"msg_temp/{guild_id}.json"
                )
                if (
                        old_msg_temp["1"] == user_id
                        and send_time - int(old_msg_temp["0"]) <= 15
                ):
                    no_name = True
            id_too_long = False
            if len(username) > 20:
                if len(ctx.author.name) > 20:
                    id_too_long = True
                else:
                    username = ctx.author.name

            if id_too_long:
                username = "someone"
                if ctx.author.voice is not None:
                    content = f"{username} said {content}"
                else:
                    content = f"{username} from outside said {content}"
            elif not no_name:
                content = (
                    f"{username} said {content}"
                    if ctx.author.voice is not None
                    else f"{username} from outside said {content}"
                )
            else:
                content = content

            if say_this:

                list_name = f"list_{str(guild_id)}"
                if list_name not in globals():
                    globals()[list_name] = queue.Queue(maxsize=10)

                if not ctx.voice_client.is_playing():
                    print("play mp3")

                    platform_result = dv_tool_function.check_platform(
                        user_platform_set,
                        user_id,
                        guild_platform_set,
                        guild_id,
                        db["lang"],
                    )
                    # GCP Cloud Text to Speech Method
                    if platform_result == "Google":
                        print("Init Google TTS API")
                        await tts_func.process_voice(
                            content, db["lang"], f"{guild_id}.mp3"
                        )

                    elif platform_result == "Azure":
                        print("Init Azure TTS API")
                        await tts_func.azure_tts_converter(
                            content, db["lang"], f"{guild_id}.mp3"
                        )
                    else:
                        print("Something Wrong")
                        # send to owner
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
                        await tts_func.process_voice(
                            content, db["lang"], f"{guild_id}.mp3"
                        )

                    voice_file = discord.FFmpegPCMAudio(f"tts_temp/{guild_id}.mp3")
                    try:
                        ctx.voice_client.play(
                            voice_file,
                            after=playnext(
                                ctx, db["lang"], guild_id, globals()[list_name]
                            ),
                        )
                        await ctx.message.add_reaction("🔊")
                    except discord.errors.ClientException:
                        if (
                                dv_tool_function.check_dict_data(db, "queue")
                                and db["queue"]
                        ):
                            globals()[list_name].put(content)
                            # add reaction
                            await ctx.message.add_reaction("⏯")
                            asyncio.ensure_future(check_is_not_playing(ctx))
                            playnext(ctx, db["lang"], guild_id, globals()[list_name])
                        else:
                            await ctx.reply(
                                "Sorry, queue function is under development and current not supported."
                            )
                    else:
                        send_time = int(
                            time.mktime(
                                datetime.datetime.now(datetime.timezone.utc).timetuple()
                            )
                        )
                        msg_tmp = {0: send_time, 1: user_id}
                        dv_tool_function.write_file_json(
                            f"msg_temp/{guild_id}.json", msg_tmp
                        )

                elif dv_tool_function.check_dict_data(db, "queue") and db["queue"]:
                    globals()[list_name].put(content)
                    # add reaction
                    await ctx.message.add_reaction("⏯")
                    asyncio.ensure_future(check_is_not_playing(ctx))
                    playnext(ctx, db["lang"], guild_id, globals()[list_name])
                else:
                    await ctx.reply(
                        "Sorry, queue function is under development and current not supported."
                    )
            else:
                await ctx.reply("Too long to say.")

        elif (
                channelissetup
                and channel_id != db["channel"]
                and (
                        not dv_tool_function.check_dict_data(db, "not_this_channel_msg")
                        or db["not_this_channel_msg"] != "off"
                )
        ):
            channel_msg = f"Please run this command in <#{db['channel']}>.\n"
            await ctx.reply(
                "This channel is not made for me to speaking.\n"
                f"{channel_msg}"
                f"To change channel, use {config['prefix']}setchannel <#{channel_id}>.\n"
                f"To disable this message, use `{config['prefix']}wrong_msg off`."
            )
            await ctx.message.add_reaction("🤔")

        elif (
                dv_tool_function.check_dict_data(db, "not_this_channel_msg")
                and db["not_this_channel_msg"] == "off"
        ):
            return
            # reply to sender
        else:
            errormsg = ""
            if not is_connected:
                errormsg += f"Please join voice channel by `{config['prefix']}join`\n"
            if not channelissetup:
                # guild_system_channel = ctx.guild.system_channel
                errormsg += f"Please set channel by {config['prefix']}setchannel\n"
            if not langissetup:
                errormsg += f"Please set language by `{config['prefix']}setlang`\n"
            await ctx.reply(errormsg)
            await ctx.message.add_reaction("❌")
    else:
        await ctx.send(
            "Setting file not exist.\n"
            f"Please set channel by `{config['prefix']}setchannel`\n"
            f"Please set language by `{config['prefix']}setlang`\n"
        )


@bot.command(Name="setlang")
@commands.guild_only()
async def setlang(ctx, lang: str):
    # get guild id
    guild_id = ctx.guild.id
    support_lang = dv_tool_function.read_file_json("languages.json")
    azure_lang = dv_tool_function.read_file_json("azure_languages.json")
    lang = lang.lower()
    lang = lang.replace("_", "-")
    if (
            lang in support_lang["Support_Language"]
            or lang in azure_lang["Support_Language"]
    ):
        if dv_tool_function.check_db_file(f"{guild_id}"):
            # read db file
            db = dv_tool_function.read_db_json(f"{guild_id}")
            # add lang to db
            db["lang"] = lang
            # write to db file
            dv_tool_function.write_db_json(f"{guild_id}", db)
        else:
            dv_tool_function.write_db_json(f"{guild_id}", {"lang": lang})
        await ctx.reply(f"Language set to `{lang}`.")
        await ctx.message.add_reaction("✅")
    elif lang == "supported-languages":
        await ctx.reply(
            f"Google supported languages: \n"
            f"```\n{', '.join(support_lang['Support_Language'])}```"
            f"Azure supported languages: \n"
            f"```\n{', '.join(azure_lang['Support_Language'])}```"
        )
    else:
        await ctx.reply(
            f"`{lang}` is not supported.\n"
            f"Google supported languages: \n"
            f"```\n{', '.join(support_lang['Support_Language'])}```"
            f"Azure supported languages: \n"
            f"```\n{', '.join(azure_lang['Support_Language'])}```"
        )
        await ctx.message.add_reaction("❌")


@bot.command(Name="ping")
@commands.cooldown(1, 5, commands.BucketType.user)
async def ping(ctx):
    await ctx.reply(f"Pong! {round(bot.latency * 1000)}ms")


@bot.command(Name="reboot")
@commands.is_owner()
async def reboot(ctx):
    sender = int(ctx.message.author.id)
    owner = int(config["owner"])
    if sender == owner:
        await ctx.reply("Rebooting...")
        await bot.close()


@bot.command(Name="shutdown")
@commands.is_owner()
async def shutdown(ctx):
    sender = int(ctx.message.author.id)
    owner = int(config["owner"])
    if sender == owner:
        await ctx.reply("Shutting down...")
        # send SIGTERM to the bot process
        os.kill(os.getpid(), signal.SIGTERM)


@bot.command(Name="clear", aliases=["c"])
@commands.guild_only()
async def clear(ctx):
    list_name = f"list_{ctx.guild.id}"
    if list_name in globals():
        globals()[list_name].queue.clear()
        await ctx.reply("Cleared.")


@bot.command(Name="stop")
@commands.guild_only()
async def stop(ctx):
    list_name = f"list_{ctx.guild.id}"
    if list_name in globals():
        globals()[list_name].queue.clear()
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
        f"Invite me to your server: \n"
        f"{discord.utils.oauth_url(client_id='960004225713201172', permissions=discord.Permissions(139690626112), scopes=('bot', 'applications.commands'))}"
    )


@bot.command(Name="wrong_msg")
@commands.guild_only()
async def wrong_msg(ctx, msg: str):
    if dv_tool_function.check_db_file(f"{ctx.guild.id}"):
        db = dv_tool_function.read_db_json(f"{ctx.guild.id}")
        if msg in {"on", "off"}:
            db["not_this_channel_msg"] = msg
            dv_tool_function.write_db_json(f"{ctx.guild.id}", db)
            if msg == "on":
                reply_msg = "From now on I will tell if you sent to an wrong channel."
            elif msg == "off":
                reply_msg = (
                    "From now on I will not tell if you sent to an wrong channel."
                )
            else:
                reply_msg = "How did you trigger this?"
            await ctx.reply(f"{reply_msg}")
            await ctx.message.add_reaction("✅")
        else:
            await ctx.reply(
                "Not recognized command.\n" "Usage: `wrong_msg on` or `wrong_msg off`"
            )
            await ctx.message.add_reaction("❌")
    else:
        await ctx.reply("You haven't set up anything yet.\n")
        await ctx.message.add_reaction("🤔")


@bot.command(Name="move", aliases=command_alias["move"])
@commands.guild_only()
async def move(ctx, *, channel: discord.VoiceChannel):
    joined_vc = dv_tool_function.read_db_json("joined_vc")
    with contextlib.suppress(KeyError):
        del joined_vc[str(ctx.guild.id)]
    # get user voice channel
    user_voice_channel = channel
    try:
        with contextlib.suppress(AttributeError):
            await ctx.voice_client.disconnect()
        await user_voice_channel.connect()
    except discord.errors.ClientException:
        connect_failed: bool = True
    else:
        await ctx.message.add_reaction("✅")
        connect_failed: bool = False
    # get joined_vc
    if not connect_failed:
        joined_vc[ctx.guild.id] = user_voice_channel.id
    dv_tool_function.write_db_json("joined_vc", joined_vc)


@move.error
async def move_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        # get guild system channel
        await ctx.reply(
            f"Please enter a valid voice channel or join a voice channel and type `{config['prefix']}move` directly.\n"
        )
        await ctx.message.add_reaction("❌")


@bot.command(Name="say_lang", aliases=command_alias["say_lang"])
@commands.cooldown(1, 3, commands.BucketType.user)
@commands.guild_only()
async def say_lang(ctx, lang: str, *, content: str):  # sourcery no-metrics
    # sourcery skip: low-code-quality
    # get message channel id

    user_id = ctx.author.id
    user_platform_set = bool(
        dv_tool_function.check_dict_data(
            dv_tool_function.read_db_json("user_config"), f"user_{user_id}"
        )
        and dv_tool_function.check_dict_data(
            dv_tool_function.read_db_json("user_config")[f"user_{user_id}"], "platform"
        )
    )

    channel_id = ctx.channel.id
    # get guild id
    guild_id = ctx.guild.id
    if dv_tool_function.check_db_file(f"{guild_id}"):
        # read db file
        db = dv_tool_function.read_db_json(f"{guild_id}")
        # check channel id
        # check if is in voice channel

        guild_platform_set = bool(dv_tool_function.check_dict_data(db, "platform"))
        try:
            ctx.voice_client.is_connected()
        except AttributeError:
            is_connected = False
        else:
            is_connected = True

        if not is_connected:
            joined_vc = dv_tool_function.read_db_json("joined_vc")
            with contextlib.suppress(KeyError):
                del joined_vc[str(guild_id)]
            dv_tool_function.write_db_json("joined_vc", joined_vc)

        lang_code_list = dv_tool_function.read_file_json("languages.json")[
            "Support_Language"
        ]
        azure_lang_code_list = dv_tool_function.read_file_json("azure_languages.json")[
            "Support_Language"
        ]

        lang = lang.lower()
        lang = lang.replace("_", "-")

        lang_code_is_right = lang in lang_code_list or lang in azure_lang_code_list
        channelissetup = dv_tool_function.check_dict_data(db, "channel")

        if (
                is_connected
                and channelissetup
                and lang_code_is_right
                and channel_id == db["channel"]
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

            content = await commands.clean_content(
                fix_channel_mentions=True, use_nicknames=True
            ).convert(ctx, content)

            # Animate Emoji Replace
            if re.findall("<a:[^:]+:\d+>", content):
                emoji_id = re.findall("<a:[^:]+:\d+>", content)
                emoji_text = re.findall("<a:([^:]+):\d+>", content)
                for i in range(len(emoji_id)):
                    content = content.replace(emoji_id[i], f" Emoji:{emoji_text[i]} ")

            # Standard Emoji Replace
            if re.findall("<:[^:]+:\d+>", content):
                emoji_id = re.findall("<:[^:]+:\d+>", content)
                emoji_text = re.findall("<:([^:]+):\d+>", content)
                for i in range(len(emoji_id)):
                    content = content.replace(emoji_id[i], f" Emoji:{emoji_text[i]} ")

            say_this = (
                    ctx.author.id in (int(config["owner"]), 890234177767755849)
                    or len(content) < 30
            )
            try:
                username = ctx.author.display_name
            except AttributeError:
                username = ctx.author.name
            # get username length
            no_name = False
            send_time = int(
                time.mktime(datetime.datetime.now(datetime.timezone.utc).timetuple())
            )
            if dv_tool_function.check_file_file(f"msg_temp/{guild_id}.json"):
                old_msg_temp = dv_tool_function.read_file_json(
                    f"msg_temp/{guild_id}.json"
                )
                if (
                        old_msg_temp["1"] == user_id
                        and send_time - int(old_msg_temp["0"]) <= 15
                ):
                    no_name = True
            id_too_long = False
            if len(username) > 20:
                if len(ctx.author.name) > 20:
                    id_too_long = True
                else:
                    username = ctx.author.name

            if id_too_long:
                username = "someone"
                if ctx.author.voice is not None:
                    content = f"{username} said {content}"
                else:
                    content = f"{username} from outside said {content}"
            elif not no_name:
                content = (
                    f"{username} said {content}"
                    if ctx.author.voice is not None
                    else f"{username} from outside said {content}"
                )
            else:
                content = content

            if say_this:

                list_name = f"list_{str(guild_id)}"
                if list_name not in globals():
                    globals()[list_name] = queue.Queue(maxsize=10)

                if not ctx.voice_client.is_playing():
                    print("play mp3")

                    platform_result = dv_tool_function.check_platform(
                        user_platform_set, user_id, guild_platform_set, guild_id, lang
                    )
                    # GCP Cloud Text to Speech Method
                    if platform_result == "Google":
                        print("Init Google TTS API")
                        await tts_func.process_voice(content, lang, f"{guild_id}.mp3")

                    elif platform_result == "Azure":
                        print("Init Azure TTS API")
                        await tts_func.azure_tts_converter(
                            content, lang, f"{guild_id}.mp3"
                        )
                    else:
                        print("Something Wrong")
                        # send to owner
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
                        await tts_func.process_voice(content, lang, f"{guild_id}.mp3")

                    voice_file = discord.FFmpegPCMAudio(f"tts_temp/{guild_id}.mp3")
                    try:
                        ctx.voice_client.play(
                            voice_file,
                            after=playnext(
                                ctx, db["lang"], guild_id, globals()[list_name]
                            ),
                        )
                        await ctx.message.add_reaction("🔊")
                    except discord.errors.ClientException:
                        if (
                                dv_tool_function.check_dict_data(db, "queue")
                                and db["queue"]
                        ):
                            globals()[list_name].put(content)
                            # add reaction
                            await ctx.message.add_reaction("⏯")
                            asyncio.ensure_future(check_is_not_playing(ctx))
                            playnext(ctx, db["lang"], guild_id, globals()[list_name])
                        else:
                            await ctx.reply(
                                "Sorry, queue function is under development and current not supported."
                            )

                    else:
                        send_time = int(
                            time.mktime(
                                datetime.datetime.now(datetime.timezone.utc).timetuple()
                            )
                        )
                        msg_tmp = {0: send_time, 1: user_id}
                        dv_tool_function.write_file_json(
                            f"msg_temp/{guild_id}.json", msg_tmp
                        )

                elif dv_tool_function.check_dict_data(db, "queue") and db["queue"]:
                    globals()[list_name].put(content)
                    # add reaction
                    await ctx.message.add_reaction("⏯")
                    asyncio.ensure_future(check_is_not_playing(ctx))
                    playnext(ctx, db["lang"], guild_id, globals()[list_name])
                else:
                    await ctx.reply(
                        "Sorry, queue function is under development and current not supported."
                    )
            else:
                await ctx.reply("Too long to say.")

        elif (
                channelissetup
                and channel_id != db["channel"]
                and (
                        not dv_tool_function.check_dict_data(db, "not_this_channel_msg")
                        or db["not_this_channel_msg"] != "off"
                )
        ):
            channel_msg = f"Please run this command in <#{db['channel']}>.\n"
            await ctx.reply(
                "This channel is not made for me to speaking.\n"
                f"{channel_msg}"
                f"To change channel, use {config['prefix']}setchannel <#{channel_id}>.\n"
                f"To disable this message, use `{config['prefix']}wrong_msg off`."
            )
            await ctx.message.add_reaction("🤔")

        elif (
                dv_tool_function.check_dict_data(db, "not_this_channel_msg")
                and db["not_this_channel_msg"] == "off"
        ):
            return
            # reply to sender
        else:
            errormsg = ""
            if not is_connected:
                errormsg += f"Please join voice channel by `{config['prefix']}join`.\n"
            if not channelissetup:
                errormsg += f"Please set channel by `{config['prefix']}setchannel`.\n"
            if not lang_code_is_right:
                errormsg += (
                    f"Not supported language.\n"
                    f"Google supported languages: \n"
                    f"```\n{', '.join(lang_code_list)}```\n"
                    f"Azure supported languages: \n"
                    f"```\n{', '.join(azure_lang_code_list)}```\n"
                )
            await ctx.reply(errormsg)
            await ctx.message.add_reaction("❌")
    else:
        await ctx.send(
            "Setting file not exist.\n"
            f"Please set channel by `{config['prefix']}setchannel`.\n"
            f"Please set language by `{config['prefix']}setlang`. (This command does not required in `{config['prefix']}say_lang`)\n"
        )


@bot.command(name="force_say", aliases=command_alias["force_say"])
@commands.guild_only()
@commands.is_owner()
async def force_say(
        ctx, *, content: str
):  # sourcery no-metrics skip: for-index-replacement
    # sourcery skip: low-code-quality
    # get message channel id

    user_id = ctx.author.id
    user_platform_set = bool(
        dv_tool_function.check_dict_data(
            dv_tool_function.read_db_json("user_config"), f"user_{user_id}"
        )
        and dv_tool_function.check_dict_data(
            dv_tool_function.read_db_json("user_config")[f"user_{user_id}"], "platform"
        )
    )

    channel_id = ctx.channel.id
    # get guild id
    guild_id = ctx.guild.id
    if dv_tool_function.check_db_file(f"{guild_id}"):
        # read db file
        db = dv_tool_function.read_db_json(f"{guild_id}")
        # check channel id
        # check if is in voice channel

        guild_platform_set = bool(dv_tool_function.check_dict_data(db, "platform"))
        try:
            ctx.voice_client.is_connected()
        except AttributeError:
            is_connected = False
        else:
            is_connected = True

        if not is_connected:
            joined_vc = dv_tool_function.read_db_json("joined_vc")
            with contextlib.suppress(KeyError):
                del joined_vc[str(guild_id)]
            dv_tool_function.write_db_json("joined_vc", joined_vc)

        channelissetup = dv_tool_function.check_dict_data(db, "channel")
        langissetup = dv_tool_function.check_dict_data(db, "lang")

        if (
                is_connected
                and channelissetup
                and langissetup
                and channel_id == db["channel"]
        ):

            # use cld to detect language
            # export content to mp3 by google tts api
            # get username

            """
            Discord User ID RegExp
            <@![0-9]{18}>
            <@[0-9]{18}>
            Role ID
            <@&[0-9]{18}>
            """

            content = await commands.clean_content(
                fix_channel_mentions=True, use_nicknames=True
            ).convert(ctx, content)

            # Animate Emoji Replace
            if re.findall("<a:[^:]+:\d+>", content):
                emoji_id = re.findall("<a:[^:]+:\d+>", content)
                emoji_text = re.findall("<a:([^:]+):\d+>", content)
                for i in range(len(emoji_id)):
                    content = content.replace(emoji_id[i], f" Emoji:{emoji_text[i]} ")

            # Standard Emoji Replace
            if re.findall("<:[^:]+:\d+>", content):
                emoji_id = re.findall("<:[^:]+:\d+>", content)
                emoji_text = re.findall("<:([^:]+):\d+>", content)
                for i in range(len(emoji_id)):
                    content = content.replace(emoji_id[i], f" Emoji:{emoji_text[i]} ")

            say_this = (
                    ctx.author.id in (int(config["owner"]), 890234177767755849)
                    or len(content) < 30
            )
            try:
                username = ctx.author.display_name
            except AttributeError:
                username = ctx.author.name
            # get username length
            if len(username) > 20:
                username = "someone" if len(ctx.author.name) > 20 else ctx.author.name
            if ctx.author.voice is not None:
                content = f"{username} said {content}"
            else:
                content = f"{username} from outside said {content}"
            if say_this:
                list_name = f"list_{str(guild_id)}"
                if list_name not in globals():
                    globals()[list_name] = queue.Queue(maxsize=10)

                if not ctx.voice_client.is_playing():
                    print("play mp3")

                    platform_result = dv_tool_function.check_platform(
                        user_platform_set,
                        user_id,
                        guild_platform_set,
                        guild_id,
                        db["lang"],
                    )
                    # GCP Cloud Text to Speech Method
                    if platform_result == "Google":
                        print("Init Google TTS API")
                        await tts_func.process_voice(
                            content, db["lang"], f"{guild_id}.mp3"
                        )

                    elif platform_result == "Azure":
                        print("Init Azure TTS API")
                        await tts_func.azure_tts_converter(
                            content, db["lang"], f"{guild_id}.mp3"
                        )
                    else:
                        print("Something Wrong")
                        # send to owner
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
                        await tts_func.process_voice(
                            content, db["lang"], f"{guild_id}.mp3"
                        )

                    voice_file = discord.FFmpegPCMAudio(f"tts_temp/{guild_id}.mp3")
                    try:
                        ctx.voice_client.play(
                            voice_file,
                            after=playnext(
                                ctx, db["lang"], guild_id, globals()[list_name]
                            ),
                        )
                        await ctx.message.add_reaction("🔊")
                    except discord.errors.ClientException:
                        if (
                                dv_tool_function.check_dict_data(db, "queue")
                                and db["queue"]
                        ):
                            globals()[list_name].put(content)
                            # add reaction
                            await ctx.message.add_reaction("⏯")
                            asyncio.ensure_future(check_is_not_playing(ctx))
                            playnext(ctx, db["lang"], guild_id, globals()[list_name])
                        else:
                            print("play mp3")

                            platform_result = dv_tool_function.check_platform(
                                user_platform_set,
                                user_id,
                                guild_platform_set,
                                guild_id,
                                db["lang"],
                            )
                            # GCP Cloud Text to Speech Method
                            if platform_result == "Google":
                                print("Init Google TTS API")
                                await tts_func.process_voice(
                                    content, db["lang"], f"{guild_id}.mp3"
                                )

                            elif platform_result == "Azure":
                                print("Init Azure TTS API")
                                await tts_func.azure_tts_converter(
                                    content, db["lang"], f"{guild_id}.mp3"
                                )
                            else:
                                print("Something Wrong")
                                # send to owner
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
                                await tts_func.process_voice(
                                    content, db["lang"], f"{guild_id}.mp3"
                                )

                            voice_file = discord.FFmpegPCMAudio(
                                f"tts_temp/{guild_id}.mp3"
                            )
                            # stop current audio
                            ctx.voice_client.stop()
                            await asyncio.sleep(0.5)
                            ctx.voice_client.play(
                                voice_file,
                                after=playnext(
                                    ctx, db["lang"], guild_id, globals()[list_name]
                                ),
                            )
                            await ctx.message.add_reaction("⁉")
                else:
                    print("play mp3")

                    platform_result = dv_tool_function.check_platform(
                        user_platform_set,
                        user_id,
                        guild_platform_set,
                        guild_id,
                        db["lang"],
                    )
                    # GCP Cloud Text to Speech Method
                    if platform_result == "Google":
                        print("Init Google TTS API")
                        await tts_func.process_voice(
                            content, db["lang"], f"{guild_id}.mp3"
                        )

                    elif platform_result == "Azure":
                        print("Init Azure TTS API")
                        await tts_func.azure_tts_converter(
                            content, db["lang"], f"{guild_id}.mp3"
                        )
                    else:
                        print("Something Wrong")
                        # send to owner
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
                        await tts_func.process_voice(
                            content, db["lang"], f"{guild_id}.mp3"
                        )

                    voice_file = discord.FFmpegPCMAudio(f"tts_temp/{guild_id}.mp3")
                    # stop current audio
                    ctx.voice_client.stop()
                    await asyncio.sleep(0.5)
                    ctx.voice_client.play(
                        voice_file,
                        after=playnext(ctx, db["lang"], guild_id, globals()[list_name]),
                    )
                    await ctx.message.add_reaction("⁉")
            else:
                await ctx.reply("Too long to say.")

        elif (
                channelissetup
                and channel_id != db["channel"]
                and (
                        not dv_tool_function.check_dict_data(db, "not_this_channel_msg")
                        or db["not_this_channel_msg"] != "off"
                )
        ):
            channel_msg = f"Please run this command in <#{db['channel']}>.\n"
            await ctx.reply(
                "This channel is not made for me to speaking.\n"
                f"{channel_msg}"
                f"To change channel, use {config['prefix']}setchannel <#{channel_id}>.\n"
                f"To disable this message, use `{config['prefix']}wrong_msg off`."
            )
            await ctx.message.add_reaction("🤔")

        elif (
                dv_tool_function.check_dict_data(db, "not_this_channel_msg")
                and db["not_this_channel_msg"] == "off"
        ):
            return
            # reply to sender
        else:
            errormsg = ""
            if not is_connected:
                errormsg += f"Please join voice channel by `{config['prefix']}join`.\n"
            if not channelissetup:
                errormsg += f"Please set channel by `{config['prefix']}setchannel`.\n"
            if not langissetup:
                errormsg += f"Please set language by `{config['prefix']}setlang`.\n"
            await ctx.reply(errormsg)
            await ctx.message.add_reaction("❌")
    else:
        await ctx.send(
            "Setting file not exist.\n"
            f"Please set channel by `{config['prefix']}setchannel`.\n"
            f"Please set language by `{config['prefix']}setlang`.\n"
        )


@bot.command(name="setvoice")
async def setvoice(ctx, platform: str):
    supported_platform = {"Google", "Azure"}
    if platform.capitalize() not in supported_platform and platform.lower() != "reset":
        await ctx.reply(
            "Not supported platform.\n"
            "Currently supported platform: \n"
            "```\n"
            f"{', '.join(list(supported_platform))}\n"
            "```\n"
            "or `reset` to reset."
        )
        return
    is_guild = dv_tool_function.check_guild_or_dm(ctx)
    guild_id = dv_tool_function.get_id(ctx)

    if platform.lower() == "reset":
        if not is_guild and (
                not dv_tool_function.check_dict_data(
                    dv_tool_function.read_db_json("user_config"), guild_id
                )
                or not dv_tool_function.check_dict_data(
            dv_tool_function.read_db_json("user_config")[guild_id], "platform"
        )
        ):
            await ctx.reply("Platform is not set.")
            return

        if is_guild and (
                not dv_tool_function.check_db_file(guild_id)
                or not dv_tool_function.check_dict_data(
            dv_tool_function.read_db_json(guild_id), "platform"
        )
        ):
            await ctx.reply("Platform is not set.")
            return

        if is_guild:
            data = dv_tool_function.read_db_json(guild_id)
            del data["platform"]
            dv_tool_function.write_db_json(guild_id, data)
        else:
            data = dv_tool_function.read_db_json("user_config")
            del data[guild_id]["platform"]
            if data[guild_id] == {}:
                del data[guild_id]
            dv_tool_function.write_db_json("user_config", data)

        await ctx.reply("Reset platform.")
        return
    platform = platform.capitalize()
    if dv_tool_function.check_db_file(guild_id) and is_guild:
        data = dv_tool_function.read_db_json(guild_id)
        data["platform"] = platform
        dv_tool_function.write_db_json(guild_id, data)
    elif not is_guild:
        data = dv_tool_function.read_db_json("user_config")
        data[guild_id] = {
            "platform": platform,
        }
        dv_tool_function.write_db_json("user_config", data)
    else:
        data = {"platform": platform}
        dv_tool_function.write_db_json(guild_id, data)

    await ctx.reply(f"Set platform to {platform}.")


if os.getenv("TEST_ENV"):
    print("Running on test environment")
    test_env = True
else:
    print("Running on production environment")
    test_env = False

if test_env:
    bot.run(os.environ["DISCORD_DV_TEST_TOKEN"])
else:
    subprocess.call(["python", "gcp-token-generator.py"])
    subprocess.call(["python", "get_lang_code.py"])
    bot.run(os.environ["DISCORD_DV_TOKEN"])

"""
Note:

`os.getenv()` does not raise an exception, but returns None
`os.environ.get()` similarly returns None
`os.environ[]` raises an exception if the environmental variable does not exist

"""

# TODO: `say_del` command
