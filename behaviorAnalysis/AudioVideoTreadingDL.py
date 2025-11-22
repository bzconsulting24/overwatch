import os
import threading
import subprocess
import sys

def probe_duration(url):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        url
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).strip()
    return float(out)

def download_video_part(url, video_path, duration):
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "0", "-t", str(duration),
        "-i", url,
        "-c", "copy",
        "-progress", "pipe:1", "-nostats",
        video_path
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    total_us = duration * 1_000_000
    bar_width = 50

    while True:
        line = proc.stdout.readline()
        if not line:
            break
        if line.startswith("out_time_us="):
            raw = line.split("=", 1)[1].strip()
            try:
                out_us = int(raw)
                pct = min(out_us / total_us * 100, 100)
                blocks = int(bar_width * pct / 100)
                bar = "█" * blocks + "-" * (bar_width - blocks)
                sys.stdout.write(f"\rVideo-Audio: {pct:5.1f}% |{bar}|")
                sys.stdout.flush()
            except ValueError:
                pass

    proc.wait()
    sys.stdout.write("\n")
    print("Video saved:", video_path)

def download_audio_part(url, audio_path, duration):
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "0", "-t", str(duration),
        "-i", url,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        audio_path
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    _, stderr = proc.communicate()
    if proc.returncode != 0:
        print("Audio download failed:", stderr.strip())
    else:
        print("Audio saved:", audio_path)

def download_video_audio(url, output_dir, percent_download=40):
    import shutil
    duration = probe_duration(url)
    partial = duration * percent_download / 100

    os.makedirs(output_dir, exist_ok=True)
    video_path = os.path.join(output_dir, "video.mp4")
    audio_path = os.path.join(output_dir, "audio.wav")
    playback_path = os.path.join(output_dir, "playback.mp4")

    t_video = threading.Thread(target=download_video_part, args=(url, video_path, partial))
    t_audio = threading.Thread(target=download_audio_part, args=(url, audio_path, partial))

    t_video.start()
    t_audio.start()

    t_video.join()

    # Convert using GPU acceleration for faster encoding
    if os.path.exists(video_path):
        print("Converting with GPU acceleration for playback...")
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-hwaccel", "cuda",  # GPU acceleration
            "-i", video_path,
            "-c:v", "h264_nvenc",  # NVIDIA GPU encoder
            "-preset", "fast",  # Fast encoding preset
            "-b:v", "2M",  # 2 Mbps video bitrate
            "-c:a", "aac", "-b:a", "192k",  # AAC audio
            playback_path
        ]
        subprocess.run(cmd, check=True)
        print("GPU-accelerated playback video created:", playback_path)

    t_audio.join()

    print("Both downloads complete.")
    return video_path, audio_path, playback_path



# ## Example usage
# if __name__ == "__main__":
#     url = "https://storage.googleapis.com/lb-alignerr-prod-e-7c6-interviews/55910f19-2e2e-4368-9afa-1810937f5979/video.mp4?GoogleAccessId=gsda-cm473k27a06l907xn0v0c68rj@labelbox-193903.iam.gserviceaccount.com&Expires=1752108911&Signature=nvndZXhERmS9uaQfO%2FYdxf75vt%2Fs4DCwLVjGLrSmnQJ71uFXUnuHAL1DTxwpv9WT5xkewi3o2FDR6FTVjjCgwLfabeHFBkd5kNPoMwne%2B2NPM90ksk4SAl%2FvVCzQ%2BDazUnTL7UcwI%2FchERr60JkMnxE7o%2FsUUFMUCTY3q4w6n2KtT7Rq2FE3NizrNEGYlSehJoInBsXul%2BctDFiN%2FE4AK3IqSDo7hOr1utBPAnC6rOh6k5%2Fq03SP7VBnE4SZTR4vFwM9zNMOFjTKkXu2I0CtDggeA7%2BF7JDaAwQPhgOI4MaGeIkDi6z9ziKO2LuniPRkB%2FwfH1DOnjyceJfV3dx4Zw%3D%3D"
#     out_dir = r"C:\Users\julius\Alignerr_vids"
#     download_video_audio(url, out_dir)
