import os
import librosa
import soundfile as sf
from scipy.signal import iirnotch, filtfilt
import pyroomacoustics as pra
from pydub import AudioSegment, effects
from audioextract import extract_audio  # your existing extraction function

def remove_hum(audio, sr, freq=60, Q=30.0):
    b, a = iirnotch(freq, Q, sr)
    return filtfilt(b, a, audio)

def reduce_reverb(audio, alpha=0.9, iterations=1, frame_len=2048):
    return pra.denoise.apply_iterative_wiener(
        audio, frame_len=frame_len, alpha=alpha, iterations=iterations
    )

def normalize_audio(input_audio, output_audio, volume_boost_dB=6):
    audio = AudioSegment.from_file(input_audio)
    audio = effects.normalize(audio)
    audio += volume_boost_dB
    audio.export(output_audio, format="wav")

def process_audio(video_path, final_output):
    # clearly create temp files
    extracted_audio_path = "extracted_temp_audio.wav"
    intermediate_output = "intermediate_clean.wav"

    extract_audio(video_path, extracted_audio_path)

    audio, sr = librosa.load(extracted_audio_path, sr=None)
    audio_no_hum = remove_hum(audio, sr)
    audio_clean = reduce_reverb(audio_no_hum, alpha=0.9, iterations=1)

    sf.write(intermediate_output, audio_clean, sr)
    normalize_audio(intermediate_output, final_output, volume_boost_dB=6)

    # clean up temp files
    os.remove(extracted_audio_path)
    os.remove(intermediate_output)

    return final_output
