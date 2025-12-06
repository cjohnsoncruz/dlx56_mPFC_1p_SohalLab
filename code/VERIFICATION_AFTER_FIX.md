# Verification Code: After Applying Zero-Trial Filtering Fix

Run these cells **after** re-running the preprocessing notebook to verify the fix works.

---

## Setup

```python
import pandas as pd
import numpy as np
from pathlib import Path

# Load datasets
data_dir = Path(r"c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\data")
results_dir = Path(r"c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\results")

canon_path = data_dir / "Dlx56_Normalized Trial Calcium Timeseries_20_Jun_2025.parquet"

# Load NEW dataset - you may need to update this filename if it changed
new_path = results_dir / "python-made_trial_timeseries_raster_2025-12-04 15.parquet"  # UPDATE if needed
# Or use the most recent file
import glob
new_files = glob.glob(str(results_dir / "python-made_trial_timeseries_raster_*.parquet"))
if new_files:
    new_path = max(new_files)  # Get most recent
    print(f"Using NEW file: {Path(new_path).name}")

print("Loading datasets...")
canon_df = pd.read_parquet(canon_path)
new_df = pd.read_parquet(new_path)

# Get time-series columns
canon_ts_cols = [c for c in canon_df.columns if 's to ' in str(c)]
new_ts_cols = [c for c in new_df.columns if 's to ' in str(c)]

print(f"CANON shape: {canon_df.shape}, time-series bins: {len(canon_ts_cols)}")
print(f"NEW shape: {new_df.shape}, time-series bins: {len(new_ts_cols)}")
```

---

## Test 1: Verify Specific Neuron-Stage Matches

Test the neuron-stage combinations that previously showed discrepancies:

```python
test_cases = [
    ('10_3_HET_RS1-1', 'Early_IA_Correct'),
    ('10_3_HET_RS1-1', 'Early_RS_Correct'),
    ('10_3_HET_RS1-1', 'Late_IA'),
]

print("="*80)
print("TEST 1: Verify Previously Mismatched Neuron-Stages Now Match")
print("="*80)

all_match = True

for test_neuron, test_stage in test_cases:
    canon_subset = canon_df[(canon_df['unique_ID'] == test_neuron) &
                            (canon_df['task_phase_vec'] == test_stage)]

    new_subset = new_df[(new_df['neuron_id'] == test_neuron) &
                         (new_df['task_phase_vec'] == test_stage)]

    if len(canon_subset) == 0 or len(new_subset) == 0:
        print(f"\n{test_neuron}, {test_stage}:")
        print(f"  ⚠️ Missing data - CANON: {len(canon_subset)} rows, NEW: {len(new_subset)} rows")
        continue

    canon_mean = canon_subset[canon_ts_cols].mean().mean()
    new_mean = new_subset[new_ts_cols].mean().mean()

    match = np.isclose(canon_mean, new_mean, rtol=1e-5)
    all_match &= match

    symbol = "✓" if match else "✗"
    print(f"\n{test_neuron}, {test_stage}:")
    print(f"  CANON mean: {canon_mean:.6f}")
    print(f"  NEW mean: {new_mean:.6f}")
    print(f"  {symbol} Match: {match}")

    if not match:
        print(f"  Difference: {abs(canon_mean - new_mean):.9f}")

print("\n" + "="*80)
if all_match:
    print("✓✓✓ ALL TEST CASES PASSED ✓✓✓")
else:
    print("⚠️ SOME TEST CASES FAILED - investigate further")
print("="*80)
```

---

## Test 2: Check Trial Counts Match

Verify that NEW now includes the same trials as CANON:

