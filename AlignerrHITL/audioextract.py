import subprocess

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