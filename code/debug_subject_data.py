"""
Diagnostic script to check for NaN/inf values in subject shuffle data
Run this to identify the source of the numpy percentile warning
"""
import pandas as pd
import numpy as np

def diagnose_subject_data(subject_name, shuffle_df, raster_df):
    """
    Check for NaN/inf values in shuffle and raster data for a specific subject

    Parameters:
    -----------
    subject_name : str
        Name of subject to check
    shuffle_df : pd.DataFrame
        Shuffled mean activity DataFrame for this subject
    raster_df : pd.DataFrame
        Raster DataFrame for this subject
    """
    print(f"\n{'='*60}")
    print(f"DIAGNOSTIC REPORT FOR: {subject_name}")
    print(f"{'='*60}\n")

    # Get cell columns
    cell_cols = [c for c in shuffle_df.columns if c.startswith('cell_')]

    # Check shuffle data
    print("=== SHUFFLE DATA ===")
    print(f"Shape: {shuffle_df.shape}")
    print(f"\nColumns: {list(shuffle_df.columns)}")

    # Check if expected columns exist
    if 'shuffle_seed' in shuffle_df.columns:
        print(f"Number of unique seeds: {shuffle_df['shuffle_seed'].nunique()}")
    else:
        print("⚠️  WARNING: 'shuffle_seed' column not found")

    if 'task_stage' in shuffle_df.columns:
        print(f"Task stages: {shuffle_df['task_stage'].unique()}")
    else:
        print("⚠️  WARNING: 'task_stage' column not found")

    # Check for NaN values in cell data
    nan_counts = shuffle_df[cell_cols].isna().sum()
    if nan_counts.sum() > 0:
        print(f"\n⚠️  WARNING: Found {nan_counts.sum()} NaN values across cells")
        print("Cells with NaN values:")
        for cell, count in nan_counts[nan_counts > 0].items():
            print(f"  {cell}: {count} NaN values ({count/len(shuffle_df)*100:.2f}%)")
    else:
        print("✓ No NaN values in shuffle data")

    # Check for inf values
    inf_counts = shuffle_df[cell_cols].apply(lambda x: np.isinf(x).sum())
    if inf_counts.sum() > 0:
        print(f"\n⚠️  WARNING: Found {inf_counts.sum()} inf values across cells")
        print("Cells with inf values:")
        for cell, count in inf_counts[inf_counts > 0].items():
            print(f"  {cell}: {count} inf values")
    else:
        print("✓ No inf values in shuffle data")

    # Check by task_stage
    if 'task_stage' in shuffle_df.columns:
        print("\n=== NaN/INF BY TASK STAGE ===")
        for stage in shuffle_df['task_stage'].unique():
            stage_data = shuffle_df[shuffle_df['task_stage'] == stage]
            nan_count = stage_data[cell_cols].isna().sum().sum()
            inf_count = stage_data[cell_cols].apply(lambda x: np.isinf(x).sum()).sum()
            print(f"{stage}: {nan_count} NaNs, {inf_count} infs (n={len(stage_data)} rows)")
    else:
        print("\n⚠️  Skipping task_stage analysis (column not found)")

    # Check raster data
    print("\n=== RASTER DATA ===")
    print(f"Shape: {raster_df.shape}")
    raster_cell_cols = [c for c in raster_df.columns if 'cell' in c]

    nan_counts_raster = raster_df[raster_cell_cols].isna().sum()
    if nan_counts_raster.sum() > 0:
        print(f"\n⚠️  WARNING: Found {nan_counts_raster.sum()} NaN values in raster data")
        print("Top 10 cells with most NaNs:")
        print(nan_counts_raster.nlargest(10))
    else:
        print("✓ No NaN values in raster data")

    # Check for all-NaN cells in any task_stage
    print("\n=== CHECKING FOR PROBLEMATIC CELLS ===")
    problematic_cells = []
    if 'task_stage' in shuffle_df.columns:
        for stage in shuffle_df['task_stage'].unique():
            stage_data = shuffle_df[shuffle_df['task_stage'] == stage][cell_cols]
            all_nan_cells = [col for col in cell_cols if stage_data[col].isna().all()]
            if all_nan_cells:
                print(f"Stage '{stage}': {len(all_nan_cells)} cells with ALL NaN values")
                problematic_cells.extend([(stage, cell) for cell in all_nan_cells])

        if not problematic_cells:
            print("✓ No cells with all-NaN values in any stage")
    else:
        # Check for all-NaN cells overall
        all_nan_cells = [col for col in cell_cols if shuffle_df[col].isna().all()]
        if all_nan_cells:
            print(f"Found {len(all_nan_cells)} cells with ALL NaN values")
            print(f"First 10: {all_nan_cells[:10]}")
        else:
            print("✓ No cells with all-NaN values")

    # Summary statistics
    print("\n=== SUMMARY STATISTICS (first 5 cells) ===")
    print(shuffle_df[cell_cols[:5]].describe())

    return shuffle_df, nan_counts, inf_counts


# Example usage in your notebook:
# For the problematic subject:
# shuffle_df_problem = all_subject_shuffles['13_3_HET_RS1']
# raster_df_problem = raster_dataframes['13_3_HET_RS1']
# diagnose_subject_data('13_3_HET_RS1', shuffle_df_problem, raster_df_problem)
