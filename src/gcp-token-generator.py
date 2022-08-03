import contextlib
import json
import os

with contextlib.suppress(ImportError):
    import dotenv

with contextlib.suppress(NameError):
    dotenv.load_dotenv()

GCP_TOKEN = os.environ["GCP_TOKEN"]
GCP_JSON = json.loads(GCP_TOKEN)

# dump the json to a file
with open("gcp-token.json", "w") as f:
    json.dump(GCP_JSON, f)
