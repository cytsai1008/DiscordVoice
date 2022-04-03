def read_description(command, language):
    with open(
        "commands/{}/{}.txt".format(command, language), "r", encoding="utf-8"
    ) as f:
        return f.read()
