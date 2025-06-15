import os
import subprocess
import sys
import requests


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
        if line.startswith("out_time_us="):
            raw   = line.split("=", 1)[1].strip()
            out_us = int(raw)
            # now scale by microseconds
            percent = min(out_us / (duration * 1_000_000) * 100, 100)
            blocks  = int(percent * 50 // 100)
            bar     = "█" * blocks
            sys.stdout.write(f"\rRe-encoding: {percent:5.1f}% |{bar:<50}|")
            sys.stdout.flush()


    proc.wait()
    print()  # newline
    print(f"Re-encoded at {target_fps} FPS: {lowfps_path}")
    return lowfps_path