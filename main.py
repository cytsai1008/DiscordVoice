import asyncio
import logging
import os
import traceback

# import sys
import queue
import subprocess
import shutil
from datetime import datetime

import discord
from discord.ext import commands

from dotenv import load_dotenv

import tool_function

# from io import BytesIO

# from google.cloud import texttospeech

# import tts_func

# logging
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
if not os.path.exists("Log"):
    os.mkdir("Log")
handler = logging.FileHandler(filename="Log/discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

# check file
if not tool_function.check_file("config.json"):
    print(
        "No token detected\n"
        "please input your token from https://discord.com/developers/applications:"
    )
    config_json = input()
    print("Please input your user id:")
    user_id = input()
    print("Please input your bot prefix:")
    prefix = input()
    config_dump = {"token": config_json, "owner": user_id, "prefix": prefix}
    tool_function.write_json("config.json", config_dump)
    del config_json, user_id, prefix, config_dump
config = tool_function.read_json("config.json")
if not tool_function.check_file("db"):
    os.mkdir("db")

bot = commands.Bot(command_prefix=config["prefix"], help_command=None, case_insensitive=True, owner_id=config["owner"])

# initialize some variable
bot.remove_command("help")
load_dotenv()

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
'''
def process_voice(content: str, lang_code: str):
    """Synthesizes speech from the input string of text or ssml.
    Make sure to be working in a virtual environment.

    Note: ssml must be well-formed according to:
        https://www.w3.org/TR/speech-synthesis/
    """
    import os
    from google.cloud import texttospeech

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=content)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_code,
        ssml_gender=texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED,
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content
'''


def remove_file(file_name):
    os.remove(f"tts_temp/{file_name}")


def convert_tts(content: str, lang_code: str, file_name: str):
    print("init google tts api")
    print("play mp3")
    subprocess.call(
        [
            "python",
            "tts_alone.py",
            "--content",
            content,
            "--lang",
            lang_code,
            "--filename",
            f"{file_name}.mp3",
        ]
    )


def playnext(ctx, lang_id: str, guild_id, list_id: queue.Queue):
    if list_id.empty():
        try:
            if os.path.exists(f"tts_temp/{guild_id}.mp3"):
                os.remove("tts_temp/{guild_id}.mp3")
        except:
            pass

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
# 當機器人完成啟動時
async def on_ready():
    print("目前登入身份：", bot.user)
    game = discord.Game(f"{config['prefix']}help")
    # discord.Status.<狀態>，可以是online,offline,idle,dnd,invisible
    await bot.change_presence(status=discord.Status.online, activity=game)
    owner = await bot.fetch_user(config["owner"])
    await owner.send("bot online.")
    # get all guilds
    print("目前登入的伺服器：")
    for guild in bot.guilds:
        print(guild.name + "\n")


@bot.event
async def on_guild_join(guild):
    general = guild.system_channel
    if general and general.permissions_for(guild.me).send_messages:
        await general.send(
            "Thanks for adding me!\n"
            "Please set a channel by `$setchannel`. (ex. `$setchannel #general`)\n"
            "Please set a language by `$setlang`. (ex. `$setlang en-us`)\n"
            "To speak something, please use `$say`. (ex. `$say ABCD`)\n"
            "To join a voice channel, please use `$join`.\n"
            "To leave a voice channel, please use `$leave`.\n"
            "For more information, please type `$help`."
        )


@bot.event
async def on_command_error(ctx, error, exception):  # sourcery skip: remove-pass-elif
    command = ctx.invoked_with
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.reply("Command not found.")
        await ctx.message.add_reaction("❌")
    elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        if command == "setchannel":
            await ctx.reply("No channel providing, please set by `$setchannel #some-channel`.")
        elif command == "setlang":
            support_lang = tool_function.read_json("languages.json")
            await ctx.reply("No language providing, please set by `$setlang some-lang-code`.\n"
                            f"Current supported languages: \n"
                            f"```{', '.join(support_lang['Support_Language'])}```\n"
                            )
        elif command == "say":
            await ctx.reply("What can I say? :(")
        else:
            await ctx.reply("Missing required argument.")
        await ctx.message.add_reaction("❓")
    elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.reply(f"You're too fast! Please wait for {round(error.retry_after)} seconds.")
        await ctx.message.add_reaction("⏳")
    elif command == "setchannel" and isinstance(error, discord.ext.commands.errors.ChannelNotFound):
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
        try:
            await ctx.reply(
                f"Unknown command error, please report to developer (<@{config['owner']}> or `(⊙ｏ⊙)#0001`).\n"
                "```"
                f"{error}\n"
                f"{exception}\n"
                "```"
            )
        except:
            try:
                ctx.send(
                    f"Unknown command error, please report to developer (<@{config['owner']}> or `(⊙ｏ⊙)#0001`).\n"
                    "```"
                    f"{error}\n"
                    f"{exception}\n"
                    "```"
                )
            except:
                # send to owner
                owner = await bot.fetch_user(config["owner"])
                await owner.send(
                    f"Unknown command error, please report to developer (<@{config['owner']}> or `(⊙ｏ⊙)#0001`).\n"
                    "```"
                    f"{error}\n"
                    f"{exception}\n"
                    "```"
                )


@bot.event
async def on_error(event, *args, **kwargs):
    with open("error.log", "a") as f:
        f.write(f"{datetime.now()}\n")
        f.write(f"{event}\n")
        f.write(f"{args}\n")
        f.write(f"{kwargs}\n")
        f.write("\n")
    # send message to owner
    owner = await bot.fetch_user(config["owner"])
    await owner.send(
        f"Error event on: {event}\n"
        f"Error args on: {args}\n"
        f"Error kwargs on: {kwargs}\n"
    )


@bot.command(Name="help")
async def help(ctx):
    try:
        _ = ctx.guild.id
    except:
        guild_msg = False
    else:
        guild_msg = True
    if guild_msg and tool_function.check_file(f"db/{ctx.guild.id}.json"):
        data = tool_function.read_json(f"db/{ctx.guild.id}.json")
        if tool_function.check_dict_data(data, "lang"):
            lang_msg = f"Use `$setlang` to set a language. (Current: `{data['lang']}`)\n"
        else:
            support_lang = tool_function.read_json("languages.json")
            lang_msg = "Use `$setlang` to set a language. (ex. `$setlang en-us`)\n" \
                       f"Current supported languages: \n" \
                       f"```{', '.join(support_lang['Support_Language'])}```\n"

        if tool_function.check_dict_data(data, "channel"):
            channel_msg = f"Use `$setchannel` to set a channel. (Current: <#{data['channel']}>)\n"
        else:
            channel_msg = "Use `$setchannel` to set a channel. (ex. `$setchannel #general`)\n"

        await ctx.reply(
            "Use `$help` to see the help message.\n"
            f"{channel_msg}"
            f"{lang_msg}"
            "Use `$say` to speak in voice channel. (ex. `$say ABCD`)\n"
            "Use `$stop` to stop speaking.\n"
            "Use `$join` to let me join to a voice channel.\n"
            "Use `$leave` to let me leave the voice channel.\n"
            "Use `$ping` to check my latency.\n"
        )
    else:
        support_lang = tool_function.read_json("languages.json")
        await ctx.reply(
            "Use `$help` to see the help message.\n"
            "Use `$setchannel` to set a channel. (ex. `$setchannel #general`)\n"
            "Use `$setlang` to set a language. (ex. `$setlang en-us`)\n"
            f"Current supported languages: \n"
            f"```{', '.join(support_lang['Support_Language'])}```\n"
            "Use `$say` to speak in voice channel. (ex. `$say ABCD`)\n"
            "Use `$stop` to stop speaking.\n"
            "Use `$join` to let me join to a voice channel.\n"
            "Use `$leave` to let me leave the voice channel.\n"
            "Use `$ping` to check my latency.\n"
        )


@bot.command(Name="join")
@commands.guild_only()
@commands.has_permissions(connect=True, speak=True)
async def join(ctx):
    # get user voice channel
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
                "To move, please use `$leave` first."
            )
            await ctx.message.add_reaction("❌")
        else:
            await ctx.message.add_reaction("✅")


