import os
import cv2
import shutil
import numpy as np
from PIL import Image
import openface.feature_extraction
import whisper
import subprocess
import requests
import librosa
import tensorflow as tf
import tensorflow_hub as hub
import pandas as pd
import opensmile

os.system('cls')
os.environ["OPENCV_FFMPEG_READ_ATTEMPTS"] = "20000"  # Increase attempts to read video frames

def clear_output_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path, exist_ok=True)

## ---Download Video---
def download_video(url, save_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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
    
## ---Extract Frames with timestamps ---
def extract_even_frames_with_timestamps(video_path, output_folder, num_frames=200, resize_width=640, resize_height=360):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Failed to open video: {video_path}")
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
    
    
## ---save frames to PDF---
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
    
## ---Conpress PDF---
def compress_pdf(input_pdf, output_pdf, quality=75):
    from PyPDF2 import PdfReader, PdfWriter
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)
    
    print(f"Compressed PDF saved to: {output_pdf}")
    
## ---EXTRACT AUDIO---
def extract_audio(video_path, audio_path):
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("[Warning!] Audio extraction failed:")
        print(result.stderr.decode())
    elif not os.path.exists(audio_path):
        print("[Warning!] Audio file not found after ffmpeg run.")
    else:
        print(f"[check] Audio saved to: {audio_path}")

## ---TRANSCRIBE AUDIO---
def transcribe_audio(audio_path, transcript_path):
    model = whisper.load_model("base")  ##  ## Models ['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large', 'large-v3-turbo', 'turbo']
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
    
    ## ---Detect Keyboard Sounds---
def detect_keyboard_sounds(audio_path):
    print("Analyzing audio for keyboard sounds...")
    model = hub.load("https://tfhub.dev/google/yamnet/1")
    waveform, sr = librosa.load(audio_path, sr=16000)
    scores, embeddings, spectrogram = model(waveform)

    class_map_path = tf.keras.utils.get_file(
        'yamnet_class_map.csv',
        'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
    )

    class_names = pd.read_csv(class_map_path)['display_name'].to_list()
    mean_scores = tf.reduce_mean(scores, axis=0).numpy()
    top_indexes = mean_scores.argsort()[-10:][::-1]
    top_classes = [class_names[i] for i in top_indexes]

    summary = ["Top detected sounds:"]
    for name in top_classes:
        summary.append(f"  - {name}")

    if "Typing" in top_classes and "Clicking" in top_classes:
        summary.append("[Warning!]  Keyboard typing sounds detected.")
    elif "Clock" in top_classes or "Tick" in top_classes:
        summary.append("[Warning!]  Possible keyboard sounds detected.")
    else:
        summary.append("[check]  No strong evidence of keyboard typing detected.")

    print("\n".join(summary))
    return summary


   ## ---Analyze Speech Rhythm---     
def analyze_speech_pattern(audio_path):
    print("Analyzing speech rhythm...")
    y, sr = librosa.load(audio_path, sr=16000)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    rms = librosa.feature.rms(y=y).flatten()
    volume_std = np.std(rms)

    if isinstance(tempo, (list, np.ndarray)):
        tempo_val = float(tempo[0])
    else:
        tempo_val = float(tempo)
        
    print(f"  Detected speaking tempo (approx): {tempo_val:.2f} BPM")
    print(f"  Volume variation (std): {volume_std:.4f}")

    if tempo > 190 or tempo < 70:
        print("[Warning!] Unusual speaking rate (too fast or too slow).")

    if volume_std < 0.01:
        print("[Warning!] Voice sounds flat or monotone.")
    else:
        print("[check] Voice shows natural variation.")
        
    
    features = smile.process_file(audio_path)
    print(features.head())
    
    ## --- Behavioral Analysis ---