```python
print("\n" + "="*80)
print("TEST 2: Verify Trial Counts Match")
print("="*80)

test_neuron = '10_3_HET_RS1-1'
test_stage = 'Early_IA_Correct'

canon_trials = canon_df[(canon_df['unique_ID'] == test_neuron) &
                        (canon_df['task_phase_vec'] == test_stage)]['trial_num'].unique()

new_trials = new_df[(new_df['neuron_id'] == test_neuron) &
                    (new_df['task_phase_vec'] == test_stage)]['trial_num'].unique()

print(f"\nTest case: {test_neuron}, {test_stage}")
print(f"  CANON trials: {len(canon_trials)}")
print(f"  NEW trials: {len(new_trials)}")

missing_in_new = set(canon_trials) - set(new_trials)
extra_in_new = set(new_trials) - set(canon_trials)

if len(missing_in_new) == 0 and len(extra_in_new) == 0:
    print(f"\n  ✓ Trial counts match perfectly!")
else:
    print(f"\n  ⚠️ Trial count mismatch:")
    if missing_in_new:
        print(f"    Missing from NEW: {sorted(missing_in_new)}")
    if extra_in_new:
        print(f"    Extra in NEW: {sorted(extra_in_new)}")
```

---

## Test 3: Global Comparison

Compare all neurons across all stages to see how many still differ:

```python
print("\n" + "="*80)
print("TEST 3: Global Comparison Across All Neurons")
print("="*80)

# Calculate mean by neuron-stage for CANON
canon_grouped = canon_df.groupby(['unique_ID', 'task_phase_vec'])[canon_ts_cols].mean().mean(axis=1).reset_index()
canon_grouped.columns = ['unique_ID', 'task_phase_vec', 'mean_activity']

# Calculate mean by neuron-stage for NEW
new_grouped = new_df.groupby(['neuron_id', 'task_phase_vec'])[new_ts_cols].mean().mean(axis=1).reset_index()
new_grouped.columns = ['neuron_id', 'task_phase_vec', 'mean_activity']

# Merge
comparison = canon_grouped.merge(new_grouped,
                                  left_on=['unique_ID', 'task_phase_vec'],
                                  right_on=['neuron_id', 'task_phase_vec'],
                                  suffixes=('_canon', '_new'))

# Calculate differences
comparison['diff'] = np.abs(comparison['mean_activity_canon'] - comparison['mean_activity_new'])
comparison['pct_diff'] = comparison['diff'] / (comparison['mean_activity_canon'] + 1e-10) * 100

# Analyze differences
threshold = 1e-5  # Consider values within this as "matching"
matching = comparison[comparison['diff'] < threshold]
differing = comparison[comparison['diff'] >= threshold]

print(f"\nTotal neuron-stage combinations: {len(comparison)}")
print(f"Matching (diff < {threshold}): {len(matching)} ({len(matching)/len(comparison)*100:.1f}%)")
print(f"Differing (diff >= {threshold}): {len(differing)} ({len(differing)/len(comparison)*100:.1f}%)")

if len(differing) > 0:
    print(f"\nTop 10 largest differences:")
    top_diff = differing.nlargest(10, 'diff')[['unique_ID', 'task_phase_vec', 'mean_activity_canon', 'mean_activity_new', 'diff']]
    print(top_diff.to_string())
else:
    print("\n✓ All neuron-stage combinations match!")

# Check specifically for zero-mean cases
canon_zeros = comparison[comparison['mean_activity_canon'] < 1e-6]
print(f"\n{'='*80}")
print(f"Neurons with zero mean activity in CANON: {len(canon_zeros)}")

if len(canon_zeros) > 0:
    canon_zeros['new_is_zero'] = canon_zeros['mean_activity_new'] < 1e-6
    matching_zeros = canon_zeros[canon_zeros['new_is_zero']]
    non_matching_zeros = canon_zeros[~canon_zeros['new_is_zero']]

    print(f"  NEW also has zero mean: {len(matching_zeros)} ({len(matching_zeros)/len(canon_zeros)*100:.1f}%)")
    print(f"  NEW has non-zero mean: {len(non_matching_zeros)} ({len(non_matching_zeros)/len(canon_zeros)*100:.1f}%)")

    if len(matching_zeros) == len(canon_zeros):
        print(f"\n  ✓✓✓ ALL zero-mean cases now match! ✓✓✓")
    elif len(non_matching_zeros) > 0:
        print(f"\n  ⚠️ Some zero-mean cases still don't match:")
        print(non_matching_zeros[['unique_ID', 'task_phase_vec', 'mean_activity_canon', 'mean_activity_new']].head(10).to_string())
```

---

## Test 4: Verify Zero-Max Trials Are Included

Check that trials with max_trial_val == 0 are now present in the NEW dataset:

