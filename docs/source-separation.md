# From the literature to a working separation pipeline

This implementation study asks how three sources can be recovered from two
instantaneous linear mixtures. It adapts the original course experiments and
checks the connection between mathematical assumptions and executable code.
It does not reproduce the benchmark experiments or claim the performance of
either cited paper.

## Observation model

For a source matrix $S\in\mathbb R^{3\times N}$, observations are $X=AS$, with
$A\in\mathbb R^{2\times3}$. Each column is $(\cos\phi_j,\sin\phi_j)^T$.
The experiment uses directions of 30, 90 and 150 degrees. They are abstract
mixing directions: the third has a negative first-channel coefficient, so
this is not a conventional nonnegative stereo-panning simulation.

Mixing is instantaneous, constant and noiseless. There is no reverberation,
time delay, frequency-dependent transfer function or changing source position.
Each source is normalized to unit standard deviation before mixing.

## What each reference contributes

| Reference | Specific idea | Implementation and departure |
| --- | --- | --- |
| [Bofill & Zibulevsky, 2001](https://doi.org/10.1016/S0165-1684(01)00120-7), Section 4 | Real minimum-L1 decomposition in the two-channel case | `minimum_l1_real` enumerates all nonsingular two-column bases and selects the smallest L1 cost; enumeration handles signed directions without an angular wrap-around special case |
| Bofill & Zibulevsky, Sections 5-6 | A transform can make audio mixtures sparser; real and imaginary Fourier coordinates are used separately | Matched Hann STFT/ISTFT, followed by independent real/imaginary reconstruction; synthesis uses SciPy overlap-add rather than the paper's frame-center concatenation |
| [Cano et al., 2019](https://doi.org/10.1109/MSP.2018.2874719), “Musical source position models” | Source-dominated TF bins encode spatial mixture information; assigning bins enables masking-based reconstruction | A three-sector angular histogram estimates directions, followed by the original projection/argmax binary baseline |
| [Le Roux et al., 2019](https://doi.org/10.1109/ICASSP.2019.8683855) | Scale-invariant distortion measurement | Zero-mean SI-SDR per source, after evaluation-only permutation matching; compare against the best input channel |

The histogram is a simplified estimator inherited from the original work.
It is **not** the potential-function clustering algorithm in Bofill &
Zibulevsky. The known source count is three, and one peak is taken in each
third of the angular interval. Three directions in the same sector would
violate this estimator's prior. Histogram range is fixed to $[0,\pi)$ so
results are not shifted by the extrema of each particular dataset.

## Sparse reconstruction and the complex-coordinate caveat

For real rank-two $A$ and $x\in\mathbb R^2$, solve

$$\min_s\|s\|_1\quad\text{subject to }As=x.$$

Writing $s=u-v$ with $u,v\geq0$ gives a linear program with two equality
constraints. An optimal basic feasible solution has at most two active
variables. Thus enumerating nonsingular two-column bases suffices to find
an optimum. Negative source coefficients are allowed. Pair inverses depend
only on the estimated matrix and are shared across all observation vectors.

For complex STFT coefficients this implementation solves the real problem
twice, separately on the real and imaginary coordinates, then recombines.
Equivalently it minimizes

$$\sum_j(|\operatorname{Re}s_j|+|\operatorname{Im}s_j|)$$

under the complex mixing equality. This is **not** the rotation-invariant
complex objective $\sum_j|s_j|$. Its value can depend on the coordinate phase.
The distinction is explicit in the API name `split_l1`, plots and notebooks.

The original bonus selected a pair from the real-part angle and applied it
to the whole complex vector. The public implementation corrects that
inconsistency. The numerical tests establish primal feasibility and a dual
certificate with the same objective, demonstrating global optimality for
the real subproblems. This verifies the solver, not recovery of the true
sources when its sparsity assumptions fail.

## Fixed configuration and evaluation

| Setting | Value or rule |
| --- | --- |
| Inputs | Original bird, female-voice and male-voice recordings |
| Source length and sample rate | 16,384 samples at 15 kHz |
| STFT | 128-sample Hann window, 32-sample overlap, zero boundary extension, padded coverage |
| Direction estimation | Retain complex bins above 10% of maximum energy; angular histogram of their nonzero real/imaginary vectors |
| Reconstruction pruning | Discard bins below the median complex mixture energy, for both methods |
| Reference use | Evaluation and permutation resolution only |
| Baseline | Best SI-SDR among the two input channels, separately for each reference source |
| Listening files | Independently peak-normalized float32 WAVs; evaluation uses original arrays |

The low-energy discarding is a heuristic inherited from the original code.
After discarding, exact mixture consistency is no longer enforced in those
bins. SI-SDR is invariant to a global gain and is not a loudness or perceptual
quality measure. No time-shift search, learned model or test-set tuning is used.

## Limits and useful follow-up experiments

Overlapping harmonics, nearly collinear directions, weak sources, sensor noise
and reverberation are natural failure modes. These excerpts and constructed instantaneous mixtures are limited examples
of recorded audio. A useful extension would test
performance against increasing spectral overlap or reduced direction
separation, while replacing the sector prior with a general peak estimator.
These extensions are suggestions; they have not been implemented or benchmarked.

See [measured results](results.md) and the [complete bibliography](../REFERENCES.md).
