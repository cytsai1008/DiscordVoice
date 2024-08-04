# noinspection PyTypeChecker
async def google_tts_converter(content: str, lang_code: str, filename: str) -> None:
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
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    # The response's audio_content is binary.
    with open(f"tts_temp/{filename}", "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print(f'Audio content written to file "{filename}"')


async def azure_tts_converter(content: str, lang_code: str, filename: str) -> None:
    import os
    from azure.cognitiveservices.speech import (
        SpeechConfig,
        SpeechSynthesizer,
        SpeechSynthesisOutputFormat,
    )
    from azure.cognitiveservices.speech.audio import AudioOutputConfig

    subscription_key = os.getenv("AZURE_TTS_KEY")

    speech_config = SpeechConfig(subscription=subscription_key, region="eastus")
    audio_config = AudioOutputConfig(filename=f"./tts_temp/{filename}")

    # The language of the voice that speaks.
    speech_config.speech_synthesis_language = lang_code

    # Set output format to mp3
    speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat["Audio16Khz128KBitRateMonoMp3"])

    # special case for Chinese Simplified
    if lang_code == "zh-cn":
        speech_config.speech_synthesis_voice_name = "zh-CN-YunxiNeural"

    synthesizer = SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )  # Get text from the console and synthesize to the default speaker.
    synthesizer.speak_text(content)
    print(f'Audio content written to file "{filename}"')
