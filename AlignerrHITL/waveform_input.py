import torchaudio
import torch

class WaveformInput:
    def __init__(self, sample_rate=16000, patch_window=0.96, patch_hop=0.48):
        self.sample_rate = sample_rate
        self.patch_window = patch_window
        self.patch_hop = patch_hop
        self.n_mels = 64
        self.n_fft = 1024
        self.hop_length = int(self.sample_rate * 0.01)
        self.win_length = int(self.sample_rate * 0.025)

        self.mel_spectrogram = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length,
            n_mels=self.n_mels,
            center=True,
            power=2.0,
        )

        self.amplitude_to_db = torchaudio.transforms.AmplitudeToDB()

    def __call__(self, waveform: torch.Tensor) -> torch.Tensor:
        # waveform shape: [1, T]
        mel_spec = self.mel_spectrogram(waveform)
        log_mel_spec = self.amplitude_to_db(mel_spec)

        frame_size = 96
        step = int(self.patch_hop * self.sample_rate / self.hop_length)
        num_frames = log_mel_spec.shape[-1]

        if num_frames < frame_size:
            raise ValueError("Audio too short for patching")

        patches = []
        for start in range(0, num_frames - frame_size + 1, step):
            patch = log_mel_spec[:, :, start:start + frame_size]
            patches.append(patch)

        return torch.stack(patches)
