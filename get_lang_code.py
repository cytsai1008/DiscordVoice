import google.cloud.texttospeech as tts
import dotenv
import json

dotenv.load_dotenv()


def unique_languages_from_voices(voices):
    language_set = set()
    for voice in voices:
        for language_code in voice.language_codes:
            language_set.add(language_code)
    return language_set


def list_languages():
    client = tts.TextToSpeechClient()
    response = client.list_voices()
    languages = unique_languages_from_voices(response.voices)
    languages = str(languages).replace("{", "").replace("}", "").replace("'", "").lower()
    languages = languages.replace("cmn", "zh")
    languages = list(languages.split(", "))
    languages = sorted(languages)
    json_lang = {"Support_Language": languages}
    with open('languages.json', 'w') as f:
        json.dump(json_lang, f)


if __name__ == '__main__':
    list_languages()
