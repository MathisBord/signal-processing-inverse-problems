"""Execute one project notebook through IPython without a network kernel.

Used by execute_notebooks.py. Each invocation is a new interpreter. Rich displays
are captured through IPython's MIME formatter, never fabricated from old output.
"""

import base64
from contextlib import redirect_stdout, redirect_stderr
import io
import os
from pathlib import Path
import sys
import tempfile
import nbformat
from IPython.core.interactiveshell import InteractiveShell
from traitlets.config import Config
from clean_notebooks import clean


class Stream(io.TextIOBase):
    def __init__(self,outputs,name):
        self.outputs,self.name=outputs,name

    def write(self,text):
        if text:
            if self.outputs and self.outputs[-1].output_type=="stream" and self.outputs[-1].name==self.name:
                self.outputs[-1].text+=text
            else:
                self.outputs.append(nbformat.v4.new_output("stream",name=self.name,text=text))
        return len(text)

    def flush(self): pass


def main():
    os.environ["MPLBACKEND"]="Agg"
    path=Path(sys.argv[1]).resolve()
    notebook=nbformat.read(path,as_version=4)
    runtime=tempfile.TemporaryDirectory(prefix="signal-inverse-ipython-")
    config=Config()
    config.HistoryManager.enabled=False
    config.HistoryManager.hist_file=":memory:"
    shell=InteractiveShell.instance(ipython_dir=runtime.name,config=config)
    shell.colors="NoColor"
    execution_count=0
    for cell in notebook.cells:
        if cell.cell_type!="code":
            continue
        execution_count+=1
        outputs=[]
        def publish(data,metadata=None,**kwargs):
            clean={key:base64.b64encode(value).decode("ascii") if isinstance(value,bytes) else value
                   for key,value in data.items()}
            outputs.append(nbformat.v4.new_output("display_data",data=clean,metadata=metadata or {}))
        shell.display_pub.publish=publish
        with redirect_stdout(Stream(outputs,"stdout")),redirect_stderr(Stream(outputs,"stderr")):
            result=shell.run_cell(cell.source,store_history=False,silent=False)
        if result.error_before_exec or result.error_in_exec:
            print(f"Failed {path.name}, cell {execution_count}: {result.error_before_exec or result.error_in_exec}",file=sys.__stderr__,flush=True)
            raise RuntimeError(f"{path.name}, cell {execution_count}: {result.error_before_exec or result.error_in_exec}")
        cell.execution_count=execution_count
        cell.outputs=outputs
    notebook.metadata.kernelspec={"display_name":"Python 3","language":"python","name":"python3"}
    nbformat.validate(notebook)
    nbformat.write(notebook,path)
    clean(path)
    print(f"Executed {path.name}: {execution_count} code cells (fresh IPython process)",flush=True)
    runtime.cleanup()


if __name__=="__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc(file=sys.__stderr__)
        raise SystemExit(1)