def interpret_behavior(features):
    def safe_get(col_name):
        return features[col_name].values[0] if col_name in features.columns else None

    pitch = safe_get("F0final_sma_amean")
    energy = safe_get("pcm_RMSenergy_sma_amean")
    jitter = safe_get("jitterLocal_sma_amean")

    results = []
    results.append(f"Pitch (F0final_sma_amean): {pitch:.2f}" if pitch is not None else "Pitch: N/A")
    results.append(f"Energy (RMSenergy): {energy:.2f}" if energy is not None else "Energy: N/A")
    results.append(f"Jitter (local): {jitter:.4f}" if jitter is not None else "Jitter: N/A")

    if pitch is not None and pitch < 120:
        results.append("[warning] Possibly monotone or calm.")
    if energy is not None and energy < -30:
        results.append("[warning] Low vocal energy detected.")
    if jitter is not None and jitter > 0.01:
        results.append("[warning] Unstable voice — could indicate nervousness.")
    elif jitter is not None:
        results.append("[check] Vocal delivery seems stable.")

    print("\n".join(results))
    return results 

    ## ---Flag Sensitive Words---
def flag_sensitive_words(transcript_path, words_to_flag=["combinatorial", "paradigm", "in computer science"]):
    print("Checking transcript for flagged words...")
    flagged_lines = []
    word_hits = {word: 0 for word in words_to_flag}

    with open(transcript_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            lower_line = line.lower()
            matched_words = [word for word in words_to_flag if word in lower_line]
            if matched_words:
                flagged_lines.append((i, line.strip(), matched_words))
                for word in matched_words:
                    word_hits[word] += 1

    output_lines = []
    if flagged_lines:
        output_lines.append("[Warning!] Flagged words found in transcript:")
        for line_num, content, words in flagged_lines:
            output_lines.append(f"  Line {line_num}: {content}")
            output_lines.append(f"    → Matched: {', '.join(words)}")

        output_lines.append("\nSummary of flagged words:")
        for word, count in word_hits.items():
            output_lines.append(f"  {word}: {count} occurrence(s)")
    else:
        output_lines.append("[check] No flagged words found.")

    print("\n".join(output_lines))
    return output_lines


if __name__ == "__main__":
    # === SETTINGS ===
    use_url = True  # Set to False to use a local video file
    video_url = input("Enter video URL:")
    local_video_path = r"C:\Users\julius\Alignerr_vids\video.avi"
    download_target = r"C:\Users\julius\Alignerr_vids\video.avi"
    
    output_dir = r"C:\Users\julius\Alignerr_vids"
    audio_path = os.path.join(output_dir, "temp_audio.wav")
    transcript_path = os.path.join(output_dir, "transcript.txt")

    clear_output_folder(output_dir)
    video_path = download_video(video_url, download_target) if use_url else local_video_path

    extract_even_frames_with_timestamps(video_path, output_dir)
    save_frames_to_pdf_and_cleanup(output_dir)
    extract_audio(video_path, audio_path)
    
        ## Deterct Emotional Features
    smile = opensmile.Smile(
        feature_set=opensmile.FeatureSet.ComParE_2016,
        feature_level=opensmile.FeatureLevel.Functionals
    )
    features = smile.process_file(audio_path)
    behavior_summary = interpret_behavior(features)
    # print(features.filter(regex="F0|jitter|energy", axis=1).head())  ## For debugging


    if os.path.exists(audio_path):
        transcribe_audio(audio_path, transcript_path)
        analyze_speech_pattern(audio_path)
        flagged_summary = flag_sensitive_words(transcript_path)
        sound_summary = detect_keyboard_sounds(audio_path)
        behavior_summary = interpret_behavior(features)

    ## Append summaries to the transcript file
        with open(transcript_path, "a", encoding="utf-8") as f:
            f.write("\n\n---\n\n")
            f.write(" ### Cheating indicator Analysis\n\n")
            for line in flagged_summary:
                f.write(line + "\n")
            f.write("\n")
            for line in sound_summary:
                f.write(line + "\n")
            f.write("\n")
            f.write("### Behavioral Analysis\n\n")
            for line in behavior_summary:
                f.write(line + "\n")

        os.remove(audio_path)
        os.remove(local_video_path)
        print("Temp audio file deleted.")
        print("Temp Video file deleted.")
    else:
        print("[X] Skipping analysis: audio file not found.")

