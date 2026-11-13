"""Deterministic experiments shared by the CLI and four narrative notebooks.

These functions return measured summaries and export their supporting figures.
No stored coursework output is substituted for a computation.
"""

from pathlib import Path
import csv
import json
import platform
import importlib.metadata
import numpy as np
import pywt
import matplotlib.pyplot as plt
from scipy.io import wavfile
from . import datasets, time_frequency as tf, wavelets, optimization as opt, separation
from .metrics import psnr, mse, si_sdr
from .plotting import set_style, save, image_panel


def write_csv(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _spectrogram(ax, x, fs, width, window="hann", limits=(-90, -20), ylim=None):
    f, t, db = tf.spectrogram_db(x, fs, width, window)
    mesh = ax.pcolormesh(t, f, db, shading="auto", cmap="magma", vmin=limits[0], vmax=limits[1])
    ax.set(xlabel="Time (s)", ylabel="Frequency (Hz)")
    if ylim:
        ax.set_ylim(*ylim)
    return mesh


def run_time_frequency(inputs, output):
    output = Path(output)
    set_style()
    fs = inputs["audio_fs"]
    x = inputs["audio"][:2**15].astype(float)
    x = x / max(np.max(np.abs(x)), 1e-15)
    f, spectrum = tf.centered_spectrum(x, fs)
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), layout="constrained")
    axes[0].plot(np.arange(len(x)) / fs, x, linewidth=0.7)
    axes[0].set(xlabel="Time (s)", ylabel="Amplitude", title="The waveform hides how frequency content changes")
    axes[1].plot(f, np.abs(spectrum), linewidth=0.8)
    axes[1].set(xlabel="Frequency (Hz)", ylabel="Normalized DFT magnitude", title="A global spectrum summarizes the whole interval")
    save(fig, output, "global_spectrum")

    centers = np.linspace(500, len(x) - 501, 6, dtype=int)
    fig, axes = plt.subplots(2, 3, figsize=(12, 6), layout="constrained")
    for ax, center in zip(axes.flat, centers):
        frequency, transform, _ = tf.local_spectrum(x, fs, int(center))
        positive = frequency >= 0
        ax.plot(frequency[positive], np.abs(transform[positive]))
        ax.set(title=f"Center: {center / fs:.3f} s", xlabel="Frequency (Hz)", ylabel="Local magnitude")
    save(fig, output, "local_spectra")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for sigma in (50, 100, 200):
        frequency, transform, window = tf.local_spectrum(x, fs, len(x) // 2, sigma=sigma)
        axes[0].plot((np.arange(len(window)) - len(window)//2)/fs, window, label=f"sigma={sigma} samples")
        freq, fw = tf.centered_spectrum(window, fs)
        axes[1].plot(freq, np.abs(fw) / np.abs(fw).max())
    axes[0].set(xlabel="Time relative to center (s)", ylabel="Window amplitude", title="Gaussian windows")
    axes[1].set(xlabel="Frequency (Hz)", ylabel="Normalized magnitude", xlim=(-fs/30, fs/30), title="Wider in time, narrower in frequency")
    axes[0].legend(fontsize=8)
    save(fig, output, "gaussian_tradeoff")

    tone_fs, tones = inputs["tone_fs"], inputs["tones"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), layout="constrained")
    widths = [128, 512, 1024]
    for ax, width in zip(axes, widths):
        _spectrogram(ax, tones, tone_fs, width, limits=(-70, -10), ylim=(330, 490))
        ax.set_title(f"Hann window: {width} samples")
    save(fig, output, "two_tone_resolution")

    chirp_fs, chirps = datasets.hyperbolic_chirps()
    fig, axes = plt.subplots(2, 4, figsize=(14, 7), layout="constrained")
    for i, width in enumerate((128, 1024)):
        for j, window in enumerate(("hann", "hamming", "blackman", "boxcar")):
            _spectrogram(axes[i, j], chirps, chirp_fs, width, window, limits=(-90, -10), ylim=(0, 1900))
            axes[i, j].set_title(f"{window.capitalize()}, L={width}")
    save(fig, output, "chirp_windows")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), layout="constrained")
    for ax, recording in zip(axes, inputs["audio_signatures"]):
        source = recording["samples"]
        normalized = source / np.max(np.abs(source))
        _spectrogram(ax, normalized, recording["fs"], 512, limits=(-90, -20))
        ax.set_title(recording["label"])
    save(fig, output, "audio_signatures")

    _, _, coefficients = tf.stft(x, fs, 512, 448)
    restored = tf.inverse_stft(coefficients, fs, len(x), 512, 448)
    rows = [dict(window_samples=w, duration_ms=1000*w/tone_fs, bin_spacing_hz=tone_fs/w,
                 tone_spacing_hz=float(np.diff(inputs["tone_frequencies_hz"])[0])) for w in (64, 128, 256, 512, 1024)]
    write_csv(output / "resolution.csv", rows)
    result = dict(audio_sample_rate_hz=fs, tone_sample_rate_hz=tone_fs, tone_frequencies_hz=inputs["tone_frequencies_hz"],
                  stft_relative_roundtrip_error=float(np.linalg.norm(x-restored)/np.linalg.norm(x)),
                  resolutions=rows)
    write_json(output / "summary.json", result)
    return result


