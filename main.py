import logging
import os

# import sys
import subprocess
from io import BytesIO

import discord
from discord.ext import commands

# from datetime import datetime
from dotenv import load_dotenv

import tool_function

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

bot = commands.Bot(command_prefix=config["prefix"], help_command=None)

# initialize some variable
bot.remove_command("help")
load_dotenv()


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
        language_code=lang_code, ssml_gender=texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED
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


@bot.event
# 當機器人完成啟動時
async def on_ready():
    print("目前登入身份：", bot.user)
    game = discord.Game(f"{config['prefix']}help")
    # discord.Status.<狀態>，可以是online,offline,idle,dnd,invisible
    await bot.change_presence(status=discord.Status.online, activity=game)
    owner = await bot.fetch_user(config["owner"])
    await owner.send("bot online.")


@bot.event
async def on_guild_join(guild):
    general = guild.system_channel
    if general and general.permissions_for(guild.me).send_messages:
        await general.send(
            "Thanks for adding me!\n"
            "Please set a channel by `$setchannel`.\n"
            "Please set a language by `$setlang`.\n"
            "For more information, please type `$help`."
        )


@bot.command(Name="help")
async def help(ctx):
    await ctx.send(
        "Use `$help` to see the help message.\n"
        "Use `$setchannel` to set a channel.\n"
        "Use `$setlang` to set a language.\n"
        "Use `$say` to speak in voice channel.\n"
        "Use `$join` to let me join to a voice channel.\n"
        "Use `$leave` to let me leave the voice channel.\n"
        "Use `$ping` to check my latency.\n"
    )


@bot.command(Name="join")
async def join(ctx):
    # get user voice channel
    try:
        user_voice_channel = ctx.author.voice.channel
    except AttributeError:
        await ctx.send("Please join a voice channel first.")
    # join
    else:
        try:
            await user_voice_channel.connect()
        except discord.errors.ClientException:
            await ctx.send("I'm already in a voice channel.")


@bot.command(Name="leave")
async def leave(ctx):
    try:
        await ctx.voice_client.disconnect()
    except AttributeError:
        pass


@bot.command(Name="setchannel")
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
    await ctx.send(f"channel set to {channel.name}")


@bot.command(Name="say")
async def say(ctx, *, content: str):  # sourcery skip: for-index-replacement
    # get message channel id
    if content is None:
        await ctx.send("Please input your message.")
    else:
        channel_id = ctx.channel.id
        # get guild id
        guild_id = ctx.guild.id
        if tool_function.check_file(f"db/{guild_id}.json"):
            # read db file
            db = tool_function.read_json(f"db/{guild_id}.json")
            # check channel id
            # check if is in voice channel
            # print(ctx.voice_client.is_connected())
            try:
                ctx.voice_client.is_connected()
            except AttributeError:
                # await ctx.send("Please join a voice channel first.")
                is_connected = False
            else:
                is_connected = True
            if (
                is_connected
                and channel_id == db["channel"]
                and tool_function.check_dict_data(db, "channel")
                and tool_function.check_dict_data(db, "lang")
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
                print("init google tts api")
                # tts_func.process_voice(content, db["lang"])
                print("play mp3")
                """
                mp3file = BytesIO(process_voice(content, db["lang"]))
                voice_file = discord.FFmpegPCMAudio(mp3file)
                """
                subprocess.call(["python", "tts_alone.py", "--content", content, "--lang", db["lang"]])
                voice_file = discord.FFmpegPCMAudio("tts_temp/output.mp3")

                if not ctx.voice_client.is_playing():
                    ctx.voice_client.play(voice_file, after=None)
            else:
                await ctx.send(
                    "Please set channel by `$setchannel`.\n"
                    "Please set language by `$setlang`.\n"
                    "Please join voice channel by `$join`."
                )
        else:
            await ctx.send(
                "Please set channel by `$setchannel`.\n"
                "Please set language by `$setlang`.\n"
            )


@bot.command(Name="setlang")
async def setlang(ctx, lang: str):
    # get guild id
    guild_id = ctx.guild.id
    if tool_function.check_file(f"db/{guild_id}.json"):
        # read db file
        db = tool_function.read_json(f"db/{guild_id}.json")
        # add lang to db
        db["lang"] = lang
        # write to db file
        tool_function.write_json(f"db/{guild_id}.json", db)
    else:
        tool_function.write_json(f"db/{guild_id}.json", {"lang": lang})
    await ctx.send(
        f"Set language to {lang}\n"
        f"Please make sure the code is same as https://cloud.google.com/text-to-speech/docs/voices."
    )


@bot.command(Name="ping")
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")


bot.run(config["token"])
