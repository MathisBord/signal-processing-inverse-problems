"""Reproduce all four studies using the bundled original course resources."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from signal_inverse.experiments import run_all


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    result = run_all(args.output)
    print(json.dumps({"output": str(args.output), "environment": result["environment"]}, indent=2))


if __name__ == "__main__":
    main()
