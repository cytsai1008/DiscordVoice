def read_description(command, language):
    with open(f"wfnm_cmd_list/{command}/{language}.txt", "r", encoding="utf-8") as f:
        return f.read()
