# Verification record

Verification performed on 13 November 2026 using Python 3.12.14 and the pinned
dependencies in requirements-reproduce.txt.

| Check | Outcome |
| --- | --- |
| Numerical and input-integrity tests | 20 passed |
| Package installation | Editable package built and installed in an isolated environment |
| Four studies | Executed from the CLI using the included original course resources |
| Notebook execution | Four fresh IPython processes; 24 code cells; no saved error outputs |
| Input provenance | All nine bundled resources match the SHA-256 hashes of their source files |
| Original notebooks | All four completed source notebooks unchanged after preparation |
| Two-tone input | Original file confirmed at 4096 Hz, with peaks at 400 and 424 Hz |
| Figure review | Overview, boat-image denoising/restoration and audio scores inspected |
| Project links and data references | Checked locally before publication |
| Metadata | Notebook execution metadata and optional PNG text chunks cleaned |
| GitHub Actions | No workflow included; checks run locally |

Figures, tables and audio previews come from executed code. Metrics reported
in the README and results page are generated from measured JSON summaries.
The original course directory is read only throughout this workflow.
