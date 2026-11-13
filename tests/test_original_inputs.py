"""Verify the included course resources and their numerical conventions."""
import hashlib
import json
from pathlib import Path

import numpy as np

from signal_inverse.datasets import load_inputs


def test_bundled_resources_match_recorded_source_hashes():
    data = Path(__file__).resolve().parents[1] / "data"
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 9
    for entry in manifest:
        assert hashlib.sha256((data / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]


def test_original_inputs_and_two_tone_frequencies():
    inputs = load_inputs()
    assert inputs["image"].shape == (512, 512)
    assert inputs["sources"].shape == (3, 16384)
    assert inputs["source_header_sample_rates_hz"] == [44100, 16000, 16000]
    assert inputs["fs"] == 15000
    spectrum = np.abs(np.fft.rfft(inputs["tones"]))
    frequencies = np.fft.rfftfreq(len(inputs["tones"]), 1 / inputs["tone_fs"])
    assert np.array_equal(np.sort(frequencies[np.argsort(spectrum)[-2:]]), [400, 424])
