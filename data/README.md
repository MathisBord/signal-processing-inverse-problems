# Original experiment inputs

These are byte-for-byte copies of the image and audio resources used in the
original Representation of Signals and Inverse Problems labs at Centrale Lille.
The original course folder is never changed by the project.

| Files | Study |
| --- | --- |
| `audio/time_frequency/bird.wav`, `glockenspiel_mono.wav`, `desactive_mono.wav` | Waveforms, local Fourier spectra and audio spectrograms |
| `audio/time_frequency/signal_2sinus.mat` | Original 400/424 Hz two-tone signal, sampled at 4096 Hz |
| `images/boat.png`, `images/chessboard.png` | Wavelets, denoising, coefficient layout and image restoration |
| `audio/separation/bird.wav`, `female.wav`, `male.wav` | Three-source, two-channel separation |

`manifest.json` records a SHA-256 digest for every included source file.
The loader preserves the original bird trimming and 16,384-sample excerpts.
For separation, the WAV headers are 44.1, 16 and 16 kHz, while the original
lab interprets all three sample arrays at 15 kHz without resampling. This
sample-based convention is preserved and explained in the notebooks.

The first lab also defines two analytical hyperbolic chirps, and the wavelet
lab uses the standard Bumps and Blocks test signals. These original exercises
are evaluated alongside the supplied recordings and images.