def run_wavelets(inputs, output):
    output = Path(output)
    set_style()
    image = inputs["image"]
    sigma = 0.1
    noisy = image + np.random.default_rng(1234).normal(0, sigma, image.shape)
    levels, thresholds = list(range(1, 6)), [0.1, 0.2, 0.3, 0.4]
    grids, best_images, best_rows = {}, {}, {}
    all_rows = []
    for transform in ("dwt", "swt"):
        grid = np.zeros((len(levels), len(thresholds)))
        best_score = -np.inf
        for i, level in enumerate(levels):
            for j, threshold in enumerate(thresholds):
                restored = wavelets.denoise(noisy, threshold, level, transform=transform)
                score = psnr(image, restored)
                grid[i, j] = score
                row = dict(transform=transform, wavelet="sym8", level=level,
                           threshold=threshold, noise_sigma=sigma, psnr_db=score)
                all_rows.append(row)
                if score > best_score:
                    best_score, best_images[transform], best_rows[transform] = score, restored, row
        grids[transform] = grid
    write_csv(output / "threshold_sweep.csv", all_rows)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), layout="constrained")
    lower, upper = min(g.min() for g in grids.values()), max(g.max() for g in grids.values())
    for ax, transform in zip(axes, grids):
        grid = grids[transform]
        im = ax.imshow(grid, cmap="viridis", vmin=lower, vmax=upper, aspect="auto")
        for (i, j), score in np.ndenumerate(grid):
            ax.text(j, i, f"{score:.2f}", ha="center", va="center", fontsize=9,
                    color="white" if score < (lower+upper)/2 else "#14212c")
        ax.set(xticks=range(len(thresholds)), xticklabels=thresholds,
               yticks=range(len(levels)), yticklabels=levels, xlabel="Hard threshold", ylabel="Decomposition level",
               title=f"{transform.upper()} - PSNR (dB)")
    fig.colorbar(im, ax=list(axes), label="PSNR (dB)", shrink=0.8)
    save(fig, output, "threshold_heatmaps")
    baseline = psnr(image, noisy)
    fig = image_panel([image, noisy, best_images["dwt"], best_images["swt"]],
                      ["Reference", f"Noisy: {baseline:.2f} dB",
                       f"DWT: {best_rows['dwt']['psnr_db']:.2f} dB",
                       f"SWT: {best_rows['swt']['psnr_db']:.2f} dB"])
    save(fig, output, "denoising_comparison")

    fig, axes = plt.subplots(2, 3, figsize=(12, 6), layout="constrained")
    for i, name in enumerate(("Bumps", "Blocks")):
        x = pywt.data.demo_signal(name, n=2048)
        for j, wavelet in enumerate(("haar", "sym8", "bior3.1")):
            axes[i, j].plot(x, color="#bcc6ce", linewidth=0.8, label="Signal")
            approximation = wavelets.reconstruct_component(x, wavelet, level=5)
            axes[i, j].plot(approximation, linewidth=1, label="Coarse approximation")
            axes[i, j].set(title=f"{name} / {wavelet}", xlabel="Sample index", ylabel="Amplitude")
    axes[0, 0].legend(fontsize=8)
    save(fig, output, "wavelet_families")

    # Original chessboard resource for directional subband inspection.
    checker = inputs["chessboard"]
    coeffs = pywt.wavedec2(checker.astype(float), "haar", level=2, mode="periodization")
    array, _ = pywt.coeffs_to_array(coeffs)
    fig, axes = plt.subplots(1, 2, figsize=(9,4), layout="constrained")
    axes[0].imshow(checker, cmap="gray"); axes[0].set_title("Axis-aligned chessboard")
    axes[1].imshow(np.log1p(np.abs(array)), cmap="magma"); axes[1].set_title("2D Haar coefficient layout (log magnitude)")
    for ax in axes: ax.set_axis_off()
    save(fig, output, "coefficient_layout")

    fig = image_panel([image] + [wavelets.remove_orientation(image, name, wavelet="db4", level=3)
                                for name in ("all", "horizontal", "vertical", "diagonal")],
                      ["Reference", "Approximation only", "No horizontal details", "No vertical details", "No diagonal details"],
                      figsize=(16, 4))
    save(fig, output, "directional_filtering")

    signal = pywt.data.demo_signal("Bumps", n=2048)
    fig, axes = plt.subplots(4, 1, figsize=(11, 7), layout="constrained")
    axes[0].plot(signal); axes[0].set_title("Multiscale components of a Bumps signal (sym8)")
    for ax, level in zip(axes[1:], (1, 4, 7)):
        ax.plot(wavelets.reconstruct_component(signal, level=7, detail_level=level))
        ax.set(ylabel=f"Detail {level}", xlabel="Sample index")
    save(fig, output, "detail_scales")
    result = dict(noisy_psnr_db=baseline, noise_sigma=sigma, seed=1234,
                  data_range=1.0, image_shape=list(image.shape), best=best_rows,
                  selection="Oracle grid selection on this one known reference; not held-out performance.")
    write_json(output / "summary.json", result)
    return result