@bot.command(Name="leave")
async def leave(ctx):
    try:
        await ctx.voice_client.disconnect()
    except AttributeError:
        pass
    else:
        await ctx.message.add_reaction("🖐")


@bot.command(Name="setchannel")
@commands.guild_only()
async def setchannel(ctx, channel: discord.TextChannel):
    # get channel id
    channel_id = channel.id
    # get guild id
    guild_id = ctx.guild.id
    # write to db folder with guild id filename
    if tool_function.check_file(f"db/{guild_id}.json"):
        data = tool_function.read_json(f"db/{guild_id}.json")
        data["channel"] = channel_id
    else:
        data = {"channel": channel_id}

    tool_function.write_json(f"db/{guild_id}.json", data)
    await ctx.reply(f"channel set to <#{channel.id}>.")


@setchannel.error
async def setchannel_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.reply("Please enter a valid channel. (Must have blue background and is clickable, ex. `$setchannel "
                        "#general`)")
        await ctx.message.add_reaction("❌")


@bot.command(Name="say")
@commands.cooldown(1, 3, commands.BucketType.user)
@commands.guild_only()
@commands.has_permissions(connect=True, speak=True)
async def say(ctx, *, content: str):  # sourcery no-metrics skip: for-index-replacement
    # get message channel id

    channel_id = ctx.channel.id
    # get guild id
    guild_id = ctx.guild.id
    if tool_function.check_file(f"db/{guild_id}.json"):
        # read db file
        db = tool_function.read_json(f"db/{guild_id}.json")
        # check channel id
        # check if is in voice channel
        try:
            ctx.voice_client.is_connected()
        except AttributeError:
            is_connected = False
        else:
            is_connected = True

        channelissetup = tool_function.check_dict_data(db, "channel")
        langissetup = tool_function.check_dict_data(db, "lang")

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
            say_this = ctx.author.id == config["owner"] or len(content) < 30
            try:
                username = ctx.author.display_name
            except AttributeError:
                username = ctx.author.name
            # get username length
            if len(username) <= 20:
                if ctx.author.voice is not None:
                    content = f"{username} said {content}"
                else:
                    content = f"{username} from outside said {content}"
            if say_this:
                list_name = f"list_{str(guild_id)}"
                if list_name not in globals():
                    globals()[list_name] = queue.Queue(maxsize=10)

                if not ctx.voice_client.is_playing():
                    print("init google tts api")
                    # tts_func.process_voice(content, db["lang"])
                    print("play mp3")
                    subprocess.call(
                        [
                            "python",
                            "tts_alone.py",
                            "--content",
                            content,
                            "--lang",
                            db["lang"],
                            "--filename",
                            f"{guild_id}.mp3",
                        ]
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
                                tool_function.check_dict_data(db, "queue")
                                and db["queue"]
                        ):
                            globals()[list_name].put(content)
                            # add reaction
                            await ctx.message.add_reaction("⏯")
                            asyncio.ensure_future(check_is_not_playing(ctx))
                            playnext(
                                ctx, db["lang"], guild_id, globals()[list_name]
                            )
                        else:
                            await ctx.reply("Sorry, queue function is under development and current not supported.")

                elif ctx.author.id == config["owner"]:
                    print("init google tts api")
                    # tts_func.process_voice(content, db["lang"])
                    print("play mp3")
                    subprocess.call(
                        [
                            "python",
                            "tts_alone.py",
                            "--content",
                            content,
                            "--lang",
                            db["lang"],
                            "--filename",
                            f"{guild_id}.mp3",
                        ]
                    )

                    voice_file = discord.FFmpegPCMAudio(f"tts_temp/{guild_id}.mp3")
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
                elif tool_function.check_dict_data(db, "queue") and db["queue"]:
                    globals()[list_name].put(content)
                    # add reaction
                    await ctx.message.add_reaction("⏯")
                    asyncio.ensure_future(check_is_not_playing(ctx))
                    playnext(ctx, db["lang"], guild_id, globals()[list_name])
                else:
                    await ctx.reply("Sorry, queue function is under development and current not supported.")
            else:
                await ctx.reply("Too long to say.")
                # reply to sender
        else:
            """
            await ctx.send("Please set channel by `$setchannel`.\n"
                           "Please set language by `$setlang`.\n"
                           "Please join voice channel by `$join`.")
            """
            errormsg = ""
            if not is_connected:
                errormsg += "Please join voice channel by `$join`.\n"
            if not channelissetup:
                errormsg += "Please set channel by `$setchannel`.\n"
            if not langissetup:
                errormsg += "Please set language by `$setlang`.\n"
            await ctx.reply(errormsg)
            await ctx.message.add_reaction("❌")
    else:
        await ctx.send(
            "Setting file not exist.\n"
            "Please set channel by `$setchannel`.\n"
            "Please set language by `$setlang`.\n"
        )


