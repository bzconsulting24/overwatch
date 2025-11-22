import torchaudio.transforms as T
import torch
import soundfile as sf

def analyze_speech_pattern(audio_path):
    print("Analyzing speech rhythm...")

    # Load audio using soundfile directly
    waveform, sr = sf.read(audio_path)
    waveform = torch.from_numpy(waveform).float()
    if len(waveform.shape) > 1:  # If stereo
        waveform = waveform.T  # Shape: [channels, samples]
    else:
        waveform = waveform.unsqueeze(0)  # Shape: [1, samples]
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

    # Speech rate via RMS energy envelope onsets (syllable/word detection)
    duration_sec = waveform.shape[0] / 16000

    # Detect speech onsets using RMS envelope
    window_size = 400  # ~25ms at 16kHz
    hop = 160  # ~10ms hop
    rms_envelope = []
    for i in range(0, len(waveform) - window_size, hop):
        window = waveform[i:i+window_size]
        rms_envelope.append(torch.sqrt(torch.mean(window ** 2)).item())

    rms_envelope = torch.tensor(rms_envelope)

    # Find peaks in RMS envelope (speech onsets)
    if len(rms_envelope) > 2:
        # Local maxima detection
        peaks = (rms_envelope[1:-1] > rms_envelope[:-2]) & (rms_envelope[1:-1] > rms_envelope[2:])
        # Filter by threshold (30% of max RMS)
        threshold = rms_envelope.max() * 0.3
        strong_peaks = peaks & (rms_envelope[1:-1] > threshold)
        num_onsets = strong_peaks.sum().item()
    else:
        num_onsets = 0

    # Convert to words/syllables per minute
    speech_rate = (num_onsets / duration_sec) * 60 if duration_sec > 0 else 0

    print(f"  Detected speech rate: {speech_rate:.1f} syllables/min (~{speech_rate/60:.1f} per sec)")
    print(f"  Volume variation (std): {volume_std:.4f}")

    # Normal speech: 120-200 syllables/min (2-3.3 per sec)
    if speech_rate > 250 or (speech_rate < 80 and speech_rate > 0):
        print("[Warning!] Unusual speaking rate (too fast or too slow).")

    if volume_std < 0.01:
        print("[Warning!] Voice sounds flat or monotone.")
    else:
        print("[check] Voice shows natural variation.")

    return speech_rate, volume_std
