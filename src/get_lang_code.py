import contextlib
import json
import multiprocessing
import os

with contextlib.suppress(ImportError):
    import dotenv

import google.cloud.texttospeech as tts

with contextlib.suppress(NameError):
    dotenv.load_dotenv()


def unique_languages_from_voices(voices):
    language_set = set()
    for voice in voices:
        for language_code in voice.language_codes:
            language_set.add(language_code)
    return language_set


def list_languages():
    print("Updating google_languages.json...")
    client = tts.TextToSpeechClient()
    response = client.list_voices()
    languages = unique_languages_from_voices(response.voices)
    languages = (
        str(languages).replace("{", "").replace("}", "").replace("'", "").lower()
    )
    languages = languages.replace("cmn", "zh")
    languages = list(languages.split(", "))
    languages = sorted(languages)
    json_lang = {"Support_Language": languages}
    with open("lang_list/google_languages.json", "w") as f:
        json.dump(json_lang, f)


def list_azure_languages():
    print("Updating azure_languages.json...")
    # Request module must be installed.
    # Run pip install requests if necessary.
    import requests

    subscription_key = os.getenv("AZURE_TTS_KEY")

    def get_token(subscription_key):
        fetch_token_url = (
            "https://eastus.tts.speech.microsoft.com/cognitiveservices/voices/list"
        )
        headers = {"Ocp-Apim-Subscription-Key": subscription_key}
        response = requests.get(fetch_token_url, headers=headers)
        return response.json()

    azure_lang = get_token(subscription_key)
    with open("azure_raw.json", "w") as f:
        json.dump(azure_lang, f, indent=2, ensure_ascii=False)
    azure_langs = []

    for i in range(len(azure_lang)):
        if azure_lang[i]["Locale"] not in azure_langs:
            azure_langs.append(azure_lang[i]["Locale"])

    azure_langs = [x.lower() for x in azure_langs]
    azure_langs = sorted(azure_langs)

    azure_langs = {"Support_Language": azure_langs}
    with open("lang_list/azure_languages.json", "w") as f:
        json.dump(azure_langs, f)


if __name__ == "__main__":
    azure_multi = multiprocessing.Process(target=list_azure_languages)
    google_multi = multiprocessing.Process(target=list_languages)
    azure_multi.start()
    google_multi.start()
    # Why it returns 0xC0000005 error? Reason: google.cloud.texttospeech bug :(
