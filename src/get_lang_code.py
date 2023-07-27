import asyncio
import contextlib
import json
import os

import google.cloud.texttospeech as tts
import httpx

with contextlib.suppress(ImportError):
    import dotenv

with contextlib.suppress(NameError):
    dotenv.load_dotenv()


async def google_get_languages():
    def google_process_voice_languages(voices):
        language_set = set()
        for voice in voices:
            for language_code in voice.language_codes:
                language_set.add(language_code)
        return language_set

    print("Updating google_languages.json...")
    client = tts.TextToSpeechClient()
    response = client.list_voices()
    languages = google_process_voice_languages(response.voices)
    languages = (
        str(languages).replace("{", "").replace("}", "").replace("'", "").lower()
    )
    languages = languages.replace("cmn", "zh")
    languages = list(languages.split(", "))
    languages = sorted(languages)
    json_lang = {"Support_Language": languages}
    with open("lang_list/google_languages.json", "w") as f:
        json.dump(json_lang, f)

    return


async def azure_get_languages():
    print("Updating azure_languages.json...")

    subscription_key = os.getenv("AZURE_TTS_KEY")

    def get_token(sub_key):
        fetch_token_url = (
            "https://eastus.tts.speech.microsoft.com/cognitiveservices/voices/list"
        )
        headers = {"Ocp-Apim-Subscription-Key": sub_key}
        response = httpx.get(fetch_token_url, headers=headers)
        return response.json()

    azure_lang = get_token(subscription_key)
    with open("azure_raw.json", "w", encoding="utf-8") as f:
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

    return


async def main():
    tasks = [
        asyncio.create_task(google_get_languages()),
        asyncio.create_task(azure_get_languages()),
    ]
    await asyncio.gather(*tasks)

    return


if __name__ == "__main__":
    asyncio.run(main())
