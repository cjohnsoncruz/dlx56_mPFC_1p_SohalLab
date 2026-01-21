"""
Investigate differences between NEW and CANON time-series parquet files.
Compares mean activity in task stages for each cell.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# File paths
data_dir = Path(r"C:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\data")
results_dir = Path(r"C:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\results")

canon_path = data_dir / "Dlx56_Normalized Trial Calcium Timeseries_20_Jun_2025.parquet"
new_path = results_dir / "python-made_trial_timeseries_raster_2025-12-04 15.parquet"

print("="*80)
print("LOADING DATA")
print("="*80)

# Load both files
print(f"\nLoading CANON: {canon_path}")
canon_df = pd.read_parquet(canon_path)
print(f"  Shape: {canon_df.shape}")
print(f"  Memory: {canon_df.memory_usage(deep=True).sum() / 1e6:.2f} MB")

print(f"\nLoading NEW: {new_path}")
new_df = pd.read_parquet(new_path)
print(f"  Shape: {new_df.shape}")
print(f"  Memory: {new_df.memory_usage(deep=True).sum() / 1e6:.2f} MB")

# Examine structure
print("\n" + "="*80)
print("STRUCTURE COMPARISON")
print("="*80)

print(f"\nCANON columns ({len(canon_df.columns)}):")
print(canon_df.columns.tolist()[:20], "...")

print(f"\nNEW columns ({len(new_df.columns)}):")
print(new_df.columns.tolist()[:20], "...")

# Get time-series columns for each
canon_ts_cols = [col for col in canon_df.columns if 's to' in col]
new_ts_cols = [col for col in new_df.columns if col.startswith(('f_', '-f_'))]

print(f"\nCANON time-series columns: {len(canon_ts_cols)}")
print(f"  Sample: {canon_ts_cols[:5]}")

print(f"\nNEW time-series columns: {len(new_ts_cols)}")
print(f"  Sample: {new_ts_cols[:5]}")

# Check metadata columns
print("\nCANON metadata columns:")
canon_meta = [col for col in canon_df.columns if col not in canon_ts_cols]
print(f"  {canon_meta}")

print("\nNEW metadata columns:")
new_meta = [col for col in new_df.columns if col not in new_ts_cols]
print(f"  {new_meta}")

# Check if there's a common identifier
print("\n" + "="*80)
print("IDENTIFYING KEY COLUMNS")
print("="*80)

# Look for stage/phase columns
stage_cols_canon = [col for col in canon_df.columns if 'stage' in col.lower() or 'phase' in col.lower()]
stage_cols_new = [col for col in new_df.columns if 'stage' in col.lower() or 'phase' in col.lower()]

print(f"\nCANON stage columns: {stage_cols_canon}")
print(f"NEW stage columns: {stage_cols_new}")

# Check unique values in stage columns
if stage_cols_canon:
    print(f"\nCANON unique stages in '{stage_cols_canon[0]}':")
    print(f"  {canon_df[stage_cols_canon[0]].unique()}")

if stage_cols_new:
    print(f"\nNEW unique stages in '{stage_cols_new[0]}':")
    print(f"  {new_df[stage_cols_new[0]].unique()}")

# Check for neuron/cell identifiers
cell_id_canon = [col for col in canon_df.columns if 'neuron' in col.lower() or 'cell' in col.lower()]
cell_id_new = [col for col in new_df.columns if 'neuron' in col.lower() or 'cell' in col.lower()]

print(f"\nCANON cell ID columns: {cell_id_canon}")
print(f"NEW cell ID columns: {cell_id_new}")

# Sample data
print("\n" + "="*80)
print("SAMPLE DATA")
print("="*80)

print("\nCANON first 3 rows (metadata only):")
print(canon_df[canon_meta].head(3))

print("\nNEW first 3 rows (metadata only):")
print(new_df[new_meta].head(3))

# Check data types
print("\n" + "="*80)
print("DATA TYPES")
print("="*80)

print("\nCANON time-series dtypes (first 5):")
for col in canon_ts_cols[:5]:
    print(f"  {col}: {canon_df[col].dtype}")

print("\nNEW time-series dtypes (first 5):")
for col in new_ts_cols[:5]:
    print(f"  {col}: {new_df[col].dtype}")

print("\n" + "="*80)
print("SCRIPT COMPLETED - Review output to determine next steps")
print("="*80)
