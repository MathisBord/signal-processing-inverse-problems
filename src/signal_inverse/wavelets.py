"""Multiscale reconstruction and detail-only hard thresholding."""

import numpy as np
import pywt


def hard_threshold(values, threshold):
    if threshold < 0:
        raise ValueError("threshold must be nonnegative.")
    return np.asarray(values) * (np.abs(values) > threshold)


def denoise(image, threshold, level=3, wavelet="sym8", transform="dwt"):
    """Preserve the coarse approximation, threshold every detail subband.

    DWT uses periodic boundary extension. SWT is unnormalized, matching the
    convention in the supplied implementation; threshold scales are unchanged.
    No post-reconstruction clipping is applied to the scored output.
    """
    image = np.asarray(image, dtype=float)
    if image.ndim != 2 or level < 1:
        raise ValueError("A 2D image and a positive decomposition level are required.")
    if transform == "dwt":
        max_level = pywt.dwtn_max_level(image.shape, wavelet)
        if level > max_level:
            raise ValueError(f"level {level} exceeds the boundary-safe maximum {max_level}.")
        coeffs = pywt.wavedec2(image, wavelet, mode="periodization", level=level)
        filtered = [coeffs[0]] + [tuple(hard_threshold(d, threshold) for d in detail) for detail in coeffs[1:]]
        result = pywt.waverec2(filtered, wavelet, mode="periodization")
    elif transform == "swt":
        if any(n % 2**level for n in image.shape):
            raise ValueError("SWT image dimensions must be divisible by 2**level.")
        coeffs = pywt.swt2(image, wavelet, level=level, trim_approx=True, norm=False)
        filtered = [coeffs[0]] + [tuple(hard_threshold(d, threshold) for d in detail) for detail in coeffs[1:]]
        result = pywt.iswt2(filtered, wavelet, norm=False)
    else:
        raise ValueError("transform must be 'dwt' or 'swt'.")
    return result[:image.shape[0], :image.shape[1]]


def reconstruct_component(x, wavelet="sym8", level=7, detail_level=None):
    """Reconstruct the coarse approximation, or one numbered detail scale."""
    coeffs = pywt.wavedec(np.asarray(x, float), wavelet, level=level)
    selected = [np.zeros_like(c) for c in coeffs]
    index = 0 if detail_level is None else level - detail_level + 1
    if not 0 <= index < len(coeffs):
        raise ValueError("detail_level must lie in [1, level].")
    selected[index] = coeffs[index].copy()
    return pywt.waverec(selected, wavelet)[:len(x)]


def remove_orientation(image, orientation="all", wavelet="haar", level=2):
    coeffs = pywt.wavedec2(image, wavelet, mode="periodization", level=level)
    names = ("horizontal", "vertical", "diagonal")
    if orientation not in (*names, "all"):
        raise ValueError("Unknown wavelet detail orientation.")
    filtered = [coeffs[0]] + [tuple(np.zeros_like(c) if orientation in (names[i], "all") else c
                                  for i, c in enumerate(detail)) for detail in coeffs[1:]]
    return pywt.waverec2(filtered, wavelet, mode="periodization")[:image.shape[0], :image.shape[1]]
