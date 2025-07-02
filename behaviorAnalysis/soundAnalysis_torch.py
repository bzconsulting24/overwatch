import torch
import torchaudio

def detect_keyboard_sounds(audio_path):
    print("Analyzing audio for keyboard sounds...")

    # 1) Load + resample + mono
    waveform, sr = torchaudio.load(audio_path)
    if sr != 16000:
        waveform = torchaudio.transforms.Resample(sr, 16000)(waveform)
    y = waveform.mean(dim=0)  # shape: [T]

    # 2) Compute complex STFT, then magnitude spectrogram [freq_bins, frames]
    spec = torch.stft(
        y,
        n_fft=1024,
        hop_length=512,
        win_length=1024,
        return_complex=True
    )
    spec_mag = spec.abs()

    # 3) Spectral flux: difference along time frames, keep only positive changes
    #    diff shape: [freq_bins, frames-1]
    diff = spec_mag[:, 1:] - spec_mag[:, :-1]
    positive_diff = diff.clamp(min=0)

    # 4) Sum over frequency axis → flux per time frame (length = frames-1)
    flux = positive_diff.sum(dim=0)

    # 5) Onset count: local peaks in the 1-D flux signal
    if flux.numel() < 3:
        num_onsets = 0
    else:
        peaks = (flux[1:-1] > flux[:-2]) & (flux[1:-1] > flux[2:])
        num_onsets = int(peaks.sum().item())

    # 6) Normalize by duration
    duration_sec = y.shape[0] / 16000
    onsets_per_sec = num_onsets / duration_sec if duration_sec > 0 else 0.0

    # 7) Build the summary
    summary = [f"Detected {num_onsets} onsets ({onsets_per_sec:.2f} per sec)"]
    if onsets_per_sec > 5:
        summary.append("[Warning!] Possible keyboard typing detected.")
    else:
        summary.append("[check] No strong evidence of typing detected.")

    print("\n".join(summary))
    return summary
