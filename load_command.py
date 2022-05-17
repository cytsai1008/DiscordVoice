def read_description(command, language):
    with open(f"commands/{command}/{language}.txt", "r", encoding="utf-8") as f:
        return f.read()
