"""Two-channel instantaneous source separation using sparse representations.

See REFERENCES.md and docs/source-separation.md for the precise relationship
to Bofill & Zibulevsky (2001) and Cano et al. (2019).
"""

from itertools import combinations, permutations
import numpy as np
from .time_frequency import stft, inverse_stft
from .metrics import si_sdr


def mixing_matrix(angles):
    angles = np.asarray(angles)
    return np.vstack([np.cos(angles), np.sin(angles)])


def estimate_directions(coefficients, energy_ratio=0.1, bins=35):
    """Histogram peaks in three sectors, preserving the coursework estimator.

    This explicitly assumes one source direction per third of [0, pi).
    It is not a general estimator of the number or positions of sources.
    """
    vectors = coefficients.reshape(2, -1).T
    energy = np.sum(np.abs(vectors)**2, axis=1)
    strong = vectors[energy > energy_ratio * energy.max()]
    points = np.concatenate([strong.real, strong.imag], axis=0)
    points = points[np.linalg.norm(points, axis=1) > 1e-12]
    if not points.size:
        raise ValueError("No energetic coefficients are available for estimation.")
    angles = np.arctan2(points[:, 1], points[:, 0]) % np.pi
    counts, edges = np.histogram(angles, bins=bins, range=(0, np.pi))
    centers = (edges[1:] + edges[:-1]) / 2
    peaks = [sector[np.argmax(counts[sector])] for sector in np.array_split(np.arange(bins), 3)]
    return centers[peaks], counts, edges


def binary_mask(coefficients, matrix, discard_percentile=50):
    vectors = coefficients.reshape(2, -1).T
    projections = vectors @ matrix
    labels = np.argmax(np.abs(projections), axis=1)
    energy = np.sum(np.abs(vectors)**2, axis=1)
    keep = energy >= np.percentile(energy, discard_percentile)
    labels[~keep] = -1
    sources = np.zeros((len(vectors), matrix.shape[1]), dtype=complex)
    for j in range(matrix.shape[1]):
        sources[:, j] = projections[:, j] * (labels == j)
    return sources.T.reshape(matrix.shape[1], *coefficients.shape[1:]), labels.reshape(coefficients.shape[1:])


def minimum_l1_real(vectors, matrix):
    """Solve min ||s||_1 subject to A s = x for real rank-two mixtures.

    Enumerate nonsingular two-column bases. A real linear program admits an
    optimal basic solution with at most two nonzero coefficients. Enumerating
    bases avoids sign and angular wrap-around errors in the enclosing rule.
    """
    vectors, matrix = np.asarray(vectors, float), np.asarray(matrix, float)
    best = np.full(vectors.shape[0], np.inf)
    solution = np.zeros((vectors.shape[0], matrix.shape[1]))
    for pair in combinations(range(matrix.shape[1]), 2):
        basis = matrix[:, pair]
        if abs(np.linalg.det(basis)) < 1e-10:
            continue
        values = np.linalg.solve(basis, vectors.T).T
        objective = np.sum(np.abs(values), axis=1)
        improve = objective < best
        solution[improve] = 0
        for k, j in enumerate(pair):
            solution[improve, j] = values[improve, k]
        best[improve] = objective[improve]
    if not np.all(np.isfinite(best)):
        raise ValueError("The mixing matrix must have rank two.")
    return solution


def split_l1(coefficients, matrix, discard_percentile=50):
    """Separate real and imaginary coordinates, then recombine.

    The objective is sum_j(|Re s_j|+|Im s_j|), not sum_j|s_j| with complex
    magnitudes. Low-energy discarding is an additional, explicit heuristic.
    """
    vectors = coefficients.reshape(2, -1).T
    result = minimum_l1_real(vectors.real, matrix) + 1j * minimum_l1_real(vectors.imag, matrix)
    energy = np.sum(np.abs(vectors)**2, axis=1)
    result[energy < np.percentile(energy, discard_percentile)] = 0
    return result.T.reshape(matrix.shape[1], *coefficients.shape[1:])


def separate(mixtures, fs, width=128, overlap=32, energy_ratio=0.1, discard_percentile=50):
    if np.asarray(mixtures).shape[0] != 2:
        raise ValueError("Exactly two observed channels are required.")
    _, _, coefficients = stft(mixtures, fs, width, overlap)
    angles, counts, edges = estimate_directions(coefficients, energy_ratio)
    matrix = mixing_matrix(angles)
    masked, labels = binary_mask(coefficients, matrix, discard_percentile)
    sparse = split_l1(coefficients, matrix, discard_percentile)
    length = mixtures.shape[1]
    return dict(angles=angles, matrix=matrix, counts=counts, edges=edges, labels=labels,
                coefficients=coefficients,
                binary=inverse_stft(masked, fs, length, width, overlap),
                split_l1=inverse_stft(sparse, fs, length, width, overlap))


def match_sources(reference, estimates):
    """Resolve permutation by maximizing absolute zero-mean correlation.

    Matching uses ground truth only for evaluation, never during separation.
    """
    reference, estimates = np.asarray(reference), np.asarray(estimates)
    a = reference - reference.mean(axis=1, keepdims=True)
    b = estimates - estimates.mean(axis=1, keepdims=True)
    correlations = a @ b.T / np.maximum(np.linalg.norm(a, axis=1)[:, None] * np.linalg.norm(b, axis=1), 1e-15)
    if len(reference) != len(estimates) or len(reference) > 7:
        raise ValueError("Exhaustive permutation matching supports equal source counts up to seven.")
    rows = range(len(reference))
    columns = max(permutations(rows), key=lambda p: sum(abs(correlations[i,j]) for i,j in enumerate(p)))
    aligned = np.empty_like(reference)
    for i, j in zip(rows, columns):
        aligned[i] = estimates[j]
    return aligned, [si_sdr(reference[i], aligned[i]) for i in range(len(reference))]