```python
print("\n" + "="*80)
print("TEST 4: Verify Zero-Max Trials Are Included")
print("="*80)

# Check if max_trial_val column exists in NEW
if 'max_trial_val' in new_df.columns:
    zero_max_trials = new_df[new_df['max_trial_val'] == 0]
    print(f"\nTrials with max_trial_val == 0 in NEW: {len(zero_max_trials)}")

    if len(zero_max_trials) > 0:
        print(f"  ✓ Zero-max trials are present (expected)")
        print(f"\nSample of zero-max trials:")
        sample = zero_max_trials[['neuron_id', 'task_phase_vec', 'trial_num', 'max_trial_val']].head(5)
        print(sample.to_string())

        # Check that time-series values are 0
        ts_vals = zero_max_trials.iloc[0][new_ts_cols].values
        all_zeros = np.allclose(ts_vals, 0.0)
        print(f"\n  Time-series values are all 0: {all_zeros}")
        if all_zeros:
            print(f"    ✓ Correct - normalized values are 0 when max=0")
        else:
            print(f"    ⚠️ Unexpected - some values are non-zero")
    else:
        print(f"  ⚠️ No zero-max trials found - this might indicate the fix didn't work")
else:
    print(f"\n  ⚠️ 'max_trial_val' column not found in NEW dataset")
    print(f"     Available columns: {list(new_df.columns[:20])}...")
```

---

## Summary

```python
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print("\nFix Implementation:")
print("  - Modified helper_functions.py:501-575")
print("  - Added filter_zero_max parameter (default=False)")
print("  - Default behavior now matches MATLAB")

print("\nExpected Results:")
print("  ✓ Test 1: Previously mismatched cases should now match")
print("  ✓ Test 2: Trial counts should match between CANON and NEW")
print("  ✓ Test 3: >95% of neuron-stage combinations should match")
print("  ✓ Test 4: Zero-max trials should be present in NEW")

print("\nIf all tests pass:")
print("  → Fix successfully resolves CANON vs NEW differences")
print("  → Python pipeline now matches MATLAB behavior")

print("\nIf some tests fail:")
print("  → Check that you re-ran the full preprocessing notebook")
print("  → Verify NEW dataset is the one generated after the fix")
print("  → Investigate remaining differences with diagnostic cells")

print("="*80)
```

---

## Additional Diagnostics (If Needed)

If tests reveal ongoing issues, use these diagnostic cells:

### Check Function Call

```python
# Verify the function is being called with correct parameters
print("Checking helper_functions.py implementation...")

import helper_functions
import inspect

sig = inspect.signature(helper_functions.run_min_max_norm_on_timeseries)
print(f"\nFunction signature:")
print(f"  {sig}")

params = sig.parameters
if 'filter_zero_max' in params:
    default = params['filter_zero_max'].default
    print(f"\n✓ filter_zero_max parameter exists")
    print(f"  Default value: {default}")
    if default == False:
        print(f"  ✓ Default is False (MATLAB-matching)")
    else:
        print(f"  ⚠️ Default is {default}, should be False")
else:
    print(f"\n✗ filter_zero_max parameter NOT found")
    print(f"  Available parameters: {list(params.keys())}")
```

### Check Preprocessing Config

```python
# Verify preprocessing notebook used the updated function
print("\nChecking preprocessing configuration...")

# This requires looking at what actually ran in the notebook
# You may need to add debug prints in the notebook cell where normalization happens

print("\nAdd this to your preprocessing notebook before normalization:")
print("```python")
print("# Debug: Check function signature")
print("import inspect")
print("sig = inspect.signature(run_min_max_norm_on_timeseries)")
print("print(f'Function signature: {sig}')")
print("```")
```

---

## Next Steps

1. **Run all verification tests above**
2. **If tests pass**: The fix is complete and working! Document findings in your summary.
3. **If tests fail**:
   - Verify you re-ran the full preprocessing notebook
   - Check that the NEW dataset file is the one generated after the fix
   - Use additional diagnostics to identify remaining issues
   - Review [FIX_ZERO_TRIAL_FILTERING.md](c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\code\FIX_ZERO_TRIAL_FILTERING.md) for implementation details
