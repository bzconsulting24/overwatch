# audioTranscriptWithSpeakers.py
import os
from google.oauth2 import service_account
from google.cloud import storage, speech

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
# Set these to match your GCS bucket and service-account JSON
BUCKET_NAME   = "audiodiarize"
KEY_FILE_PATH = r"C:\Users\julius\Documents\vscode codes\behaviorAnalysis\soy-lore-465001-s6-e153c4da9d23.json"

# Optional: map speaker IDs to names
SPEAKER_MAP = {
    1: "Zara",
    2: "Guest",
    # add more if needed
}

# ─── HELPERS ────────────────────────────────────────────────────────────────────

def _get_seconds(tp):
    if hasattr(tp, "total_seconds"):
        return tp.total_seconds()
    if hasattr(tp, "ToTimedelta"):
        return tp.ToTimedelta().total_seconds()
    if hasattr(tp, "ToNanoseconds"):
        return tp.ToNanoseconds() * 1e-9
    return tp.seconds + tp.nanos * 1e-9

def _get_storage_client():
    creds = service_account.Credentials.from_service_account_file(KEY_FILE_PATH)
    return storage.Client(credentials=creds, project=creds.project_id)

def _get_speech_client():
    creds = service_account.Credentials.from_service_account_file(KEY_FILE_PATH)
    return speech.SpeechClient(credentials=creds)

def _clear_bucket():
    client = _get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    for blob in bucket.list_blobs():
        blob.delete()

def _upload_to_gcs(path):
    client = _get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    name = os.path.basename(path)
    blob = bucket.blob(name)
    blob.upload_from_filename(path)
    return f"gs://{BUCKET_NAME}/{name}"

def _format_time(tp):
    total = _get_seconds(tp)
    m = int(total // 60)
    s = total - m * 60
    return f"{m:02d}:{s:06.3f}"

def _format_conversation(words):
    lines = []
    tag = words[0].speaker_tag
    buf = []
    start = words[0].start_time

    for w in words:
        if w.speaker_tag != tag:
            name = SPEAKER_MAP.get(tag, f"Speaker {tag}")
            text = " ".join(buf).capitalize() + "."
            lines.append(f"[{_format_time(start)}] {name}: {text}")
            buf = []
            start = w.start_time
            tag = w.speaker_tag
        buf.append(w.word)

    if buf:
        name = SPEAKER_MAP.get(tag, f"Speaker {tag}")
        text = " ".join(buf).capitalize() + "."
        lines.append(f"[{_format_time(start)}] {name}: {text}")

    return lines

def _detect_events(words, pause_thresh=0.7):
    events = []
    for prev, curr in zip(words, words[1:]):
        gap = _get_seconds(curr.start_time) - _get_seconds(prev.end_time)
        if gap > pause_thresh:
            events.append(f"Pause {gap:.2f}s at {_format_time(prev.end_time)}")
        if curr.word.lower() == prev.word.lower():
            events.append(f"Stutter '{curr.word}' at {_format_time(curr.start_time)}")
    return events

# ─── PUBLIC API ──────────────────────────────────────────────────────────────────

def transcribe_and_diarize(audio_path: str, transcript_path: str):
    """
    1) Clears your GCS bucket
    2) Uploads `audio_path`
    3) Runs diarization (2–4 speakers)
    4) Formats transcript with timestamps and speaker names
    5) Detects pauses and stutters
    6) Writes full transcript to `transcript_path`

    Returns (transcript_text, events_list).
    """
    # 1 & 2
    _clear_bucket()
    uri = _upload_to_gcs(audio_path)

    # 3
    client = _get_speech_client()
    audio = speech.RecognitionAudio(uri=uri)
    diar = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=True,
        min_speaker_count=2,
        max_speaker_count=4,
    )
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        diarization_config=diar,
    )
    op = client.long_running_recognize(config=config, audio=audio)
    response = op.result(timeout=600)
    words = response.results[-1].alternatives[0].words

    # 4 & 5
    convo  = _format_conversation(words)
    events = _detect_events(words)

    # 6
    with open(transcript_path, "w", encoding="utf-8") as f:
        for line in convo:
            f.write(line + "\n")
        for ev in events:
            f.write(ev + "\n")

    transcript_text = "\n".join(convo + events)
    return transcript_text, events

# # ─── EXAMPLE USAGE ───────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     # drop-in test
#     sample_audio = r"C:\Users\julius\Alignerr_vids\audio.wav"
#     out_txt      = r"C:\Users\julius\Alignerr_vids\transcript.txt"
#     text, events = transcribe_and_diarize(sample_audio, out_txt)
#     print("Transcript:\n", text)
#     print("Events:\n", events)

