import os
from google.cloud import speech_v2
from google.cloud.speech_v2.types import cloud_speech

def transcribe_audio_google(audio_file_path, transcript_path, project_id, recognizer_id="_"):
    client = speech_v2.SpeechClient()

    recognizer_name = f"projects/{project_id}/locations/global/recognizers/{recognizer_id}"

    # Verify audio file exists explicitly
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"[ERROR] Audio file missing at: {audio_file_path}")

    with open(audio_file_path, "rb") as audio_file:
        audio_content = audio_file.read()

    config = cloud_speech.RecognitionConfig(
        language_codes=["en-US"],
        model="latest_long",
        features=cloud_speech.RecognitionFeatures(
            diarization_speaker_count=2
        )
    )


    request = cloud_speech.RecognizeRequest(
        recognizer=recognizer_name,
        config=config,
        content=audio_content
    )

    # Explicitly handle transcription request and catch errors
    try:
        response = client.recognize(request=request)
    except Exception as e:
        raise Exception(f"[ERROR] Transcription request failed: {e}")

    # Process the API response explicitly
    transcript_lines = []
    if not response.results:
        print("[WARNING] No transcription results returned.")
    else:
        for result in response.results:
            if not result.alternatives:
                continue
            for word_info in result.alternatives[0].words:
                speaker_tag = word_info.speaker_tag
                word = word_info.word
                transcript_lines.append(f"Speaker {speaker_tag}: {word}")

    # Explicitly ensure transcript is saved
    print(f"[CHECK] Saving transcript explicitly to: {transcript_path}")
    try:
        with open(transcript_path, "w", encoding="utf-8") as f:
            if transcript_lines:
                f.write("\n".join(transcript_lines))
            else:
                f.write("[WARNING] No transcript content available.")
    except Exception as e:
        raise Exception(f"[ERROR] Saving transcript failed: {e}")

    # Confirm explicitly the transcript was saved
    if os.path.exists(transcript_path):
        print("[SUCCESS] Transcript file saved successfully.")
    else:
        print("[ERROR] Transcript file still missing after saving attempt.")

    return "\n".join(transcript_lines), response

if __name__ == "__main__":
    # Example usage explicitly shown:
    audio_file = r"C:\Users\julius\Alignerr_vids\temp_audio.wav"  # Make sure this is the correct audio path
    transcript_path = r"C:\Users\julius\Alignerr_vids\transcript.txt"
    project_id = "speech-2-text-464904"

    # Run the transcription function explicitly
    transcript, response = transcribe_audio_google(audio_file, transcript_path, project_id)

    print("\n=== Transcription Result ===\n")
    print(transcript)
