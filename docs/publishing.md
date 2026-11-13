# Publishing and rebuilding

The repository contains the original input assets in `data/`, executable
notebooks, shared implementations and computed results under `results/`.
Run the README verification commands before publishing changes.

Suggested topics: `signal-processing`, `inverse-problems`, `wavelets`,
`source-separation`, `optimization`, `python`, `jupyter-notebook`.

To rebuild a standalone archive:

```bash
python scripts/package_project.py
```

The archive includes project files, bundled input resources and computed
results. Git internals, caches, environments and temporary files are excluded.
