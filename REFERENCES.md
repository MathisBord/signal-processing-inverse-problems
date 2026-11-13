# References and their role in the project

References support specific models and implementation choices. This project
does not claim a new algorithm or a reproduction of published benchmark scores.
Equations and explanatory text have been rewritten for this implementation.

1. **Pau Bofill and Michael Zibulevsky (2001).** “Underdetermined blind source
   separation using sparse representations.” *Signal Processing*, 81(11),
   2353-2362. [DOI: 10.1016/S0165-1684(01)00120-7](https://doi.org/10.1016/S0165-1684(01)00120-7).
   Original source for sparse transformed-domain separation and two-dimensional
   minimum-L1 reconstruction. Sections 4-6 are mapped to the implementation in
   [the method note](docs/source-separation.md).

2. **Estefania Cano, Derry FitzGerald, Antoine Liutkus, Mark D. Plumbley and
   Fabian-Robert Stoter (2019).** “Musical Source Separation: An Introduction.”
   *IEEE Signal Processing Magazine*, 36(1), 31-40.
   [DOI: 10.1109/MSP.2018.2874719](https://doi.org/10.1109/MSP.2018.2874719).
   [Author's publication page](https://ecanoc.github.io/publication/spm19/).
   The “Musical source position models” section motivates spatial mixture
   geometry and time-frequency masking. This is a survey, not a claim that
   this repository implements every method it describes.

3. **Jonathan Le Roux, Scott Wisdom, Hakan Erdogan and John R. Hershey (2019).**
   “SDR - Half-Baked or Well Done?” *ICASSP 2019*, 626-630.
   [DOI: 10.1109/ICASSP.2019.8683855](https://doi.org/10.1109/ICASSP.2019.8683855).
   [Author-hosted paper](https://merl.com/publications/docs/TR2019-013.pdf).
   Source for the SI-SDR evaluation added in the public edition. The project
   computes the zero-mean projection/residual form directly.

4. **SciPy documentation.**
   [STFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.stft.html),
   [inverse STFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.istft.html),
   [NOLA condition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.check_NOLA.html).
   Analysis/synthesis conventions, complete window coverage and overlap-add.
   The matched legacy STFT functions are retained for continuity with the
   original implementation; no migration to a new algorithm is claimed.

5. **PyWavelets documentation.**
   [Multilevel transforms](https://pywavelets.readthedocs.io/en/latest/regression/multilevel.html),
   [stationary wavelet transform](https://pywavelets.readthedocs.io/en/latest/ref/swt-stationary-wavelet-transform.html),
   [DWT and decomposition levels](https://pywavelets.readthedocs.io/en/stable/ref/dwt-discrete-wavelet-transform.html).
   Coefficient conventions, inverse transforms, boundary conditions and SWT
   normalization. The standard Bumps and Blocks test signals are generated
   with `pywt.data.demo_signal`; no course-provided image is redistributed.

6. **Representation of Signals and Inverse Problems, Centrale Lille.**
   Course materials credited to P.-A. Thouvenin in the supplied README files,
   academic year 2025-2026. The original collaborative project supplied the
   four experimental themes and baseline implementations. Course handouts,
   question sheets, slide screenshots and article PDFs are not included.

## Reading order

Start with the source-position discussion in Cano et al., then Sections 4-6
of Bofill & Zibulevsky. Follow the distinction between mixture geometry,
direction estimation and source reconstruction. Read Le Roux et al. when
interpreting reconstruction scores. Public results are generated here and
are not numbers quoted from these papers.
