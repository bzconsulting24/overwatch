import librosa
import numpy as np

    ## Deterct Emotional Features

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
    return tempo_val, volume_std