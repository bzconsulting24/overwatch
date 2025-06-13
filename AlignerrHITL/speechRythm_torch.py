import torchaudio
import torchaudio.transforms as T
import torch

def analyze_speech_pattern(audio_path):
    print("Analyzing speech rhythm...")

    # Load audio
    waveform, sr = torchaudio.load(audio_path)
    if sr != 16000:
        resampler = T.Resample(orig_freq=sr, new_freq=16000)
        waveform = resampler(waveform)
    waveform = waveform.mean(dim=0)  # Convert to mono

    # Volume analysis (RMS and variation)
    rms = torch.sqrt(torch.mean(waveform ** 2))
    frame_length = 1024
    hop_length = 512
    frame_rms = torch.nn.functional.unfold(
        waveform.unsqueeze(0).unsqueeze(0), kernel_size=(1, frame_length), stride=(1, hop_length)
    ).squeeze().pow(2).mean(dim=0).sqrt()
    volume_std = frame_rms.std().item()

    # Tempo (approximate via zero-crossing rate peaks)
    zero_crossings = torch.abs(torch.diff(torch.sign(waveform))).sum().item()
    duration_sec = waveform.shape[0] / 16000
    tempo_estimate = (zero_crossings / duration_sec) / 2  # crude BPM estimate

    print(f"  Detected speaking tempo (approx): {tempo_estimate:.2f} BPM")
    print(f"  Volume variation (std): {volume_std:.4f}")

    if tempo_estimate > 190 or tempo_estimate < 70:
        print("[Warning!] Unusual speaking rate (too fast or too slow).")

    if volume_std < 0.01:
        print("[Warning!] Voice sounds flat or monotone.")
    else:
        print("[check] Voice shows natural variation.")

    return tempo_estimate, volume_std
