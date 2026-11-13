"""Load the original image and audio resources used in the four course labs."""

from pathlib import Path
import numpy as np
from PIL import Image
from scipy import signal
from scipy.io import loadmat, wavfile


def hyperbolic_chirps():
    """The analytical chirp experiment already present in the first lab."""
    fs, duration = 4096, 3
    t = np.arange(fs * duration) / fs
    x = signal.chirp(t, 200, duration, 1650, method="hyperbolic")
    x += signal.chirp(t, 250, duration, 1650, method="hyperbolic")
    return fs, x


def load_inputs(data_dir=None):
    directory = Path(data_dir) if data_dir else Path(__file__).resolve().parents[2] / "data"
    def image(name):
        with Image.open(directory / "images" / name) as source:
            return np.asarray(source.convert("L"), dtype=float) / 255
    recordings = [wavfile.read(directory / "audio/separation" / (name + ".wav"))
                  for name in ("bird", "female", "male")]
    bird = recordings[0][1]
    # Preserve the bird trimming and common playback rate of the original lab.
    removed = np.r_[np.arange(6001), np.arange(12500, 15001),
                    np.arange(22500, 24001), np.arange(32500, 34001)]
    bird = np.delete(bird, removed)
    n = 16384
    sources = np.stack([bird[:n], recordings[1][1][:n], recordings[2][1][:n]]).astype(float)
    sources /= sources.std(axis=1, keepdims=True)
    tf_directory = directory / "audio/time_frequency"
    audio_fs, audio = wavfile.read(tf_directory / "bird.wav")
    tone = loadmat(tf_directory / "signal_2sinus.mat")
    signatures = []
    for filename, label in [("bird.wav", "Bird"), ("glockenspiel_mono.wav", "Glockenspiel"),
                            ("desactive_mono.wav", "Sound effect")]:
        fs, samples = wavfile.read(tf_directory / filename)
        signatures.append(dict(label=label, fs=int(fs), samples=samples.astype(float)))
    return dict(image=image("boat.png"), chessboard=image("chessboard.png"),
                fs=15000, sources=sources, labels=["Bird", "Female voice", "Male voice"],
                audio=audio.astype(float), audio_fs=int(audio_fs),
                tones=tone["x"].ravel(), tone_fs=int(tone["Fe"].item()),
                tone_frequencies_hz=[400, 424], audio_signatures=signatures,
                source_header_sample_rates_hz=[int(fs) for fs, _ in recordings])
