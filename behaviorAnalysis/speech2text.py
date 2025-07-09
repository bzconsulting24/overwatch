import os
from google.cloud import speech_v2
from google.cloud.speech_v2.types import cloud_speech
import requests

# Explicitly set your credentials here clearly:
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\julius\speech-2-text-464904-2675de5d0b16.json"

def transcribe_audio_google(audio_file_path, transcript_path, project_id, recognizer_id="_"):
    client = speech_v2.SpeechClient()

    recognizer_name = f"projects/{project_id}/locations/global/recognizers/{recognizer_id}"

    with open(audio_file_path, "rb") as audio_file:
        audio_content = audio_file.read()

    config = cloud_speech.RecognitionConfig(
        language_codes=["en-US"],
        model="latest_long",
        features=cloud_speech.RecognitionFeatures(
            enable_speaker_diarization=True,
            diarization_speaker_count=2,
        ),
    )

    request = cloud_speech.RecognizeRequest(
        recognizer=recognizer_name,
        config=config,
        content=audio_content
    )

    response = client.recognize(request=request)

    transcript_lines = []
    for result in response.results:
        for word_info in result.alternatives[0].words:
            speaker_tag = word_info.speaker_tag
            word = word_info.word
            transcript_lines.append(f"Speaker {speaker_tag}: {word}")
            
    print(f"[CHECK] Saving transcript to: {transcript_path}")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write("\n".join(transcript_lines))
        
    if not os.path.exists(transcript_path):
        print("[ERROR] Transcript file still missing after saving attempt.")
    else:
        print("[SUCCESS] Transcript file saved successfully.")

    return "\n".join(transcript_lines), response
