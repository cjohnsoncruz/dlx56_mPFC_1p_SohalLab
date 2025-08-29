# custom_module_imports.py
# Ensure robust sys.path setup before local imports
import sys
import os
_here = os.path.dirname(os.path.abspath(__file__)) # add this directory (Function .py Storage) to sys.path
if _here not in sys.path:
    sys.path.append(_here)
# add plot_posthoc_test/src to sys.path
_plot_posthoc_src = os.path.join(_here, 'plot_posthoc_test', 'src')
if os.path.isdir(_plot_posthoc_src) and _plot_posthoc_src not in sys.path:
    sys.path.append(_plot_posthoc_src)

"""
Centralized, explicit imports without wildcard re-exports.

Usage examples in notebooks or modules:
  - helper functions:          hf.save_fig_in_main_fig_dir(...)
  - axis modifiers:            axmod.set_ax_title_xlabel_ylabel(ax, labels)
  - dataframe annotations:     dfanno.add_rule_pair_col(df, ...)
  - preprocessing utilities:   pp.run_min_max_norm_on_timeseries(...)
  - plotting config:           sns_cfg.apply_sns_theme()
  - timeseries binning:        ts_bin.some_function(...)
  - taco hypothesis testing:   taco_ht.some_test(...)
  - posthoc plotting:          pst.plot_with_stats(...)
"""

# Module-level, namespaced imports (preferred over star-imports)
import helper_functions as hf
import ax_modifier_functions as axmod
import dataframe_annotation_functions as dfanno
import preprocess_data as pp
import sns_plotting_config as sns_cfg

# Posthoc plotting module (import module, not names)
from plot_posthoc_test import plot_stat_annotate as pst