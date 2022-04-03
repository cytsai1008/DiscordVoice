import json
import os


# import load_command


def read_json(filename) -> dict:
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def write_json(filename, data) -> None:
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


"""
def check_json(filename) -> dict:
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    return data
"""


def check_args_zero(args, arg_list) -> bool:
    return args in arg_list


def id_check(self) -> str:
    try:
        server_id = str(self.guild.id)
    except:
        server_id = "user_" + str(self.author.id)
    return server_id


def check_args_one(args) -> bool:
    return args is not type(None)
    # return False if args is type(None)


def check_dict_data(data: dict, arg) -> bool:
    try:
        print(f"data in {arg} is {data[arg]}")
    except KeyError:
        return False
    else:
        return True


def check_duplicate_data(existing_data, new_data: list) -> list:
    # sourcery skip: for-index-replacement
    del_key = []
    for i in range(len(existing_data)):
        for j in range(len(new_data)):
            if existing_data[i] == new_data[j]:
                del_key.append(new_data[j])
    return del_key


def check_file(filename) -> bool:
    return bool(os.path.exists(filename))


"""
def lang_command(lang: str, command: str) -> str:
    try:
        command_out = load_command.read_description(lang, command)
    except FileNotFoundError:
        command_out = load_command.read_description("en", command)
    finally:
        return command_out
"""

# TODO: time commands function
# TODO: Merging functions to main.py
