import logging
import os
# import sys
import subprocess

import pycld2
# from datetime import datetime
from dotenv import load_dotenv
# from google.cloud import texttospeech

import discord
from discord.ext import commands

import load_command
import tool_function
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
        )


@bot.command(Name="help")
async def help(ctx):
    await ctx.send("help")


@bot.command(Name="join")
async def join(ctx):
    # get user voice channel
    user_voice_channel = ctx.author.voice.channel
    # join
    await user_voice_channel.connect()


@bot.command(Name="leave")
async def leave(ctx):
    await ctx.voice_client.disconnect()


@bot.command(Name="setchannel")
async def setchannel(ctx, channel: discord.TextChannel):
    # get channel id
    channel_id = channel.id
    # get guild id
    guild_id = ctx.guild.id
    # write to db folder with guild id filename
    tool_function.write_json(f"db/{guild_id}.json", {"channel": channel_id})
    await ctx.send(f"Set channel to {channel.mention}")


@bot.command(Name="say")
async def say(ctx, *, content: str):  # sourcery skip: for-index-replacement
    # get message channel id
    channel_id = ctx.channel.id
    # get guild id
    guild_id = ctx.guild.id
    if tool_function.check_file(f"db/{guild_id}.json"):
        # read db file
        db = tool_function.read_json(f"db/{guild_id}.json")
        # check channel id
        # check if is in voice channel
        # print(ctx.voice_client.is_connected())
        if ctx.voice_client.is_connected() and channel_id == db["channel"]:
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
            subprocess.call(["python", "tts_alone.py", "--content", content, "--lang", db["lang"]])

            # play mp3
            print("play mp3")
            voice_file = discord.FFmpegPCMAudio(f"{os.environ['TEMP']}/output.mp3")
            if not ctx.voice_client.is_playing():
                ctx.voice_client.play(voice_file, after=None)


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
        await ctx.send(f"Set language to {lang}\n"
                       f"Please make sure the code is same as https://cloud.google.com/text-to-speech/docs/voices.")


bot.run(config["token"])