"""
Diagnostic script to investigate why CANON has zero mean activity
where NEW has non-zero values.

Hypothesis: Python filters out trials with max_trial_val == 0, MATLAB doesn't.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
data_dir = Path(r"c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\data")
results_dir = Path(r"c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\results")

# Load datasets
print("Loading datasets...")
canon_path = data_dir / "Dlx56_Normalized Trial Calcium Timeseries_20_Jun_2025.parquet"
new_path = results_dir / "python-made_trial_timeseries_raster_2025-12-04 15.parquet"

canon_df = pd.read_parquet(canon_path)
new_df = pd.read_parquet(new_path)

# Get time-series columns
canon_ts_cols = [c for c in canon_df.columns if 's to ' in str(c)]
new_ts_cols = [c for c in new_df.columns if 's to ' in str(c)]

print(f"CANON shape: {canon_df.shape}")
print(f"NEW shape: {new_df.shape}")
print(f"CANON time-series bins: {len(canon_ts_cols)}")
print(f"NEW time-series bins: {len(new_ts_cols)}")

# Test neuron and stage
test_neuron = '10_3_HET_RS1-1'
test_stage = 'Early_IA_Correct'

print(f"\n{'='*80}")
print(f"DIAGNOSTIC: Investigating {test_neuron} in {test_stage}")
print(f"{'='*80}")

# ============================================================================
# STEP 1: Verify Trial Count Differences
# ============================================================================
print(f"\n{'='*80}")
print("STEP 1: Verify Trial Count Differences")
print(f"{'='*80}")

canon_trials = canon_df[(canon_df['unique_ID'] == test_neuron) &
                        (canon_df['task_phase_vec'] == test_stage)]['trial_num'].unique()

new_trials = new_df[(new_df['neuron_id'] == test_neuron) &
                    (new_df['task_phase_vec'] == test_stage)]['trial_num'].unique()

print(f"\nCANON trials: {len(canon_trials)} trials")
print(f"  Trial numbers: {sorted(canon_trials)}")
print(f"\nNEW trials: {len(new_trials)} trials")
print(f"  Trial numbers: {sorted(new_trials)}")

missing_in_new = set(canon_trials) - set(new_trials)
extra_in_new = set(new_trials) - set(canon_trials)

print(f"\nTrials in CANON but not NEW: {sorted(missing_in_new) if missing_in_new else 'None'}")
print(f"Trials in NEW but not CANON: {sorted(extra_in_new) if extra_in_new else 'None'}")

if len(missing_in_new) == 0:
    print("\n⚠️ UNEXPECTED: No trials are missing from NEW")
    print("   Hypothesis may be incorrect - both datasets have same trials")
else:
    print(f"\n✓ Expected: NEW has {len(missing_in_new)} fewer trial(s)")

# ============================================================================
# STEP 2: Check Individual Trial Activity
# ============================================================================
print(f"\n{'='*80}")
print("STEP 2: Check Individual Trial Activity")
print(f"{'='*80}")

if len(missing_in_new) > 0:
    print(f"\nChecking {len(missing_in_new)} missing trial(s)...")

    for trial in sorted(missing_in_new):
        canon_row = canon_df[(canon_df['unique_ID'] == test_neuron) &
                              (canon_df['task_phase_vec'] == test_stage) &
                              (canon_df['trial_num'] == trial)]

        if len(canon_row) == 0:
            print(f"\nTrial {trial}: NOT FOUND in CANON (unexpected)")
            continue

        # Get time-series values
        trial_vals = canon_row[canon_ts_cols].values[0]

        print(f"\nTrial {trial}:")
        print(f"  Mean: {trial_vals.mean():.6f}")
        print(f"  Max: {trial_vals.max():.6f}")
        print(f"  Non-zero bins: {(trial_vals > 0).sum()}/{len(trial_vals)}")

        if trial_vals.max() == 0:
            print(f"  ✓ This trial has max=0 (explains why it was filtered)")
        else:
            print(f"  ⚠️ This trial has max>0 (does NOT explain filtering)")
else:
    print("\nSkipping Step 2 - no missing trials to analyze")

# ============================================================================
# STEP 3: Verify Filtering Code Path
# ============================================================================
print(f"\n{'='*80}")
print("STEP 3: Verify Filtering Code Path")
print(f"{'='*80}")

print("\nNOTE: This step requires adding debug output to the preprocessing notebook.")
print("      Add this line before normalization:")
print("      trial_tseries_df_raw.to_csv('before_norm.csv')")
print("\nSkipping automated check - manual inspection required.")

# ============================================================================
# STEP 4: Recalculate Mean Without Filtering
# ============================================================================
print(f"\n{'='*80}")
print("STEP 4: Recalculate Mean Without Filtering")
print(f"{'='*80}")

# Get all trials from CANON for this neuron-stage
canon_subset = canon_df[(canon_df['unique_ID'] == test_neuron) &
                        (canon_df['task_phase_vec'] == test_stage)]

print(f"\nCANON subset: {len(canon_subset)} rows")

# Calculate mean across all trials (including zeros)
all_trials_mean = canon_subset[canon_ts_cols].mean().mean()
print(f"\nMean including ALL trials: {all_trials_mean:.6f}")

# Filter to non-zero trials only (max across bins > 0)
trial_max = canon_subset[canon_ts_cols].max(axis=1)
non_zero_trials = canon_subset[trial_max > 0]
print(f"\nTrials with max > 0: {len(non_zero_trials)}/{len(canon_subset)}")

if len(non_zero_trials) > 0:
    non_zero_mean = non_zero_trials[canon_ts_cols].mean().mean()
    print(f"Mean excluding zero-max trials: {non_zero_mean:.6f}")
else:
    non_zero_mean = np.nan
    print(f"Mean excluding zero-max trials: N/A (no non-zero trials)")

# Compare to NEW
new_subset = new_df[(new_df['neuron_id'] == test_neuron) &
                     (new_df['task_phase_vec'] == test_stage)]

if len(new_subset) > 0:
    new_mean = new_subset[new_ts_cols].mean().mean()
    print(f"NEW mean: {new_mean:.6f}")

    # Test hypothesis
    if not np.isnan(non_zero_mean):
        is_close = np.isclose(non_zero_mean, new_mean, rtol=1e-5)
        print(f"\n{'✓' if is_close else '✗'} Does non_zero_mean ≈ NEW mean? {is_close}")
        print(f"   Difference: {abs(non_zero_mean - new_mean):.9f}")

        if is_close:
            print("\n✓ HYPOTHESIS CONFIRMED:")
            print("   Filtering zero-max trials explains the difference!")
        else:
            print("\n⚠️ HYPOTHESIS UNCLEAR:")
            print("   There may be additional differences beyond zero-trial filtering")
    else:
        print("\n⚠️ Cannot test hypothesis - no non-zero trials in CANON")
else:
    print(f"NEW mean: N/A (no rows found)")

# ============================================================================
# STEP 5: Check MATLAB Source CSV
# ============================================================================
print(f"\n{'='*80}")
print("STEP 5: Check MATLAB Source Data")
print(f"{'='*80}")

# Try to find MATLAB CSV
matlab_csv_candidates = [
    data_dir / "matlab_output.csv",
    data_dir / "section_activity_timeseries.csv",
    data_dir / "Dlx56_Trial_Calcium_Timeseries.csv",
]

matlab_csv_path = None
for path in matlab_csv_candidates:
    if path.exists():
        matlab_csv_path = path
        break

if matlab_csv_path:
    print(f"\nFound MATLAB CSV: {matlab_csv_path}")

    # Load and check
    matlab_csv = pd.read_csv(matlab_csv_path)
    print(f"MATLAB CSV shape: {matlab_csv.shape}")
    print(f"MATLAB CSV columns: {list(matlab_csv.columns[:10])}...")

    # Try to find matching neuron
    # MATLAB uses 'name' like '10_3_HET_RS1' and 'neuron_ID' starting from 1
    neuron_name = test_neuron.rsplit('-', 1)[0]  # '10_3_HET_RS1'
    neuron_id = int(test_neuron.rsplit('-', 1)[1])  # 1

    print(f"\nLooking for: name='{neuron_name}', neuron_ID={neuron_id}, stage='{test_stage}'")

    if 'name' in matlab_csv.columns and 'neuron_ID' in matlab_csv.columns:
        matlab_subset = matlab_csv[(matlab_csv['name'] == neuron_name) &
                                    (matlab_csv['neuron_ID'] == neuron_id) &
                                    (matlab_csv['task_phase_vec'] == test_stage)]

        if len(matlab_subset) > 0:
            print(f"\nMATLAB CSV trials: {len(matlab_subset)} trials")
            trial_nums = sorted(matlab_subset['trial_num'].unique())
            print(f"Trial numbers: {trial_nums}")

            # Check if any have all zeros
            frame_cols = [c for c in matlab_csv.columns if c.startswith(('f_', '-f_'))]
            print(f"\nChecking max values for each trial...")

            for trial in trial_nums:
                trial_data = matlab_subset[matlab_subset['trial_num'] == trial]
                max_val = trial_data[frame_cols].max().max()
                print(f"  Trial {trial}: max = {max_val:.6f}")

                if max_val == 0:
                    print(f"    ✓ This trial has max=0 in MATLAB CSV")
        else:
            print(f"\n⚠️ No matching rows found in MATLAB CSV")
    else:
        print("\n⚠️ MATLAB CSV doesn't have expected columns (name, neuron_ID)")
else:
    print("\n⚠️ Could not find MATLAB source CSV")
    print("   Checked paths:")
    for path in matlab_csv_candidates:
        print(f"   - {path}")

# ============================================================================
# SUMMARY
# ============================================================================
print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")

print(f"\nTest neuron: {test_neuron}")
print(f"Test stage: {test_stage}")
print(f"\nCANON mean: {all_trials_mean:.6f}")
if len(new_subset) > 0:
    print(f"NEW mean: {new_mean:.6f}")
    print(f"Difference: {abs(all_trials_mean - new_mean):.6f}")
else:
    print(f"NEW mean: N/A")

print(f"\nTrials in CANON: {len(canon_trials)}")
print(f"Trials in NEW: {len(new_trials)}")
print(f"Missing from NEW: {len(missing_in_new)}")

if len(missing_in_new) > 0 and len(non_zero_trials) < len(canon_subset):
    print("\n✓ Evidence supports hypothesis:")
    print("  - NEW has fewer trials than CANON")
    print("  - Missing trials have zero max activity")
    print("  - Mean excluding zero trials matches NEW mean")
    print("\nConclusion: Python filters zero-max trials, MATLAB doesn't")
else:
    print("\n⚠️ Hypothesis needs more investigation")

print(f"\n{'='*80}")
