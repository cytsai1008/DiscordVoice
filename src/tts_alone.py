import argparse

import contextlib

with contextlib.suppress(ImportError):
    import dotenv

parser = argparse.ArgumentParser()
parser.add_argument("--content", required=True)
parser.add_argument("--lang", required=True)
parser.add_argument("--filename", required=True)
parser.add_argument("--platform", required=False, default="Google")

content = parser.parse_args().content
lang_code = parser.parse_args().lang
filename = parser.parse_args().filename
platform = parser.parse_args().platform
str(content)
str(lang_code)
str(filename)

dotenv.load_dotenv()


# noinspection PyTypeChecker
def process_voice(content: str, lang_code: str, filename: str) -> None:
    """Synthesizes speech from the input string of text or ssml.
    Make sure to be working in a virtual environment.

    Note: ssml must be well-formed according to:
        https://www.w3.org/TR/speech-synthesis/
    """
    from google.cloud import texttospeech

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=content)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_code,
        ssml_gender=texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED,
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(f"tts_temp/{filename}", "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print(f'Audio content written to file "{filename}"')


def azure_tts_converter(content: str, lang_code: str, filename: str) -> None:
    import os
    import azure.cognitiveservices.speech as speechsdk

    subscription_key = os.getenv("AZURE_TTS_KEY")

    speech_config = speechsdk.SpeechConfig(
        subscription=subscription_key, region="eastus"
    )
    audio_config = speechsdk.audio.AudioOutputConfig(filename=f"./tts_temp/{filename}")

    # The language of the voice that speaks.
    speech_config.speech_synthesis_language = lang_code

    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )

    # Get text from the console and synthesize to the default speaker.

    speech_synthesizer.speak_text_async(content)
    print(f'Audio content written to file "{filename}"')


if platform == "Google":
    process_voice(content, lang_code, filename)
elif platform == "Azure":
    azure_tts_converter(content, lang_code, filename)
else:
    print("?????")
