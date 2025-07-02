import os
import subprocess
import sys
import requests

def download_video(url, save_path, target_fps=10, percent_download=40):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Download original video
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(url, headers=headers, stream=True)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024*1024):
            f.write(chunk)
    print(f"Video downloaded to: {save_path}")

    # Probe original duration
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

    # Calculate partial duration (e.g., 40%)
    partial_duration = duration * percent_download / 100

    # Re-encode only partial duration
    base, ext = os.path.splitext(save_path)
    lowfps_path = f"{base}_{target_fps}fps{ext}"
    cmd = [
        "ffmpeg", "-y",
        "-hide_banner", "-loglevel", "error",
        "-ss", "0", "-t", f"{partial_duration:.2f}",
        "-i", save_path,
        "-vf", f"fps={target_fps}",
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-progress", "pipe:1", "-nostats",
        lowfps_path
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

    # Progress bar
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        if line.startswith("out_time_us="):
            raw = line.split("=", 1)[1].strip()
            try:
                out_us = int(raw)
                percent = min(out_us / (partial_duration * 1_000_000) * 100, 100)
                blocks = int(percent * 50 // 100)
                bar = '\033[92m' + "█" * blocks + '\033[0m'
                sys.stdout.write(f"\rRe-encoding: {percent:5.1f}% |{bar:<50}|")
                sys.stdout.flush()
            except ValueError:
                pass

    proc.wait()
    print()  # newline
    print(f"Re-encoded at {target_fps} FPS (first {percent_download}%): {lowfps_path}")
    return lowfps_path
