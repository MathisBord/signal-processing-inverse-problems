"""Remove machine-specific notebook metadata while preserving visible results."""

from pathlib import Path
import argparse
import nbformat


def clean(path, clear_outputs=False):
    notebook=nbformat.read(path,as_version=4)
    notebook.metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
                       "language_info":{"name":"python"}}
    for cell in notebook.cells:
        cell.metadata={}
        if cell.cell_type=="code" and clear_outputs:
            cell.outputs=[]
            cell.execution_count=None
    nbformat.validate(notebook)
    nbformat.write(notebook,path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clear-outputs",action="store_true",help="Also remove figures, tables and execution counts")
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    for path in sorted((root/"notebooks").glob("*.ipynb")):
        clean(path,args.clear_outputs)
        print(f"Cleaned metadata: {path.name}; outputs {'cleared' if args.clear_outputs else 'preserved'}")


if __name__=="__main__":
    main()
