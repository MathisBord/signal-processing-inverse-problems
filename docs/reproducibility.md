# Reproducibility and verification

Use Python 3.12 and the commands in the README. All inputs are included in
`data/`; `manifest.json` records hashes of the original resources. The committed
notebooks include computed outputs and can also be read without execution.

| Experiment | Fixed settings |
| --- | --- |
| Two-tone file | Original `signal_2sinus.mat`: 400 and 424 Hz, fs=4096 Hz; window widths 64–1024 |
| Chirps from Lab 1 | fs=4096 Hz, duration three seconds, 200/250 Hz starts and 1650 Hz endpoints |
| Wavelet noise | Boat image on [0,1]; `default_rng(1234)`, standard deviation 0.1 |
| Wavelet sweep | sym8, levels 1–5, thresholds 0.1/0.2/0.3/0.4; DWT periodization, SWT norm=False |
| Separation | Original trimmed bird and two voice arrays; unit standard deviation; 16,384 samples; common 15 kHz analysis rate; angles 30/90/150 degrees |
| Separation STFT | Hann, 128 samples, overlap 32, zero boundary extension and padded coverage |
| Direction estimation | 35 bins on [0,pi), 10%-of-max energy cutoff, one direction per angular third |
| Reconstruction | Median mixture-energy cutoff, evaluation-only permutation matching |
| Quadratic descent | Eigenvalues 1 and 8; initial (0.6,0.6); 30 iterations; steps 0.25/0.225/0.2/0.05 |
| Tikhonov | Boat image; noise seed 0, nominal expected input SNR 20 dB; lambda=8, 100 iterations, step 1.9/(1+8 lambda) |
| Inpainting | Boat image; mask seed 42, observation probability 0.1, 300 iterations, step 1.9/8 |

The boat image is 512 by 512 pixels. Image scores use floating-point reference
scaling [0,1] and PSNR data range one. Scores are computed before clipping.
Wavelet and Tikhonov noise prescriptions differ, so their PSNRs do not form
a controlled comparison between the methods.

The separation WAV headers are 44.1, 16 and 16 kHz. As in the original lab,
the arrays are interpreted at 15 kHz without resampling; this affects playback
speed and pitch. The time-frequency study uses each recording's actual header rate.

## Recompute

```bash
python -m pytest -q
python scripts/run_experiments.py
python scripts/execute_notebooks.py
python scripts/update_results_summary.py
```

Each notebook runs in a fresh IPython process; stdout and rich MIME displays
are captured from execution. The runner stops on cell errors. It uses a
temporary profile and standard Python kernel metadata. Verification is local;
no GitHub Actions workflow is included.

Tests cover adjoint identities, directional finite differences, independent
linear-system solutions, the step-size boundary, wavelet and STFT reconstruction,
real-L1 primal/dual certificates, mixture consistency, SI-SDR and permutation
matching. The test suite also checks bundled inputs and their recorded hashes.

There is one noise realization per experiment and no held-out benchmark.
Reference images select the best displayed wavelet setting; audio references
are used only for evaluation and matching, never during separation.
