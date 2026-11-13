"""Fourier and windowed Fourier analysis with explicit conventions."""

import numpy as np
from scipy import signal


def centered_spectrum(x, fs):
    x = np.asarray(x, dtype=float)
    return np.fft.fftshift(np.fft.fftfreq(x.size, 1 / fs)), np.fft.fftshift(np.fft.fft(x)) / x.size


def local_spectrum(x, fs, center, half_width=400, sigma=200):
    """Gaussian window, sigma in samples; center is a zero-based sample index."""
    if center - half_width < 0 or center + half_width >= len(x):
        raise ValueError("The complete analysis window must lie inside the signal.")
    window = signal.windows.gaussian(2 * half_width + 1, std=sigma, sym=True)
    segment = np.asarray(x)[center - half_width:center + half_width + 1] * window
    frequency, spectrum = centered_spectrum(segment, fs)
    return frequency, spectrum, window


def spectrogram_db(x, fs, width=512, window="hann", overlap=None):
    """One-sided power spectral density in dB; no boundary padding or detrending.

    dB values use a reference of 1 amplitude-unit squared per Hz. Comparisons
    use the same color limits rather than independently normalized images.
    """
    overlap = 7 * width // 8 if overlap is None else overlap
    f, t, density = signal.spectrogram(np.asarray(x, float), fs=fs, window=window,
                                     nperseg=width, noverlap=overlap, detrend=False,
                                     scaling="density", mode="psd")
    return f, t, 10 * np.log10(np.maximum(density, 1e-14))


def stft(x, fs, width=128, overlap=32):
    return signal.stft(np.asarray(x, float), fs=fs, window="hann", nperseg=width,
                       noverlap=overlap, boundary="zeros", padded=True)


def inverse_stft(coefficients, fs, length, width=128, overlap=32):
    _, result = signal.istft(coefficients, fs=fs, window="hann", nperseg=width,
                            noverlap=overlap, boundary=True)
    return result[..., :length]
