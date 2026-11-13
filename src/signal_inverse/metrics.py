"""Reference-based metrics; all inputs must use the same amplitude scale."""

import numpy as np


def mse(reference, estimate):
    reference, estimate = np.asarray(reference), np.asarray(estimate)
    if reference.shape != estimate.shape:
        raise ValueError("Reference and estimate must have identical shapes.")
    return float(np.mean(np.abs(reference - estimate) ** 2))


def psnr(reference, estimate, data_range=1.0):
    """Peak SNR in dB with an explicitly specified signal range."""
    if data_range <= 0:
        raise ValueError("data_range must be positive.")
    error = mse(reference, estimate)
    return float('inf') if error == 0 else float(10 * np.log10(data_range**2 / error))


def snr(reference, estimate):
    reference = np.asarray(reference, dtype=float)
    mse(reference, estimate)  # shape check
    error = np.sum((reference - estimate) ** 2)
    return float(10 * np.log10(np.sum(reference**2) / max(error, np.finfo(float).tiny)))


def si_sdr(reference, estimate):
    """Zero-mean scale-invariant SDR (Le Roux et al., 2019), in dB.

    No lag alignment, frequency weighting or perceptual correction is applied.
    """
    reference, estimate = np.asarray(reference, float), np.asarray(estimate, float)
    mse(reference, estimate)
    target = reference - reference.mean()
    prediction = estimate - estimate.mean()
    norm = np.dot(target, target)
    if norm <= np.finfo(float).eps:
        raise ValueError("SI-SDR is undefined for a constant reference.")
    projection = np.dot(prediction, target) / norm * target
    numerator = np.dot(projection, projection)
    denominator = np.sum((prediction - projection)**2)
    tiny = np.finfo(float).tiny
    return float(10 * np.log10(max(numerator, tiny) / max(denominator, tiny)))