def _write_audio(path, data, fs):
    # A shared gain preserves relative amplitudes across channels within a file.
    gain = 0.95 / max(float(np.max(np.abs(data))), 1e-15)
    wavfile.write(path, fs, (np.asarray(data) * gain).astype(np.float32))


def run_separation(inputs, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    set_style()
    fs, sources = inputs["fs"], inputs["sources"]
    truth = np.array([np.pi/6, np.pi/2, 5*np.pi/6])
    mixtures = separation.mixing_matrix(truth) @ sources
    result = separation.separate(mixtures, fs)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    axes[0].scatter(mixtures[0, ::3], mixtures[1, ::3], s=1, alpha=0.25, rasterized=True)
    vectors = result["coefficients"].reshape(2, -1).T
    points = np.concatenate([vectors.real, vectors.imag])
    axes[1].scatter(points[::3, 0], points[::3, 1], s=1, alpha=0.3, rasterized=True)
    for ax in axes:
        ax.set(xlabel="Channel 1", ylabel="Channel 2")
        ax.set_aspect("equal", adjustable="datalim")
    axes[0].set_title("Time domain: overlapping contributions")
    axes[1].set_title("STFT coordinates: source directions emerge")
    save(fig, output, "sparse_geometry")

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    centers = (result["edges"][:-1]+result["edges"][1:])/2
    ax.bar(np.rad2deg(centers), result["counts"], width=180/35, color="#b7cfe5", label="Retained real/imaginary coordinates")
    for i, angle in enumerate(truth):
        ax.axvline(np.rad2deg(angle), color="#25324a", linestyle="--", label="True direction" if i==0 else None)
    for i, angle in enumerate(result["angles"]):
        ax.axvline(np.rad2deg(angle), color="#d95f02", label="Estimated direction" if i==0 else None)
    ax.set(xlabel="Mixing direction (degrees, modulo 180)", ylabel="Count", title="Three directions estimated from two channels")
    ax.legend(fontsize=8)
    save(fig, output, "estimated_directions")

    rows, aligned_outputs = [], {}
    for method in ("binary", "split_l1"):
        aligned, scores = separation.match_sources(sources, result[method])
        aligned_outputs[method] = aligned
        for i, (label, score) in enumerate(zip(inputs["labels"], scores)):
            mixture_baseline = max(si_sdr(sources[i], channel) for channel in mixtures)
            rows.append(dict(method=method, source=label, si_sdr_db=score,
                             best_mixture_si_sdr_db=mixture_baseline, improvement_db=score-mixture_baseline))
        for i, track in enumerate(aligned):
            _write_audio(output/f"{method}_source_{i+1}.wav", track, fs)
    for i, track in enumerate(sources):
        _write_audio(output/f"reference_source_{i+1}.wav", track, fs)
    _write_audio(output/"mixture_stereo.wav", mixtures.T, fs)
    write_csv(output/"separation_scores.csv", rows)
    angle_rows = [dict(source=label, true_degrees=float(np.rad2deg(a)),
                       estimated_degrees=float(np.rad2deg(b)), absolute_error_degrees=float(np.rad2deg(abs(a-b))))
                  for label, a, b in zip(inputs["labels"], truth, result["angles"])]
    write_csv(output/"mixing_directions.csv", angle_rows)

    fig, axes = plt.subplots(3, 1, figsize=(11, 7), layout="constrained")
    t = np.arange(sources.shape[1]) / fs
    for i, ax in enumerate(axes):
        ax.plot(t, sources[i], color="#a9b5c2", linewidth=0.7, label="Reference")
        ax.plot(t, aligned_outputs["split_l1"][i], linewidth=0.6, alpha=0.85, label="Split real/imaginary L1")
        ax.set(title=inputs["labels"][i], xlabel="Time (s)", ylabel="Amplitude")
    axes[0].legend(fontsize=8)
    save(fig, output, "reconstructed_sources")

    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    positions = np.arange(3)
    for k, method in enumerate(("binary", "split_l1")):
        values = [row["si_sdr_db"] for row in rows if row["method"]==method]
        ax.bar(positions + (k-0.5)*0.34, values, width=0.34, label="Binary masking" if k==0 else "Split real/imaginary L1")
    baselines = [row["best_mixture_si_sdr_db"] for row in rows[:3]]
    ax.scatter(positions, baselines, marker="x", color="#25324a", label="Best input channel")
    ax.set(xticks=positions, xticklabels=inputs["labels"], ylabel="SI-SDR (dB)", title="Measured reconstruction quality; higher is better")
    ax.legend(fontsize=8)
    save(fig, output, "separation_scores")

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    f, times, _ = tf.stft(mixtures, fs)
    ax.pcolormesh(times, f, result["labels"]+1, cmap="viridis", shading="auto", vmin=0, vmax=3)
    ax.set(xlabel="Time (s)", ylabel="Frequency (Hz)", title="Binary source assignments (0 = discarded; 1-3 = source index)")
    save(fig, output, "binary_assignments")

    sensitivity = []
    for ratio in (0.0, 0.08, 0.1, 0.15, 0.2):
        angles, _, _ = separation.estimate_directions(result["coefficients"], ratio)
        sensitivity.append(dict(energy_ratio=ratio, mean_angle_error_degrees=float(np.rad2deg(np.mean(abs(angles-truth))))))
    write_csv(output/"direction_sensitivity.csv", sensitivity)
    summary = dict(fs=fs, samples=sources.shape[1], window_samples=128, overlap_samples=32,
                   energetic_bin_ratio=0.1, discard_percentile=50,
                   directions=angle_rows, scores=rows, direction_sensitivity=sensitivity,
                   mean_si_sdr_db={method:float(np.mean([r["si_sdr_db"] for r in rows if r["method"]==method]))
                                   for method in ("binary", "split_l1")})
    write_json(output/"summary.json", summary)
    return summary


def run_restoration(inputs, output):
    output = Path(output)
    set_style()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    qrows = []
    u, v = np.meshgrid(np.linspace(-0.7,0.7,80), np.linspace(-0.7,0.7,80))
    axes[1].contour(u,v,0.5*(u*u+8*v*v),levels=12,colors="#d0d8e0",linewidths=0.7)
    for step in (0.25,0.225,0.2,0.05):
        trajectory, costs = opt.quadratic_descent(step)
        axes[0].semilogy(costs, label=f"step={step}")
        axes[1].plot(*trajectory.T, ".-", markersize=2, label=f"step={step}")
        qrows.append(dict(step=step, iterations=30, final_objective=float(costs[-1]),
                          final_distance=float(np.linalg.norm(trajectory[-1]))))
    axes[0].set(xlabel="Iteration", ylabel="Objective", title="At step=0.25 the stiff component does not decay")
    axes[1].set(xlabel="First coordinate", ylabel="Second coordinate", title="Trajectories on an anisotropic quadratic")
    axes[0].legend(fontsize=8)
    save(fig, output, "step_size_convergence")
    write_csv(output/"quadratic_steps.csv", qrows)
    random_rows = []
    rng_init = np.random.default_rng(42)
    for initial in rng_init.uniform(-0.6, 0.6, size=(3,2)):
        _, costs = opt.quadratic_descent(0.2, initial=initial)
        random_rows.append(dict(initial_x=float(initial[0]), initial_y=float(initial[1]), final_objective=float(costs[-1])))
    write_csv(output/"random_initialization.csv", random_rows)

    image = inputs["image"]
    sigma2 = np.mean(image**2)/10**(20/10)
    noisy = image + np.random.default_rng(0).normal(0, np.sqrt(sigma2), image.shape)
    restored = opt.denoise(noisy, 8, iterations=100)
    mask = np.random.default_rng(42).random(image.shape) < 0.1
    observed = image*mask
    filled = opt.inpaint(observed, mask, iterations=300)
    fig = image_panel([image, noisy, restored.image], ["Reference", f"Noisy: {psnr(image,noisy):.2f} dB",
                       f"Tikhonov, lambda=8: {psnr(image,restored.image):.2f} dB"])
    save(fig, output, "tikhonov_denoising")
    fig = image_panel([image, observed, filled.image], ["Reference", f"Observed: {100*mask.mean():.1f}% of pixels",
                       f"Reconstructed: {psnr(image,filled.image):.2f} dB"])
    save(fig, output, "inpainting")
    fig, axes = plt.subplots(1,2,figsize=(11,4),layout="constrained")
    for ax, result, title in zip(axes, (restored,filled), ("Denoising", "Inpainting")):
        ax.semilogy(result.costs)
        ax.set(xlabel="Iteration",ylabel="Objective",title=title)
    save(fig, output, "restoration_convergence")

    rows = []
    for weight in (0.05, 0.2, 1, 8):
        estimate = opt.denoise(noisy, weight, iterations=100)
        rows.append(dict(regularization=weight, iterations=100, psnr_db=psnr(image,estimate.image),
                         mse=mse(image,estimate.image)))
    write_csv(output/"regularization_sweep.csv", rows)
    fig, ax = plt.subplots(figsize=(8,4),layout="constrained")
    ax.semilogx([r["regularization"] for r in rows], [r["psnr_db"] for r in rows],"o-")
    ax.axhline(psnr(image,noisy),linestyle="--",color="#d95f02",label="Noisy input")
    ax.set(xlabel="Regularization weight",ylabel="PSNR (dB)",title="A lower objective does not guarantee a better reconstruction")
    ax.legend()
    save(fig, output, "regularization_tradeoff")
    result = dict(input_snr_db=20, noise_seed=0, mask_seed=42,
                  observed_fraction=float(mask.mean()), noisy_psnr_db=psnr(image,noisy),
                  tikhonov_psnr_db=psnr(image,restored.image),
                  inpainting_psnr_db=psnr(image,filled.image),
                  inpainting_missing_psnr_db=psnr(image[~mask],filled.image[~mask]),
                  observed_pixel_max_error=float(np.max(np.abs(filled.image[mask]-image[mask]))),
                  denoising_iterations=100, inpainting_iterations=300,
                  denoising_objective_monotone=bool(np.all(np.diff(restored.costs)<=1e-9)),
                  inpainting_objective_monotone=bool(np.all(np.diff(filled.costs)<=1e-9)),
                  regularization_sweep=rows)
    write_json(output/"summary.json",result)
    return result


STUDIES = {"time_frequency":run_time_frequency, "wavelets":run_wavelets,
           "separation":run_separation, "restoration":run_restoration}


def run_all(output="results", data_dir=None):
    inputs = datasets.load_inputs(data_dir)
    output = Path(output)
    summary = {name:function(inputs,output/name) for name,function in STUDIES.items()}
    summary["inputs"] = "Original course image and recordings"
    summary["source_header_sample_rates_hz"] = inputs["source_header_sample_rates_hz"]
    summary["environment"] = {name:importlib.metadata.version(name) for name in
                              ("numpy","scipy","matplotlib","PyWavelets","Pillow")}
    summary["environment"]["python"] = platform.python_version()
    write_json(output/"summary.json",summary)
    return summary
