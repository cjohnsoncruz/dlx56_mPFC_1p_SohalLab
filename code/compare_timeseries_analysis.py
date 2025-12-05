"""
Analysis notebook cell to investigate differences between NEW and CANON time-series.
Copy this code into a Jupyter notebook cell and run it.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# ==============================================================================
# LOAD DATA
# ==============================================================================
data_dir = Path(r"C:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\data")
results_dir = Path(r"C:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\results")

canon_path = data_dir / "Dlx56_Normalized Trial Calcium Timeseries_20_Jun_2025.parquet"
new_path = results_dir / "python-made_trial_timeseries_raster_2025-12-04 15.parquet"

print("="*80)
print("LOADING DATA")
print("="*80)
print(f"\nCANON: {canon_path}")
canon_df = pd.read_parquet(canon_path)
print(f"  Shape: {canon_df.shape}")

print(f"\nNEW: {new_path}")
new_df = pd.read_parquet(new_path)
print(f"  Shape: {new_df.shape}")

# ==============================================================================
# IDENTIFY KEY COLUMNS
# ==============================================================================
print("\n" + "="*80)
print("COLUMN STRUCTURE")
print("="*80)

# Get time-series columns
canon_ts_cols = [col for col in canon_df.columns if 's to' in col]
new_ts_cols = [col for col in new_df.columns if col.startswith(('f_', '-f_'))]

print(f"\nCANON time-series cols: {len(canon_ts_cols)}")
print(f"  First 5: {canon_ts_cols[:5]}")
print(f"  Last 5: {canon_ts_cols[-5:]}")

print(f"\nNEW time-series cols: {len(new_ts_cols)}")
print(f"  First 5: {new_ts_cols[:5]}")
print(f"  Last 5: {new_ts_cols[-5:]}")

# Get metadata
canon_meta = [col for col in canon_df.columns if col not in canon_ts_cols]
new_meta = [col for col in new_df.columns if col not in new_ts_cols]

print(f"\nCANON metadata cols: {canon_meta}")
print(f"\nNEW metadata cols: {new_meta}")

# Find stage/phase column
stage_col_canon = [c for c in canon_meta if 'phase' in c.lower() or 'stage' in c.lower()][0]
stage_col_new = [c for c in new_meta if 'phase' in c.lower() or 'stage' in c.lower()][0]

print(f"\nStage column in CANON: '{stage_col_canon}'")
print(f"Stage column in NEW: '{stage_col_new}'")

# Find neuron ID column
neuron_col_canon = [c for c in canon_meta if 'neuron' in c.lower()][0] if any('neuron' in c.lower() for c in canon_meta) else None
neuron_col_new = [c for c in new_meta if 'neuron' in c.lower()][0] if any('neuron' in c.lower() for c in new_meta) else None

print(f"\nNeuron ID column in CANON: '{neuron_col_canon}'")
print(f"Neuron ID column in NEW: '{neuron_col_new}'")

# ==============================================================================
# CALCULATE MEAN ACTIVITY BY TASK STAGE FOR EACH NEURON
# ==============================================================================
print("\n" + "="*80)
print("CALCULATING MEAN ACTIVITY BY TASK STAGE")
print("="*80)

# For CANON - mean across all time-series columns per neuron per stage
canon_mean_by_stage = (canon_df.groupby([neuron_col_canon, stage_col_canon])[canon_ts_cols]
                       .mean()
                       .mean(axis=1)  # Mean across all timepoints
                       .reset_index(name='mean_activity'))

print(f"\nCANON mean activity shape: {canon_mean_by_stage.shape}")
print(f"Sample:\n{canon_mean_by_stage.head(10)}")

# For NEW - mean across all time-series columns per neuron per stage
new_mean_by_stage = (new_df.groupby([neuron_col_new, stage_col_new])[new_ts_cols]
                     .mean()
                     .mean(axis=1)  # Mean across all timepoints
                     .reset_index(name='mean_activity'))

print(f"\nNEW mean activity shape: {new_mean_by_stage.shape}")
print(f"Sample:\n{new_mean_by_stage.head(10)}")

# ==============================================================================
# COMPARE NEURONS AND STAGES
# ==============================================================================
print("\n" + "="*80)
print("COMPARING DATASETS")
print("="*80)

# Check overlap
canon_neurons = set(canon_df[neuron_col_canon].unique())
new_neurons = set(new_df[neuron_col_new].unique())

print(f"\nNeurons in CANON: {len(canon_neurons)}")
print(f"Neurons in NEW: {len(new_neurons)}")
print(f"Overlap: {len(canon_neurons & new_neurons)}")
print(f"Only in CANON: {len(canon_neurons - new_neurons)}")
print(f"Only in NEW: {len(new_neurons - canon_neurons)}")

# Check stages
canon_stages = set(canon_df[stage_col_canon].unique())
new_stages = set(new_df[stage_col_new].unique())

print(f"\nStages in CANON: {sorted(canon_stages)}")
print(f"Stages in NEW: {sorted(new_stages)}")

# ==============================================================================
# MERGE AND COMPARE MEAN ACTIVITIES
# ==============================================================================
print("\n" + "="*80)
print("MERGING AND COMPARING MEAN ACTIVITIES")
print("="*80)

# Rename columns for merging
canon_mean_renamed = canon_mean_by_stage.rename(columns={
    neuron_col_canon: 'neuron_id',
    stage_col_canon: 'task_stage',
    'mean_activity': 'canon_mean'
})

new_mean_renamed = new_mean_by_stage.rename(columns={
    neuron_col_new: 'neuron_id',
    stage_col_new: 'task_stage',
    'mean_activity': 'new_mean'
})

# Merge on neuron and stage
comparison = canon_mean_renamed.merge(
    new_mean_renamed,
    on=['neuron_id', 'task_stage'],
    how='outer',
    indicator=True
)

print(f"\nMerge result shape: {comparison.shape}")
print(f"\nMerge indicator counts:")
print(comparison['_merge'].value_counts())

# Calculate difference
comparison['difference'] = comparison['new_mean'] - comparison['canon_mean']
comparison['abs_difference'] = comparison['difference'].abs()
comparison['pct_difference'] = (comparison['difference'] / comparison['canon_mean']) * 100

# ==============================================================================
# ANALYZE DIFFERENCES
# ==============================================================================
print("\n" + "="*80)
print("DIFFERENCE STATISTICS")
print("="*80)

# Filter to only matching records
matched = comparison[comparison['_merge'] == 'both'].copy()
print(f"\nMatched neuron-stage pairs: {len(matched)}")

print(f"\nDifference statistics:")
print(matched[['difference', 'abs_difference', 'pct_difference']].describe())

# Find cells with largest differences
print(f"\n\nTop 20 neuron-stage pairs with largest absolute differences:")
top_diffs = matched.nlargest(20, 'abs_difference')[
    ['neuron_id', 'task_stage', 'canon_mean', 'new_mean', 'difference', 'pct_difference']
]
print(top_diffs.to_string())

# Cells with any difference
cells_with_diff = matched[matched['abs_difference'] > 1e-10]['neuron_id'].unique()
print(f"\n\nCells with ANY difference (>1e-10): {len(cells_with_diff)}")
print(f"Total unique cells in comparison: {matched['neuron_id'].nunique()}")

# Cells with significant difference (>1% or >0.01 absolute)
cells_with_sig_diff = matched[
    (matched['abs_difference'] > 0.01) | (matched['pct_difference'].abs() > 1)
]['neuron_id'].unique()
print(f"\nCells with SIGNIFICANT difference (>1% or >0.01 abs): {len(cells_with_sig_diff)}")

# By stage analysis
print(f"\n\nDifferences by task stage:")
stage_stats = matched.groupby('task_stage').agg({
    'difference': ['mean', 'std', 'min', 'max'],
    'abs_difference': ['mean', 'max'],
    'neuron_id': 'count'
})
print(stage_stats)

# ==============================================================================
# VISUALIZATION
# ==============================================================================
print("\n" + "="*80)
print("CREATING VISUALIZATIONS")
print("="*80)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Scatter plot: CANON vs NEW
ax = axes[0, 0]
ax.scatter(matched['canon_mean'], matched['new_mean'], alpha=0.3, s=1)
ax.plot([matched['canon_mean'].min(), matched['canon_mean'].max()],
        [matched['canon_mean'].min(), matched['canon_mean'].max()],
        'r--', lw=2, label='y=x')
ax.set_xlabel('CANON Mean Activity')
ax.set_ylabel('NEW Mean Activity')
ax.set_title('CANON vs NEW Mean Activity\n(Each point = one neuron-stage pair)')
ax.legend()
ax.grid(True, alpha=0.3)

# 2. Histogram of differences
ax = axes[0, 1]
ax.hist(matched['difference'], bins=100, edgecolor='black')
ax.set_xlabel('Difference (NEW - CANON)')
ax.set_ylabel('Count')
ax.set_title(f'Distribution of Differences\nMean={matched["difference"].mean():.6f}, Std={matched["difference"].std():.6f}')
ax.axvline(0, color='red', linestyle='--', lw=2)
ax.grid(True, alpha=0.3)

# 3. Absolute difference by stage
ax = axes[1, 0]
stage_groups = matched.groupby('task_stage')['abs_difference']
stage_names = list(stage_groups.groups.keys())
stage_values = [stage_groups.get_group(s).values for s in stage_names]
ax.boxplot(stage_values, labels=stage_names)
ax.set_ylabel('Absolute Difference')
ax.set_xlabel('Task Stage')
ax.set_title('Absolute Difference Distribution by Task Stage')
ax.tick_params(axis='x', rotation=45)
ax.grid(True, alpha=0.3, axis='y')

# 4. Percentage difference distribution
ax = axes[1, 1]
# Filter out infinite and very large values for visualization
pct_diff_filtered = matched['pct_difference'][
    (matched['pct_difference'].abs() < 100) &
    (matched['pct_difference'].notna())
]
ax.hist(pct_diff_filtered, bins=100, edgecolor='black')
ax.set_xlabel('Percentage Difference (%)')
ax.set_ylabel('Count')
ax.set_title(f'Distribution of % Differences\n(Filtered to ±100%)')
ax.axvline(0, color='red', linestyle='--', lw=2)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(results_dir / 'timeseries_comparison.png', dpi=150, bbox_inches='tight')
print(f"\nSaved visualization to: {results_dir / 'timeseries_comparison.png'}")
plt.show()

# Save comparison data
comparison_path = results_dir / 'timeseries_comparison_detailed.parquet'
matched.to_parquet(comparison_path)
print(f"\nSaved detailed comparison to: {comparison_path}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
