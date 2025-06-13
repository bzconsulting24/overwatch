import os
import cv2
import shutil
import numpy as np
from PIL import Image
import whisper
import subprocess
import requests

def clear_output_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path, exist_ok=True)

def download_video(url, save_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    }
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
        print(f"Video downloaded to: {save_path}")
        return save_path
    else:
        raise Exception(f"Download failed: HTTP {response.status_code}")

def extract_even_frames_with_timestamps(video_path, output_folder, num_frames=100, resize_width=640, resize_height=360):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

    for count, i in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        success, frame = cap.read()
        if not success:
            continue

        timestamp_sec = i / fps
        minutes = int(timestamp_sec // 60)
        seconds = int(timestamp_sec % 60)
        millis = int((timestamp_sec % 1) * 1000)
        timestamp_text = f"{minutes:02d}:{seconds:02d}.{millis:03d}"

        frame_resized = cv2.resize(frame, (resize_width, resize_height))
        cv2.putText(frame_resized, timestamp_text, (10, 30),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8,
                    color=(255, 255, 255), thickness=2, lineType=cv2.LINE_AA)

        frame_filename = os.path.join(output_folder, f"frame_{count:02d}.webp")
        cv2.imwrite(frame_filename, frame_resized)

    cap.release()
    print(f"Saved {num_frames} timestamped frames to: {output_folder}")

def save_frames_to_pdf_and_cleanup(output_folder, pdf_filename="video_frames.pdf"):
    images = sorted([
        os.path.join(output_folder, f)
        for f in os.listdir(output_folder)
        if f.startswith("frame_") and f.endswith(".webp")
    ])

    if not images:
        print("No images found for PDF.")
        return

    image_list = [Image.open(img).convert("RGB") for img in images]
    pdf_path = os.path.join(output_folder, pdf_filename)
    image_list[0].save(pdf_path, save_all=True, append_images=image_list[1:])
    print(f"PDF saved to: {pdf_path}")

    for img_path in images:
        os.remove(img_path)
    print("Temporary frames deleted.")

def extract_audio(video_path, audio_path):
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    

def transcribe_audio(audio_path, transcript_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, verbose=False)

    def format_time(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"

    with open(transcript_path, "w", encoding="utf-8") as f:
        if "segments" in result:
            for segment in result["segments"]:
                start = format_time(segment["start"])
                end = format_time(segment["end"])
                text = segment["text"].strip()
                f.write(f"[{start} - {end}] {text}\n")
        else:
            f.write(result.get("text", "").strip())

    print(f"Timestamped transcript saved to: {transcript_path}")

if __name__ == "__main__":
    os.system('clear')

    # === SETTINGS ===
    use_url = True  # Set to False to use a local video file
    video_url = input("Enter video URL:")
    local_video_path = ""
    download_target = "/Users/julius/Downloads/video.mp4"

    output_dir = "/Users/julius/Downloads/frames"
    audio_path = os.path.join(output_dir, "temp_audio.wav")
    transcript_path = os.path.join(output_dir, "transcript.txt")

    clear_output_folder(output_dir)
    video_path = download_video(video_url, download_target) if use_url else local_video_path

    extract_even_frames_with_timestamps(video_path, output_dir)
    save_frames_to_pdf_and_cleanup(output_dir)

    try:
        extract_audio(video_path, audio_path)
        if os.path.exists(audio_path):
            transcribe_audio(audio_path, transcript_path)
            os.remove(audio_path)
        else:
            print("Audio file was not created. Skipping transcription.")
    except Exception:
        print("Audio extraction failed. Skipping transcription.")

    if use_url and os.path.exists(download_target):
        os.remove(download_target)

    print("Temporary audio and video file deleted.")