@bot.command(Name="setlang")
@commands.guild_only()
async def setlang(ctx, lang: str):
    # get guild id
    guild_id = ctx.guild.id
    support_lang = tool_function.read_json("languages.json")
    lang = lang.lower()
    if lang in support_lang["Support_Language"]:
        if tool_function.check_file(f"db/{guild_id}.json"):
            # read db file
            db = tool_function.read_json(f"db/{guild_id}.json")
            # add lang to db
            db["lang"] = lang
            # write to db file
            tool_function.write_json(f"db/{guild_id}.json", db)
        else:
            tool_function.write_json(f"db/{guild_id}.json", {"lang": lang})
        await ctx.reply(f"Language set to `{lang}`.")
        await ctx.message.add_reaction("✅")
    elif lang == "supported-languages":
        await ctx.reply(
            f"Current supported languages: \n"
            f"```{', '.join(support_lang['Support_Language'])}```"
        )
    else:
        await ctx.reply(
            f"`{lang}` is not supported.\n"
            f"Current supported languages: \n"
            f"```{', '.join(support_lang['Support_Language'])}```"
        )
        await ctx.message.add_reaction("❌")


@bot.command(Name="ping")
@commands.cooldown(1, 5, commands.BucketType.user)
async def ping(ctx):
    await ctx.reply(f"Pong! {round(bot.latency * 1000)}ms")


@bot.command(Name="shutdown")
@commands.is_owner()
async def shutdown(ctx):
    sender = ctx.message.author.id
    owner = tool_function.read_json("config.json")
    owner = owner["owner"]
    if sender == owner:
        await ctx.reply("Shutting down...")
        await bot.close()


@bot.command(Name="clear")
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


subprocess.call(["python", "get_lang_code.py"])
bot.run(os.environ['DiscordToken'])
