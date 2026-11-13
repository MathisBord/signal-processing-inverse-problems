"""Shared plotting conventions for exported figures and notebook displays."""

import numpy as np
import matplotlib.pyplot as plt

COLORS = ["#2166ac", "#d95f02", "#188977", "#8e5ba6", "#c94c4c"]


def set_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.labelcolor": "#25324a", "text.color": "#25324a",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.prop_cycle": plt.cycler(color=COLORS),
        "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white", "figure.dpi": 110,
        "savefig.dpi": 150,
    })


def save(fig, directory, name):
    directory.mkdir(parents=True, exist_ok=True)
    fig.savefig(directory / (name + ".png"), bbox_inches="tight", dpi=150)
    plt.close(fig)


def image_panel(images, titles, figsize=None):
    fig, axes = plt.subplots(1, len(images), figsize=figsize or (4 * len(images), 4), layout="constrained")
    for ax, image, title in zip(np.atleast_1d(axes), images, titles):
        ax.imshow(image, cmap="gray", vmin=0, vmax=1)
        ax.set_title(title)
        ax.set_axis_off()
    return fig
