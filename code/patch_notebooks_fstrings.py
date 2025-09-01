import re
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "code"

NOTEBOOKS = [
    CODE / "Figure 1 & 2 Analysis and Figure Generation Code.ipynb",
    CODE / "Figure 2, 4+ Ensemble Analysis and Figure Code.ipynb",
    CODE / "Figure 3-7 & Sup Figure 1-2 Analysis and Figure Code.ipynb",
    CODE / "Figure 5-7 Autoencoder Analysis and Figure Code.ipynb",
]

# Regex to turn replace("_", " ") into replace('_', ' ')
RE_REPLACE_UNDERSCORE = re.compile(r'replace\("_",\s*"\s"\)')

# Helper to patch a single source string
def patch_source(src: str) -> str:
    new = src
    # 1) Inside f-strings, switch {"_".join(...)} -> {'_'.join(...)} via literal replacement
    new = new.replace('{"_".join', "{'_'.join")
    # 2) Switch replace("_", " ") -> replace('_', ' ')
    new = re.sub(r'replace\("_",\s*" "\)', "replace('_', ' ')", new)
    return new


def patch_notebook(path: Path) -> bool:
    nb = nbf.read(path, as_version=4)
    changed = False
    for cell in nb.cells:
        if cell.get('cell_type') == 'code' and isinstance(cell.get('source'), str):
            patched = patch_source(cell['source'])
            if patched != cell['source']:
                cell['source'] = patched
                changed = True
    if changed:
        nbf.write(nb, path)
    return changed


def main():
    any_changed = False
    for nb_path in NOTEBOOKS:
        if nb_path.exists():
            changed = patch_notebook(nb_path)
            print(f"Patched: {nb_path.name}: {changed}")
            any_changed = any_changed or changed
        else:
            print(f"Missing notebook: {nb_path}")
    if not any_changed:
        print("No changes were necessary.")


if __name__ == '__main__':
    main()
