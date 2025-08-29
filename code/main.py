import sys
import asyncio
if sys.platform.startswith("win"):# Use a selector-based event loop compatible with pyzmq/tornado
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from pathlib import Path
import nbformat
from nbclient import NotebookClient

repo_root = Path(__file__).resolve().parents[1]
code = repo_root / "code"
out = repo_root / "results" / "executed_notebooks"
out.mkdir(parents=True, exist_ok=True)

notebooks = [
    "Figure 1 & 2 Analysis and Figure Generation Code.ipynb",
    "Figure 2, 4+ Ensemble Analysis and Figure Code.ipynb",
    "Figure 3-7 & Sup Figure 1-2 Analysis and Figure Code.ipynb",
    "Figure 5-7 Autoencoder Analysis and Figure Code.ipynb",
]

for nb_name in notebooks:
    nb_path = code / nb_name
    print(f"Running: {nb_path}")
    nb = nbformat.read(nb_path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=None,              
        kernel_name="python3",
        allow_errors=False,
        resources={"metadata": {"path": str(code)}},  # cwd for relative paths
    )
    client.execute()
    out_path = out / (nb_path.stem + "_executed.ipynb")
    nbformat.write(nb, out_path)
    print(f"Saved: {out_path}")