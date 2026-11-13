"""Quadratic smoothness priors and gradient methods with forward differences."""

from dataclasses import dataclass
import numpy as np


def gradient(image):
    """Forward differences with zero last-row/last-column differences."""
    image = np.asarray(image, float)
    result = np.zeros((*image.shape, 2))
    result[:-1, :, 0] = image[1:] - image[:-1]
    result[:, :-1, 1] = image[:, 1:] - image[:, :-1]
    return result


def gradient_adjoint(field):
    """Exact Euclidean adjoint, including degenerate one-row/column images."""
    field = np.asarray(field, float)
    result = np.zeros(field.shape[:2])
    result[:-1] -= field[:-1, :, 0]
    result[1:] += field[:-1, :, 0]
    result[:, :-1] -= field[:, :-1, 1]
    result[:, 1:] += field[:, :-1, 1]
    return result


def smoothness(image):
    return float(0.5 * np.sum(gradient(image)**2))


def denoising_cost(image, observation, regularization):
    return float(0.5 * np.sum((image - observation)**2) + regularization * smoothness(image))


@dataclass
class Result:
    image: np.ndarray
    costs: np.ndarray
    step: float


def denoise(observation, regularization=8.0, iterations=100, step=None):
    if regularization < 0 or iterations < 0:
        raise ValueError("regularization and iterations must be nonnegative.")
    # ||D||^2 <= 8 for this 2D finite-difference stencil.
    bound = 1 + 8 * regularization
    step = 1.9 / bound if step is None else step
    if not 0 < step < 2 / bound:
        raise ValueError("step must lie strictly below 2/(1+8*regularization).")
    x = np.asarray(observation, float).copy()
    costs = [denoising_cost(x, observation, regularization)]
    for _ in range(iterations):
        x -= step * (x - observation + regularization * gradient_adjoint(gradient(x)))
        costs.append(denoising_cost(x, observation, regularization))
    return Result(x, np.array(costs), step)


def project_observed(image, observation, mask):
    mask = np.asarray(mask, bool)
    if image.shape != observation.shape or mask.shape != image.shape:
        raise ValueError("Image, observation and mask shapes must agree.")
    return np.where(mask, observation, image)


def inpaint(observation, mask, iterations=300, step=1.9 / 8):
    if iterations < 0 or not 0 < step < 2 / 8:
        raise ValueError("Use nonnegative iterations and 0 < step < 2/8.")
    x = project_observed(np.zeros_like(observation, dtype=float), observation, mask)
    costs = [smoothness(x)]
    for _ in range(iterations):
        x = project_observed(x - step * gradient_adjoint(gradient(x)), observation, mask)
        costs.append(smoothness(x))
    return Result(x, np.array(costs), step)


def quadratic_descent(step, iterations=30, initial=(0.6, 0.6), eta=8):
    """Intentionally allow unstable steps to expose the convergence boundary."""
    history = np.empty((iterations + 1, 2))
    history[0] = initial
    for k in range(iterations):
        history[k + 1] = history[k] - step * np.array([history[k, 0], eta * history[k, 1]])
    values = 0.5 * (history[:, 0]**2 + eta * history[:, 1]**2)
    return history, values
