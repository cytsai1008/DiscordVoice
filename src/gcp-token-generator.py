import json
import os

import dotenv

dotenv.load_dotenv()

GCP_TOKEN = os.getenv("GCP_TOKEN")
GCP_JSON = json.loads(GCP_TOKEN)

# dump the json to a file
with open("gcp-token.json", "w") as f:
    json.dump(GCP_JSON, f, indent=4)
