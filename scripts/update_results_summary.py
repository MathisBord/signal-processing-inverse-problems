"""Build documentation and a compact visual overview from measured JSON results."""

from pathlib import Path
import json
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from signal_inverse.plotting import set_style


def main():
    directory=ROOT/"results"
    summary=json.loads((directory/"summary.json").read_text(encoding="utf-8"))
    # Read each measured study summary so notebook re-execution can update docs.
    for study in ("time_frequency","wavelets","separation","restoration"):
        summary[study]=json.loads((directory/study/"summary.json").read_text(encoding="utf-8"))
    (directory/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    w,s,r=summary["wavelets"],summary["separation"],summary["restoration"]
    selected=(
        "| Experiment | Measured result |\n| --- | --- |\n"
        f"| Wavelet denoising | Noisy input **{w['noisy_psnr_db']:.2f} dB** PSNR; best tested DWT **{w['best']['dwt']['psnr_db']:.2f} dB**; SWT **{w['best']['swt']['psnr_db']:.2f} dB** |\n"
        f"| Three-source / two-channel separation | Mean SI-SDR: binary masking **{s['mean_si_sdr_db']['binary']:.2f} dB**, split real/imaginary L1 **{s['mean_si_sdr_db']['split_l1']:.2f} dB** |\n"
        f"| Inpainting | **{100*r['observed_fraction']:.2f}%** observed pixels; missing-pixel PSNR **{r['inpainting_missing_psnr_db']:.2f} dB**; observed-pixel error **{r['observed_pixel_max_error']:.0f}** |"
    )
    path=ROOT/"README.md"
    readme=path.read_text(encoding="utf-8")
    start,end="<!-- measured-results:start -->","<!-- measured-results:end -->"
    before,rest=readme.split(start)
    _,after=rest.split(end)
    path.write_text(before+start+"\n"+selected+"\n"+end+after,encoding="utf-8")
    scores="\n".join(f"| {x['method']} | {x['source']} | {x['si_sdr_db']:.2f} | {x['best_mixture_si_sdr_db']:.2f} | {x['improvement_db']:+.2f} |" for x in s["scores"])
    weights="\n".join(f"| {x['regularization']} | {x['psnr_db']:.2f} |" for x in r["regularization_sweep"])
    directions="\n".join(f"| {x['source']} | {x['true_degrees']:.2f} | {x['estimated_degrees']:.2f} | {x['absolute_error_degrees']:.2f} |" for x in s["directions"])
    note=f'''# Measured results

These values are generated from the checked-in implementation, using the original
boat image and bird/voice recordings from the course labs. They are not quoted from the original notebooks or papers.
The exact inputs, seeds and configuration are described in
[reproducibility](reproducibility.md). Each study exports its complete CSV and
JSON outputs under `results/`.

## Time-frequency analysis

The relative STFT round-trip error is
**{summary['time_frequency']['stft_relative_roundtrip_error']:.3e}**.
For the original 400/424 Hz two-tone file sampled at 4096 Hz, window lengths of 128, 512 and 1024 samples
give FFT bin spacings of 32, 8 and 4 Hz. Bin spacing is not itself a universal
frequency-resolution bound: the window's spectral shape also matters.

![Nearby tones under three window lengths](../results/time_frequency/two_tone_resolution.png)

## Wavelet denoising

Gaussian noise uses standard deviation {w['noise_sigma']} and seed {w['seed']}.
The same noise realization is used for every setting. PSNR uses range one
and scores un-clipped reconstructions. This known-reference sweep chooses
among five levels and four thresholds; it is not a held-out benchmark.

| Method | PSNR (dB) | Selected level | Selected threshold |
| --- | --- | --- | --- |
| Noisy input | {w['noisy_psnr_db']:.2f} | - | - |
| DWT, sym8 | {w['best']['dwt']['psnr_db']:.2f} | {w['best']['dwt']['level']} | {w['best']['dwt']['threshold']} |
| SWT, sym8 | {w['best']['swt']['psnr_db']:.2f} | {w['best']['swt']['level']} | {w['best']['swt']['threshold']} |

![DWT and SWT parameter sweeps on common color limits](../results/wavelets/threshold_heatmaps.png)

The selected settings maximize PSNR only over the tested finite grid.
This does not establish an unrestricted optimum or automatic parameter rule.
SWT has higher PSNR on this particular boat image and noise realization. The result must
not be generalized to every image or noise level.

## Three sources from two mixtures

The histogram estimator is applied to the bird and voice recordings.
Its estimated directions are evaluated against the known mixing directions;
those known directions are never substituted into reconstruction.

| Source | True direction (deg) | Estimated (deg) | Absolute error (deg) |
| --- | --- | --- | --- |
{directions}

| Reconstruction | Source | SI-SDR (dB) | Best mixture (dB) | Improvement (dB) |
| --- | --- | --- | --- | --- |
{scores}

![Per-source scores and best input-channel baselines](../results/separation/separation_scores.png)

Split real/imaginary L1 improves the mean score and both voice scores here;
binary masking performs better for the bird. All three sources are original
course recordings, interpreted at the original common 15 kHz analysis rate. The mean is an unweighted mean of the three per-source dB scores.

Listen to the [mixture](../results/separation/mixture_stereo.wav),
[reference source 1](../results/separation/reference_source_1.wav),
[binary reconstruction](../results/separation/binary_source_1.wav)
and [sparse reconstruction](../results/separation/split_l1_source_1.wav).
All three source tracks are exported. Preview files have separate peak gains;
the evaluation uses the arrays before playback normalization.

## Tikhonov denoising

The expected input SNR is 20 dB. The resulting noisy image has PSNR
**{r['noisy_psnr_db']:.2f} dB**. The original baseline (lambda=8, 100 iterations)
reaches **{r['tikhonov_psnr_db']:.2f} dB**. Changing the regularization weight
changes the balance between fidelity and smoothness:

| Regularization weight | PSNR (dB), 100 iterations |
| --- | --- |
{weights}

A lower optimization objective is not a promise of better PSNR. The comparison
retains the original lambda=8 baseline even when another tested value performs
better. No reference-aware choice is advertised as an automatic deployment rule.

## Inpainting

The seed-42 binary mask observes **{100*r['observed_fraction']:.2f}%** of pixels.
After 300 projected-gradient iterations:

| Measurement | Value |
| --- | --- |
| Full-image PSNR | {r['inpainting_psnr_db']:.2f} dB |
| Missing-pixel-only PSNR | {r['inpainting_missing_psnr_db']:.2f} dB |
| Maximum error on observed pixels | {r['observed_pixel_max_error']:.1f} |
| Tested objective histories nonincreasing | Denoising: {r['denoising_objective_monotone']}; inpainting: {r['inpainting_objective_monotone']} |

![Reconstruction from about one tenth of the pixels](../results/restoration/inpainting.png)

The original boat image contains edges and texture that the smoothness model
can blur. These scores do not imply equivalent performance on other images. Missing fine structure
cannot be uniquely recovered from a smoothness prior alone.

## Environment

```json
{json.dumps(summary['environment'],indent=2)}
```

Verification is local; no GitHub Actions workflow is included.
See [verification status](validation.md).
'''
    (ROOT/"docs/results.md").write_text(note,encoding="utf-8")
    set_style()
    import numpy as np
    from signal_inverse.datasets import load_inputs
    from signal_inverse.time_frequency import spectrogram_db
    from signal_inverse.wavelets import denoise
    from signal_inverse.optimization import inpaint
    inputs=load_inputs()
    scene=inputs["image"]
    noisy=scene+np.random.default_rng(1234).normal(0,0.1,scene.shape)
    best=w["best"]["swt"]
    clean=denoise(noisy,best["threshold"],best["level"],transform="swt")
    mask=np.random.default_rng(42).random(scene.shape)<0.1
    filled=inpaint(mask*scene,mask).image
    fig,axes=plt.subplots(2,2,figsize=(13,8),layout="constrained")
    fs=inputs["audio_fs"]
    bird=inputs["audio"] / max(np.max(np.abs(inputs["audio"])), 1e-15)
    f,t,db=spectrogram_db(bird,fs,width=512)
    axes[0,0].pcolormesh(t,f,db,cmap="magma",vmin=-90,vmax=-10,shading="auto")
    axes[0,0].set(xlabel="Time (s)",ylabel="Frequency (Hz)",ylim=(0,12000),title="01  |  Reveal changing frequencies")
    axes[0,1].imshow(np.concatenate([noisy,clean],axis=1),cmap="gray",vmin=0,vmax=1)
    axes[0,1].set_title(f"02  |  Denoise across scales: {w['noisy_psnr_db']:.2f} to {best['psnr_db']:.2f} dB")
    axes[0,1].set_axis_off()
    positions=np.arange(3)
    for k,method in enumerate(("binary","split_l1")):
        scores=[row["si_sdr_db"] for row in s["scores"] if row["method"]==method]
        axes[1,0].bar(positions+(k-0.5)*0.34,scores,width=0.34,label="Binary mask" if k==0 else "Split real/imaginary L1")
    axes[1,0].set(xticks=positions,xticklabels=["Bird","Female voice","Male voice"],ylabel="SI-SDR (dB)",title="03  |  Separate three sources from two mixtures")
    axes[1,0].legend(fontsize=8)
    axes[1,1].imshow(np.concatenate([mask*scene,filled],axis=1),cmap="gray",vmin=0,vmax=1)
    axes[1,1].set_title(f"04  |  Reconstruct from {100*r['observed_fraction']:.2f}% of pixels")
    axes[1,1].set_axis_off()
    fig.savefig(directory/"overview.png",dpi=140,bbox_inches="tight")
    plt.close(fig)
    print("Updated README measurements, docs/results.md and overview.png")


if __name__=="__main__":
    main()
