import os
import shutil
import subprocess
import requests
import opensmile
import sys
# port analyze_speech_pattern
from speechRythm_torch import analyze_speech_pattern
from SpeechPattern import flag_sensitive_words
from AudioTranscript import transcribe_audio
# from soundAnalysis import detect_keyboard_sounds
from soundAnalysis_torch import detect_keyboard_sounds
from BehaviorAnalysis import interpret_behavior
# from pdfCompile import extract_even_frames_with_timestamps, save_frames_to_pdf_and_cleanup
from Openface_Analysis import runOpenface, analyze_behavior

os.system('cls')
os.environ["OPENCV_FFMPEG_READ_ATTEMPTS"] = "20000"  # Increase attempts to read video frames

def clear_output_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path, exist_ok=True)

## ---Download Video---
def download_video(url, save_path, target_fps=10):
    # ensure output folder exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 1) Download the original
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(url, headers=headers, stream=True)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024*1024):
            f.write(chunk)
    print(f"Video downloaded to: {save_path}")

    # 2) If no re-encode requested, return the original
    if not target_fps:
        return save_path

    # 3) Probe duration (in seconds)
    probe = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        save_path
    ]
    try:
        out = subprocess.check_output(probe, stderr=subprocess.DEVNULL)
        duration = float(out.strip())
    except Exception:
        print("[Warning] Could not get duration. Skipping re-encode.")
        return save_path

    # 4) Build ffmpeg command with progress
    base, ext   = os.path.splitext(save_path)
    lowfps_path = f"{base}_{target_fps}fps{ext}"
    cmd = [
        "ffmpeg", "-y",
        "-hide_banner", "-loglevel", "error",
        "-i", save_path,
        "-vf", f"fps={target_fps}",
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-progress", "pipe:1", "-nostats",
        lowfps_path
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

    # 5) Read progress and draw a 50-char bar
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        if line.startswith("out_time_ms="):
            raw = line.split("=", 1)[1].strip()
            try:
                out_ms = int(raw)
            except ValueError:
                continue
            percent = min(out_ms / (duration * 1000) * 100, 100)
            blocks  = int(percent * 50 // 100)
            bar     = "█" * blocks
            sys.stdout.write(f"\rRe-encoding: {percent:5.1f}% |{bar:<50}|")
            sys.stdout.flush()

    proc.wait()
    print()  # newline
    print(f"Re-encoded at {target_fps} FPS: {lowfps_path}")
    return lowfps_path

## ---EXTRACT AUDIO---

def extract_audio(video_path, audio_path):
    # 1. probe for audio
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        has_audio = subprocess.check_output(probe_cmd, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        has_audio = b""
    if not has_audio.strip():
        print("[Info] No audio stream found. Skipping extraction.")
        return None

    # 2. extract audio to WAV
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("[Warning!] Audio extraction failed:")
        print(result.stderr.decode())
        return None

    if not os.path.exists(audio_path):
        print("[Warning!] Audio file not found after ffmpeg run.")
        return None

    print(f"[check] Audio saved to: {audio_path}")
    return audio_path

    
if __name__ == "__main__":
    # === SETTINGS ===
    use_url = True  # Set to False to use a local video file
    video_url = input("Enter video URL:")
    local_video_path = r"C:\Users\julius\Alignerr_vids\video.mp4"
    download_target = r"C:\Users\julius\Alignerr_vids\video.mp4"
    csv_path = r"C:\Users\julius\Alignerr_vids\video.csv"
    
    output_dir = r"C:\Users\julius\Alignerr_vids"
    audio_path = os.path.join(output_dir, "temp_audio.wav")
    transcript_path = os.path.join(output_dir, "transcript.txt")

    clear_output_folder(output_dir)
    video_path = download_video(video_url, download_target) if use_url else local_video_path

    # extract_even_frames_with_timestamps(video_path, output_dir)
    
# --- extract audio and get back a path or None
audio_file = extract_audio(video_path, audio_path)

smile = opensmile.Smile(
    feature_set=opensmile.FeatureSet.ComParE_2016,
    feature_level=opensmile.FeatureLevel.Functionals
)

if audio_file:
    # good WAV, do feature extraction
    features = smile.process_file(audio_file)
else:
    # no audio: skip this step
    print("Bypassing audio analysis.")
    features = None

print(features.head() if features is not None else "No audio features")
# print(features.filter(regex="F0|jitter|energy", axis=1).head())  ## For debugging
if features is not None:
    behavior_summary = interpret_behavior(features)
else:
    print("Skipping behavior analysis (no audio features).")
    behavior_summary = []


runOpenface(video_path, output_dir)
Openface_summary = analyze_behavior(video_path, output_dir)

if os.path.exists(audio_path):
    transcribe_audio(audio_path, transcript_path)
    analyze_speech_pattern(audio_path)
    flagged_summary = flag_sensitive_words(transcript_path)
    sound_summary = detect_keyboard_sounds(audio_path)         

## Append summaries to the transcript file
    with open(transcript_path, "a", encoding="utf-8") as f:
        f.write("\n\n---\n\n")
        f.write(" ### Cheating indicator Analysis\n\n")
        for line in flagged_summary:
            f.write(str(line) + "\n")
        f.write("\n")
        for line in sound_summary:
            f.write(str(line) + "\n")
        f.write("\n")
        f.write("### Behavioral Analysis\n\n")
        for line in behavior_summary:
            f.write(str(line) + "\n")
        f.write("\n")
        f.write("### OpenFace Analysis\n\n")
        for line in Openface_summary:
            f.write(str(line) + "\n")


    os.remove(audio_path)
    # os.remove(video_path)
    os.startfile(output_dir)
    print("Temp audio and video files deleted.")
else:
    print("[X] Skipping analysis: audio file not found.")

