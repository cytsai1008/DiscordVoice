import logging
import os
import random
import signal
# import subprocess
from datetime import datetime

import discord
import dotenv
from discord.ext import commands

import load_command
import wfnm_tool_function as tool_function

# import time

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
if not os.path.exists("Log"):
    os.mkdir("Log")
handler = logging.FileHandler(filename="Log/discord_wfnm.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

dotenv.load_dotenv()

token = {
    "token": os.getenv("DISCORD_WFNM_TOKEN"),
    "owner": int(os.getenv("DISCORD_OWNER")),
    "prefix": os.getenv("DISCORD_WFNM_PREFIX"),
}

bot = commands.Bot(command_prefix=token["prefix"], help_command=None, case_insensitive=True)

help_zh_tw = load_command.read_description("help", "zh-tw")
add_zh_tw = load_command.read_description("add", "zh-tw")
remove_zh_tw = load_command.read_description("remove", "zh-tw")
list_zh_tw = load_command.read_description("list", "zh-tw")
random_zh_tw = load_command.read_description("random", "zh-tw")

support_meal = ["breakfast", "lunch", "afternoon_tea", "dinner"]
meal_time = {
    "breakfast": [5, 10],
    "lunch": [10, 15],
    "afternoon_tea": [15, 20],
    "dinner": [20, 23],
    "sleep": [23, 24, 0, 5],
}

bot.remove_command("help")


# 調用 event 函式庫
@bot.event
# 當機器人完成啟動時
async def on_ready():
    print("目前登入身份：", bot.user)
    game = discord.Game("nm!help")
    # discord.Status.<狀態>，可以是online,offline,idle,dnd,invisible
    await bot.change_presence(status=discord.Status.online, activity=game)
    owner = await bot.fetch_user(token["owner"])
    await owner.send("bot bootup.")


@bot.event
async def on_guild_join(guild):
    general = guild.system_channel
    if general and general.permissions_for(guild.me).send_messages:
        await general.send(
            "Thanks for adding me into your server!\n"
            f"Please use `{token['prefix']}help` for more information.\n"
            f"`{token['prefix']}time <hours from London>` to setup the timezone.\n"
            "感謝您邀請我進入伺服器\n"
            f"請使用 `{token['prefix']}help` 取得更多資訊\n"
            f"並透過 `{token['prefix']}time <與倫敦相差小時數>` 設定時區"
        )


"""
@bot.event
async def change_presence():
    while True:
        rand_stat = random.choice(
            ['nm!help', 'nm!ping', 'nm!show', 'nm!choose', 'https://github.com/cytsai1008/What-For-Next-Meal',
             'nm!lists', 'nm!add', 'nm!remove', 'nm!random'])
        rand_game = discord.Game(rand_stat)
        print(type(rand_game))
        await bot.change_presence(status=discord.Status.online, activity=rand_game)
        await asyncio.sleep(10)
"""

"""
@client.event

async def status():
    game1 = discord.Game('吃拉麵')
    game2 = discord.Game('吃咖哩')
    game3 = discord.Game('吃壽司')
    game4 = discord.Game('吃火鍋')
    game5 = discord.Game('吃麵包')

    async def game_status():
        await client.change_presence(activity=game1)
        await asyncio.sleep(5)
        await client.change_presence(activity=game2)
        await asyncio.sleep(5)
        await client.change_presence(activity=game3)
        await asyncio.sleep(5)
        await client.change_presence(activity=game4)
        await asyncio.sleep(5)
        await client.change_presence(activity=game5)
        await asyncio.sleep(5)

    await game_status()

    await status()
"""


@bot.command(Name="help")
async def help(ctx):
    await ctx.send(help_zh_tw)


@bot.command(Name="ping")
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")


@bot.command(Name="sl")
async def sl(ctx):
    await ctx.send(
        "Social Credit 👎\n"
        "https://www.idlememe.com/wp-content/uploads/2021/10/social-credit-meme-idlememe.jpg"
    )


@bot.command(Name="add")
async def add(ctx, *args):
    meal_list = list(args)
    server_id = tool_function.id_check(ctx.message)
    print(server_id)
    try:
        if not tool_function.check_args_zero(args[0], support_meal):
            await ctx.send(add_zh_tw)
            # print("Error 01")
            # Check args is correct
        elif not tool_function.check_args_one(args[1]):
            await ctx.send(add_zh_tw)
            # print("Error 02")
            # Check add data exists
        elif tool_function.check_file(f"{server_id}"):
            # Check json exists
            data = tool_function.read_json(f"{server_id}")
            del meal_list[0]
            # del args[0] from meal_list
            before_del = len(meal_list)
            if not tool_function.check_dict_data(data, args[0]):
                data[args[0]] = []
                # Check Key exists
            del_list = []
            del_list = tool_function.check_duplicate_data(data[args[0]], meal_list)
            # Add duplicate to del_list to delete
            # print(del_list)
            for k in range(len(del_list)):
                meal_list.remove(del_list[k])
                # Cleanup duplicate meal_list
            for meal in meal_list:
                data[args[0]].append(meal)
                # Append meal_list to data
            after_del = len(meal_list)
            print(args[0])
            print(meal_list)
            print(data)
            duplicate_len = before_del - after_del
            if not meal_list:
                await ctx.send(f"0 food added to {args[0]}")
            elif len(meal_list) >= 2:
                await ctx.send(
                    f"{len(meal_list)} foods add into {args[0]} ({duplicate_len} duplicate)"
                )

            elif len(meal_list) == 1:
                await ctx.send(
                    f"{len(meal_list)} food add into {args[0]} ({duplicate_len} duplicate)"
                )

            tool_function.write_json(f"{server_id}", data)
            # Save data to json
        else:
            del meal_list[0]
            add_meal = {args[0]: meal_list}
            tool_function.write_json(f"{server_id}", add_meal)
            duplicate_len = 0
            if len(meal_list) >= 2:
                await ctx.send(
                    f"{len(meal_list)} foods add into {args[0]} ({duplicate_len} duplicate)"
                )

            else:
                await ctx.send(
                    f"{len(meal_list)} food add into {args[0]} ({duplicate_len} duplicate)"
                )

                # Add new json to db
                # print("Warning 01")

    except IndexError:
        await ctx.send(add_zh_tw)
        # print("Error 03")
    # If no args given


@bot.command(Name="remove")
async def remove(ctx, *args):
    del_list = list(args)
    server_id = tool_function.id_check(ctx.message)
    print(server_id)
    try:
        if not tool_function.check_args_zero(args[0], support_meal):
            await ctx.send(remove_zh_tw)
            # print("Error 01")
            # Check args is correct
        elif not tool_function.check_args_one(args[1]):
            await ctx.send(remove_zh_tw)
            # print("Error 02")
            # Check remove data exists
        elif tool_function.check_file(f"{server_id}"):
            # Check json exists
            data = tool_function.read_json(f"{server_id}")
            del del_list[0]
            # del args[0] from del_list
            before_del = len(del_list)
            if not tool_function.check_dict_data(data, args[0]):
                data[args[0]] = []
                # Check Key exists
            # print(f"data is {data}")
            try:
                del_key = tool_function.check_duplicate_data(data[args[0]], del_list)
            except:
                del_key = []
            # Cleanup duplicate meal_list
            print(f"del_list is {del_list}")
            for item in del_key:
                data[args[0]].remove(item)
                # Remove del_list to data
            after_del = len(del_key)

            wrong_data = before_del - after_del
            if not del_key:
                await ctx.send(
                    f"0 food deleted from {args[0]} ({wrong_data} not found)"
                )
            elif len(del_key) >= 2:
                await ctx.send(f"{len(del_key)} foods deleted from {args[0]} ({wrong_data} not found)")

            elif len(del_key) == 1:
                await ctx.send(f"{len(del_key)} food deleted from {args[0]} ({wrong_data} not found)")

            tool_function.write_json(f"{server_id}", data)
            # Save data to json
        else:
            tool_function.write_json(f"{server_id}", {})
            # Add new json to db
            await ctx.send(f"No food in {args[0]}")
            # print("Warning 01")
    except IndexError:
        await ctx.send(remove_zh_tw)


@bot.command(Name="show")
async def show(ctx, *args):  # sourcery no-metrics
    server_id = tool_function.id_check(ctx.message)
    print(server_id)
    try:
        if not tool_function.check_args_zero(args[0], support_meal):
            await ctx.send(list_zh_tw)
            # print("Error 01")
            # Check args is correct
        elif tool_function.check_file(f"{server_id}"):
            # Check json exists
            data = tool_function.read_json(f"{server_id}")
            # Load json to data
            try:
                print(data[args[0]])
            except KeyError:
                await ctx.send(f"No food in {args[0]}")
            else:
                if len(data[args[0]]) == 0:
                    await ctx.send(f"No food in {args[0]}")
                else:
                    str_data = ", ".join(data[args[0]])
                    await ctx.send(f"{args[0]} list: {str_data}")
        else:
            tool_function.write_json(f"{server_id}", {})
            await ctx.send(f"No food in {args[0]}")
            # print("Warning 01")
    except IndexError:
        if tool_function.check_file(f"{server_id}"):
            data = tool_function.read_json(f"{server_id}")
            # Load json to data
            if len(data) == 0:
                await ctx.send("No food in any list")
            else:
                # TODO: Need to rewrite to for loop someday
                """
                for i in support_meal:
                    try:
                        variables[str(support_meal[i-1])] = data[support_meal[i-1]]
                    except KeyError:
                        variables[str(support_meal[i-1])] = data[support_meal[i-1]]
                """
                try:
                    breakfast = data["breakfast"]
                except KeyError:
                    breakfast = []
                try:
                    lunch = data["lunch"]
                except KeyError:
                    lunch = []
                try:
                    afternoon_tea = data["afternoon_tea"]
                except KeyError:
                    afternoon_tea = []
                try:
                    dinner = data["dinner"]
                except KeyError:
                    dinner = []
                breakfast = ", ".join(breakfast)
                lunch = ", ".join(lunch)
                afternoon_tea = ", ".join(afternoon_tea)
                dinner = ", ".join(dinner)
                await ctx.send(
                    f"breakfast list: {breakfast}\n"
                    f"lunch list: {lunch}\n"
                    f"afternoon tea list: {afternoon_tea}\n"
                    f"dinner list: {dinner}"
                )
        else:
            tool_function.write_json(f"{server_id}", {})
            await ctx.send("No food in any list")
        # print("Error 03")


@bot.command(Name="lists")
async def lists(ctx, *args):  # sourcery no-metrics
    server_id = tool_function.id_check(ctx.message)
    print(server_id)
    try:
        if not tool_function.check_args_zero(args[0], support_meal):
            await ctx.send(list_zh_tw)
            # print("Error 01")
            # Check args is correct
        elif tool_function.check_file(f"{server_id}"):
            # Check json exists
            data = tool_function.read_json(f"{server_id}")
            # Load json to data
            try:
                print(data[args[0]])
            except KeyError:
                await ctx.send(f"No food in {args[0]}")
            else:
                if len(data[args[0]]) == 0:
                    await ctx.send(f"No food in {args[0]}")
                else:
                    str_data = ", ".join(data[args[0]])
                    await ctx.send(f"{args[0]} list: {str_data}")
        else:
            tool_function.write_json(f"{server_id}", {})
            await ctx.send(f"No food in {args[0]}")
            # print("Warning 01")
    except IndexError:
        if tool_function.check_file(f"{server_id}"):
            data = tool_function.read_json(f"{server_id}")
            # Load json to data
            if len(data) == 0:
                await ctx.send("No food in any list")
            else:
                # TODO: Need to rewrite to for loop someday
                """
                for i in support_meal:
                    try:
                        variables[str(support_meal[i-1])] = data[support_meal[i-1]]
                    except KeyError:
                        variables[str(support_meal[i-1])] = data[support_meal[i-1]]
                """
                try:
                    breakfast = data["breakfast"]
                except KeyError:
                    breakfast = []
                try:
                    lunch = data["lunch"]
                except KeyError:
                    lunch = []
                try:
                    afternoon_tea = data["afternoon_tea"]
                except KeyError:
                    afternoon_tea = []
                try:
                    dinner = data["dinner"]
                except KeyError:
                    dinner = []
                breakfast = ", ".join(breakfast)
                lunch = ", ".join(lunch)
                afternoon_tea = ", ".join(afternoon_tea)
                dinner = ", ".join(dinner)
                await ctx.send(
                    f"breakfast list: {breakfast}\n"
                    f"lunch list: {lunch}\n"
                    f"afternoon tea list: {afternoon_tea}\n"
                    f"dinner list: {dinner}"
                )
        else:
            tool_function.write_json(f"{server_id}", {})
            await ctx.send("No food in any list")
        # print("Error 03")


@bot.command(Name="choose")
async def choose(ctx, *args):  # sourcery no-metrics
    server_id = tool_function.id_check(ctx.message)
    print(server_id)
    try:
        if not tool_function.check_args_zero(args[0], support_meal):
            await ctx.send(list_zh_tw)
            # print("Error 01")
            # Check args is correct
        elif tool_function.check_file(f"{server_id}"):
            # Check json exists
            data = tool_function.read_json(f"{server_id}")
            # Load json to data
            if not tool_function.check_dict_data(data, args[0]):
                await ctx.send(f"No food in {args[0]}")
            elif len(data[args[0]]) == 0:
                await ctx.send(f"No food in {args[0]}")
            else:
                random.seed(str(datetime.now()))
                # print(datetime.now())
                random_food = random.choice(data[args[0]])
                await ctx.send(f"Random food in {args[0]}: {random_food}")
        else:
            tool_function.write_json(f"{server_id}", {})
            await ctx.send(f"No food in {args[0]}")
            # print("Warning 01")
    except:
        current_utc = datetime.utcnow()
        current_utc = current_utc.hour
        if os.path.exists(f"{server_id}"):

            try:
                data = tool_function.read_json(f"{server_id}")
                print(data["timezone"])
                # Load json to data
            except KeyError:
                await ctx.send(f'Please use `{token["prefix"]}time` to setup timezone.')
            else:
                current_time = current_utc + data["timezone"]
                if current_time >= 24:
                    current_time = current_time - 24
                elif current_time < 0:
                    current_time = current_time + 24
                try:
                    if current_time in range(5, 10):
                        if len(data["breakfast"]) == 0:
                            await ctx.send("No food in breakfast")
                        else:
                            random.seed(str(datetime.now()))
                            # print(datetime.now())
                            random_food = random.choice(data["breakfast"])
                            await ctx.send(f"Random food in breakfast: {random_food}")
                    elif current_time in range(10, 15):
                        if len(data["lunch"]) == 0:
                            await ctx.send("No food in lunch")
                        else:
                            random.seed(str(datetime.now()))
                            # print(datetime.now())
                            random_food = random.choice(data["lunch"])
                            await ctx.send(f"Random food in lunch: {random_food}")
                    elif current_time in range(15, 17):
                        if len(data["afternoon_tea"]) == 0:
                            await ctx.send("No food in afternoon tea")
                        else:
                            random.seed(str(datetime.now()))
                            # print(datetime.now())
                            random_food = random.choice(data["afternoon_tea"])
                            await ctx.send(
                                f"Random food in afternoon tea: {random_food}"
                            )
                    elif current_time in range(17, 23):
                        if len(data["dinner"]) == 0:
                            await ctx.send("No food in dinner")
                        else:
                            random.seed(str(datetime.now()))
                            # print(datetime.now())
                            random_food = random.choice(data["dinner"])
                            await ctx.send(f"Random food in dinner: {random_food}")
                    elif current_time in range(23, 24) or current_time in range(5):
                        await ctx.send("Go to sleep.")
                    else:
                        await ctx.send(
                            "I don't know how did you trigger this, please contact `@(⊙ｏ⊙)#6773`."
                        )
                except KeyError:
                    if current_time in range(5, 10):
                        await ctx.send("No food in breakfast")
                    elif current_time in range(10, 15):
                        await ctx.send("No food in lunch")
                    elif current_time in range(14, 17):
                        await ctx.send("No food in afternoon tea")
                    elif current_time in range(17, 23):
                        await ctx.send("No food in dinner")
                    elif current_time in range(23, 24) or current_time in range(5):
                        await ctx.send("Go to sleep.")
                    else:
                        await ctx.send(
                            "I don't know how did you trigger this, please contact `@(⊙ｏ⊙)#6773`."
                        )

        # print("Error 03")


@bot.command(Name="shutdown")
async def shutdown(ctx):
    sender = int(ctx.message.author.id)
    owner = int(token["owner"])
    if sender == owner:
        await ctx.reply("Shutting down...")
        # send SIGTERM to the bot process
        os.kill(os.getpid(), signal.SIGTERM)


@bot.command(Name="time")
async def time(ctx, *args):
    server_id = tool_function.id_check(ctx.message)
    try:
        tz = int(args[0])
        if tz != int(args[0]):
            await ctx.send("Please input a integer number.")
        elif len(args) >= 2:
            await ctx.send("Too many entry.")
        elif tz < -12 or tz > 12:
            await ctx.send("Please input a number between -12 and 12.")
        elif tool_function.check_file(f"{server_id}"):
            data = tool_function.read_json(f"{server_id}")
            data["timezone"] = tz
            # print(data['timezone'])
            tool_function.write_json(f"{server_id}", data)
            if data["timezone"] >= 0:
                await ctx.send(f"Timezone is set to UTC+{data['timezone']}")
            else:
                await ctx.send(f"Timezone is set to UTC{data['timezone']}")
        else:
            data = {"timezone": tz}
            tool_function.write_json(f"{server_id}", data)
            if data["timezone"] >= 0:
                await ctx.send(f"Timezone set to UTC+{data['timezone']}")
            else:
                await ctx.send(f"Timezone set to UTC{data['timezone']}")
    except IndexError:
        if tool_function.check_file(f"{server_id}"):
            data = tool_function.read_json(f"{server_id}")
            if not tool_function.check_dict_data(data, "timezone"):
                await ctx.send("No timezone set, please input number to set.")
            elif data["timezone"] >= 0:
                await ctx.send(f"Timezone is set to UTC+{data['timezone']}")
            else:
                await ctx.send(f"Timezone is set to UTC{data['timezone']}")
        else:
            tool_function.write_json(f"{server_id}", {})


"""
@bot.command(Name="update")
async def update(ctx):
    sender = ctx.message.author.id
    owner = token["owner"]
    if sender == owner:
        await ctx.send("Updating...")
        git_proc = subprocess.check_output(["git", "pull"]).decode("utf-8")
        print(git_proc)
        await ctx.send(git_proc)
        await bot.close()
        subprocess.run(["python", "wfnm_main.py"])
"""


@bot.command(Name="reboot")
async def reboot(ctx):
    sender = int(ctx.message.author.id)
    owner = int(token["owner"])
    if sender == owner:
        await ctx.reply("Rebooting...")
        await bot.close()


bot.run(token["token"])
