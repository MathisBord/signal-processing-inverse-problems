"""Execute project notebooks in fresh IPython processes, saving rich outputs.

Static figures and audio displays do not require a local network kernel or
changes to user Jupyter configuration.
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout",type=int,default=600,help="Timeout per notebook, in seconds")
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    environment={**os.environ,"MPLBACKEND":"Agg","PYTHONIOENCODING":"utf-8"}
    for path in sorted((root/"notebooks").glob("*.ipynb")):
        completed=subprocess.run([sys.executable,str(root/"scripts/notebook_worker.py"),str(path)],
                                 timeout=args.timeout,cwd=root/"notebooks",env=environment,
                                 capture_output=True,text=True,encoding="utf-8",errors="replace",
                                 creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if completed.stdout:
            print(completed.stdout,end="",flush=True)
        if completed.stderr:
            print(completed.stderr,end="",file=sys.stderr,flush=True)
        if completed.returncode:
            raise SystemExit(completed.returncode)


if __name__=="__main__":
    main()
