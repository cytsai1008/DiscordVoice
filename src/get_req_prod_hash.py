import hashlib


def get_file_md5(file_path: str) -> str:
    """Get file's md5 hash

    :param file_path: file path
    :return: md5 hash of file
    """

    with open(file_path, "rb") as f:
        md5 = hashlib.md5()
        md5.update(f.read())
        return md5.hexdigest()


def update_hash(req_file_path: str, prod_file_path: str) -> None:
    """Update hash of file

    :param req_file_path: file path
    :param prod_file_path: file path
    """

    with open(req_file_path, "r") as f:
        req_hash = f.readlines()
        req_hash = req_hash[-1]
    req_hash = req_hash.replace("\n", "")
    print(req_hash)

    prod_hash = get_file_md5(prod_file_path)
    prod_hash = f"# prod.txt hash: {prod_hash}"
    print(prod_hash)

    if req_hash != prod_hash:
        # update hash and keep other line unchanged
        with open(req_file_path, "r") as f:
            lines = f.readlines()
        lines[-1] = prod_hash + "\n"
        with open(req_file_path, "w") as f:
            f.writelines(lines)
        print("Hash updated")
    else:
        print("No need to update hash")


if __name__ == "__main__":
    update_hash("requirements.txt", "requirements/prod.txt")
