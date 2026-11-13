# Project provenance

The project builds on four labs completed in a group for Representation of
Signals and Inverse Problems at Centrale Lille, 2025–2026, taught by
P.-A. Thouvenin. The completed notebooks were reorganized into shared Python
modules and a connected set of experiments, using the same image and audio files.

| Area | Original work retained | Corrections and additions |
| --- | --- | --- |
| Time-frequency | Bird, glockenspiel and sound-effect analysis; Gaussian/local spectra; original 400/424 Hz tone file; hyperbolic chirps | Consistent units and dB limits; STFT round-trip check; shared exports |
| Wavelets | Wavelet families, detail scales, coefficient layout, directional filtering, DWT/SWT threshold sweeps on the boat image | Reusable coefficient handling, fixed metric range, reconstruction checks, corrected detail-array assignment |
| Separation | Original bird/voice arrays, trimming, two mixtures and three sources, histogram directions, masking and sparse bonus | Fixed histogram range, consistent split real/imaginary minimum-L1 recovery, SI-SDR, permutation matching and input-channel baseline |
| Restoration | Gradient/adjoint, quadratic descent, Tikhonov denoising, projected-gradient inpainting on the boat image | Deterministic mask, independent linear-system checks, missing-pixel metrics, regularization comparison |
| Delivery | Four completed course notebooks and their original resources | Connected narrative notebooks, shared Python package, CLI, source-file hashes and measured result tables |

The notebooks are based on the completed submission variants. The course
question sheets, slides, exams and article PDFs are not copied into the project.
Included image/audio files are unchanged copies; their hashes are in
[`data/manifest.json`](../data/manifest.json). Source notebooks remain unchanged.

## Numerical conventions

The original separation files have WAV header rates of 44.1, 16 and 16 kHz.
The original lab trims the bird, takes 16,384 samples per source, and treats
all arrays at 15 kHz without resampling. This convention is retained, so these
are constructed linear mixtures of recorded arrays, not synchronized microphone
recordings. Preview pitch/speed follows that common analysis rate.

The real and imaginary STFT coordinates are reconstructed independently.
The objective is the sum of absolute real and imaginary components, not the
rotation-invariant sum of complex magnitudes. The original bonus chose a pair
using only the real-part angle and applied it to the whole complex vector;
the project corrects that inconsistency.

For the quadratic with eigenvalues 1 and 8, a step of 0.25 is a nonconvergent
boundary: the stiff coordinate oscillates without decaying. The notebooks
explicitly show this case. The original Tikhonov weight of 8 is also retained,
even though its boat-image PSNR is worse than that of the noisy observation.
