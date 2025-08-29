"""
Centralized notebook setup for path robustness.
Usage in notebooks (first cell):
    # Optional: for live reloads
    %load_ext autoreload
    %autoreload 2
    import notebook_setup
    notebook_setup.setup()
This will:
- Add "Function .py Storage" to sys.path
- Add "Function .py Storage/plot_posthoc_test/src" to sys.path
"""
from __future__ import annotations
import os
import sys
from typing import Dict

def _add_path(path: str) -> bool:
    if os.path.isdir(path) and path not in sys.path:
        sys.path.append(path)
        return True
    return False

def setup() -> Dict[str, str]:
    """Add project-local paths to sys.path for robust imports.
    Returns a dict of important resolved paths for convenience/logging.
    """
    here = os.path.dirname(os.path.abspath(__file__))

    func_storage = os.path.join(here, 'Function .py Storage')
    plot_posthoc_src = os.path.join(func_storage, 'plot_posthoc_test', 'src')

    added_func = _add_path(func_storage)
    added_posthoc = _add_path(plot_posthoc_src)

    return {
        'repo_root': here,
        'function_py_storage': func_storage,
        'plot_posthoc_src': plot_posthoc_src,
        'added_function_py_storage': str(added_func),
        'added_plot_posthoc_src': str(added_posthoc),
    }

if __name__ == '__main__':
    info = setup()
    print('Notebook setup complete:')
    for k, v in info.items():
        print(f'  {k}: {v}')
