import whisper
from pyannote.audio import Pipeline
import os
import torch

def transcribe_and_diarize(audio_path, transcript_path):
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not set in environment variables")

    model = whisper.load_model("base", device="cuda")
    result = model.transcribe(audio_path, verbose=True)

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization",
        use_auth_token=hf_token
    ).to(torch.device("cuda"))
    diarization = pipeline(audio_path)

    def format_time(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"
    

    transcript_lines = []

    zara_phrases = ["got it", "that makes sense", "right", "are you", "can you", "how do", "how would", "what kinds", "clarify", "explain"]

    uncertainty_phrases = [
        "can you repeat", "sorry", "pardon", "didn't hear", 
        "didn't understand", "what was that", "um", "uh"
    ]

    # Identify Zara explicitly as earliest diarized speaker
    first_turn = min(diarization.itertracks(yield_label=True), key=lambda x: x[0].start)
    zara_speaker_id = first_turn[2]

    for idx, segment in enumerate(result["segments"]):
        seg_start = segment["start"]
        seg_end = segment["end"]
        text = segment["text"].strip()
        text_lower = text.lower()

        matched_speaker = None
        smallest_gap = float('inf')

        # Match Whisper segments with diarization speaker by smallest gap
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if turn.start <= seg_end and turn.end >= seg_start:
                matched_speaker = speaker
                break
            else:
                gap = min(abs(turn.start - seg_start), abs(turn.end - seg_end))
                if gap < smallest_gap:
                    smallest_gap = gap
                    matched_speaker = speaker

        # Now explicitly check textual uncertainty to prevent mislabeling
        if (
            matched_speaker == zara_speaker_id 
            and not any(phrase in text_lower for phrase in uncertainty_phrases)
        ) or (
            idx == 0
            or text.endswith("?")
            or any(text_lower.startswith(phrase) for phrase in zara_phrases)
        ):
            speaker_label = "ZARA"
        else:
            speaker_label = "INTERVIEWEE"

        start = format_time(seg_start)
        end = format_time(seg_end)

        transcript_lines.append(f"[{start} - {end}] [{speaker_label}] {text}")

    with open(transcript_path, "w", encoding="utf-8") as f:
        for line in transcript_lines:
            f.write(line + "\n")

    print(f"Speaker-labeled transcript saved to: {transcript_path}")

    return "\n".join(transcript_lines), result


# Sample usage:

# if __name__ == "__main__":
#     import sys
#     import subprocess

#     video_file = "C:\\Users\\julius\\Alignerr_vids\\video.mp4"  # Replace with your test video
#     audio_file = "temp_audio.wav"
#     transcript_file = "transcript.txt"

#     if not os.path.exists(video_file):
#         print(f"❌ Video file not found: {video_file}")
#         sys.exit(1)

#     # Step 1: Extract audio using ffmpeg
#     print("🎞 Extracting audio from video...")
#     try:
#         subprocess.run([
#             "ffmpeg", "-y", "-i", video_file, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", audio_file
#         ], check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"❌ ffmpeg failed: {e}")
#         sys.exit(1)

#     # Step 2: Transcribe and diarize
#     try:
#         print("🔁 Running transcription and diarization...")
#         transcript_text, _ = transcribe_and_diarize(audio_file, transcript_file)
#     except Exception as e:
#         print(f"❌ Transcription failed: {e}")
#         sys.exit(1)

#     # Step 3: Show result
#     if os.path.exists(transcript_file):
#         print(f"\n✅ Transcript saved to {transcript_file}")
#         print("\n📄 Transcript preview:\n" + "-" * 40)
#         with open(transcript_file, "r", encoding="utf-8") as f:
#             print(f.read())
#     else:
#         print("❌ transcript.txt was not created.")

