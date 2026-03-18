"""
Backport fix for seaborn#3478: heatmap annotations missing on mpl >= 3.8.

Matplotlib 3.8 changed pcolormesh to return PolyQuadMesh whose get_array()
returns a 2D array instead of flat. Seaborn 0.12.x's _annotate_heatmap zips
it with flat iterators, so only the first row renders annotations.

Fix: mesh.get_array() -> mesh.get_array().flat  (one line in matrix.py:255)

Run once after installing/reinstalling seaborn 0.12.x:
    python patch_seaborn_heatmap.py
"""
import importlib
import pathlib
import sys


def patch():
    import seaborn
    matrix_path = pathlib.Path(seaborn.__file__).parent / "matrix.py"
    text = matrix_path.read_text(encoding="utf-8")

    old = "mesh.get_array(), mesh.get_facecolors(),"
    new = "mesh.get_array().flat, mesh.get_facecolors(),"

    if new in text:
        print("seaborn/matrix.py is already patched.")
        return

    if old not in text:
        print(f"ERROR: Could not find target string in {matrix_path}")
        print("This patch is written for seaborn 0.12.x — check your version.")
        sys.exit(1)

    text = text.replace(old, new, 1)
    matrix_path.write_text(text, encoding="utf-8")
    print(f"Patched {matrix_path}")
    print(f"  {old}")
    print(f"  -> {new}")


if __name__ == "__main__":
    patch()
