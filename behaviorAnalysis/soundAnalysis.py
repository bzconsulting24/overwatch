import pandas as pd
import tensorflow as tf
import tensorflow_hub as hub
import librosa

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
