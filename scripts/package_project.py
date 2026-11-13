"""Create a project ZIP containing original inputs, code and computed results."""

import argparse
from pathlib import Path
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ROOT_FILES={"README.md","REFERENCES.md","references.bib","LICENSE","NOTICE.md",
            "pyproject.toml","requirements-reproduce.txt",".gitignore",".gitattributes"}
PUBLIC_DIRS={"src","scripts","tests","docs","notebooks",".github","data","results"}
EXCLUDED_PARTS={"__pycache__",".pytest_cache",".ipynb_checkpoints",".git",".venv","local",".local"}


def public_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative=path.relative_to(ROOT)
        if any(p in EXCLUDED_PARTS or p.endswith(".egg-info") for p in relative.parts):
            continue
        if relative.parts[0] in PUBLIC_DIRS or relative.as_posix() in ROOT_FILES:
            yield path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT.parent/(ROOT.name+".zip"))
    args=parser.parse_args()
    paths=list(public_files())
    for path in paths:
        if path.suffix==".ipynb":
            notebook=json.loads(path.read_text(encoding="utf-8"))
            if any(o.get("output_type")=="error" for c in notebook["cells"] for o in c.get("outputs",[])):
                raise ValueError(f"Refusing to package a notebook with errors: {path.name}")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in paths:
            archive.write(path,ROOT.name+"/"+path.relative_to(ROOT).as_posix())
    print(f"Packaged {len(paths)} public files: {args.output}")
    print(f"Archive size: {args.output.stat().st_size/1024/1024:.2f} MiB. Original inputs included; Git internals excluded.")


if __name__=="__main__":
    main()
