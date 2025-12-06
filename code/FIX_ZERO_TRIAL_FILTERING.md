# Fix: Zero-Trial Filtering to Match MATLAB Behavior

## Problem

NEW time-series showed non-zero mean activity for neuron-stage combinations where CANON showed zero activity:
- Neuron `10_3_HET_RS1-1`, `Early_IA_Correct`: CANON=0.000000, NEW=0.009028
- Neuron `10_3_HET_RS1-1`, `Early_RS_Correct`: CANON=0.000000, NEW=0.034259

## Root Cause

**Python filtered out trials with zero max activity, MATLAB did not.**

In `helper_functions.py:512-513`, the code filtered rows where `max_trial_val == 0` OR `NULL`:
```python
section_mask = (~normed_ts_df[max_val_col_name].isnull()) & (normed_ts_df[max_val_col_name] > 0)
```

This meant:
- **CANON (MATLAB)**: Includes zero-activity trials → mean_activity can be 0.0
- **NEW (Python OLD)**: Excludes zero-activity trials → mean_activity only over non-zero trials → small non-zero values

---

## Solution Implemented: Option B (Parameter-Based)

Modified [`helper_functions.py:501-575`](c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\code\Function .py Storage\helper_functions.py#L501-L575) to add a `filter_zero_max` parameter:

### New Function Signature

```python
def run_min_max_norm_on_timeseries(run_norm, timeseries_df, name_unitID_list,
                                   numeric_col, max_val_col_name,
                                   filter_zero_max=False):  # NEW PARAMETER
```

### Parameter Behavior

- **`filter_zero_max=False` (default, MATLAB-matching)**:
  - Keeps trials with `max_trial_val == 0`
  - Sets normalized values to 0.0 for these trials
  - Mean calculations include zero trials
  - **This is now the default behavior**

- **`filter_zero_max=True` (OLD behavior)**:
  - Filters out trials with `max_trial_val == 0`
  - Only non-zero trials contribute to mean
  - Use this if you need backward compatibility with OLD pipeline

### Division by Zero Handling

When `max_trial_val == 0`, the code now:
1. Sets all time-series values to 0.0 (no division)
2. For non-zero max values, normalizes normally: `activity / max_val`

```python
zero_max_mask = normed_ts_df[max_val_col_name] == 0
if zero_max_mask.any():
    # For trials with max=0, set all time-series values to 0
    normed_ts_df.loc[zero_max_mask, numeric_col] = 0.0
    # For trials with max>0, normalize normally
    nonzero_mask = ~zero_max_mask
    if nonzero_mask.any():
        normed_ts_df.loc[nonzero_mask, numeric_col] = (
            normed_ts_df.loc[nonzero_mask, numeric_col].values /
            normed_ts_df.loc[nonzero_mask, max_val_col_name].values[:,np.newaxis]
        )
```

---

## Usage

### Automatic (No Changes Required)

Your existing code in [`preprocess matlab data v6_modular.ipynb:769`](c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\code\preprocess matlab data v6_modular.ipynb#L769):

```python
trial_tseries_df_norm = run_min_max_norm_on_timeseries(
    use_min_max_norm, trial_tseries_df_raw,
    [name_col, neuron_id_col], numeric_col, 'max_trial_val'
)
```

**This call now automatically uses MATLAB-matching behavior** (`filter_zero_max=False` is the default).

### Explicit (If You Want to Control Behavior)

If you want to explicitly control the behavior:

```python
# MATLAB-matching (NEW default):
trial_tseries_df_norm = run_min_max_norm_on_timeseries(
    use_min_max_norm, trial_tseries_df_raw,
    [name_col, neuron_id_col], numeric_col, 'max_trial_val',
    filter_zero_max=False  # Keep zero-max trials
)

# OLD Python behavior (filters zeros):
trial_tseries_df_norm = run_min_max_norm_on_timeseries(
    use_min_max_norm, trial_tseries_df_raw,
    [name_col, neuron_id_col], numeric_col, 'max_trial_val',
    filter_zero_max=True  # Filter out zero-max trials
)
```

---

## Expected Outcome

After re-running the preprocessing notebook with this fix:

1. **Zero means will now appear in NEW dataset** (matching CANON)
   - Neuron-stage combinations with all-zero trials will show mean_activity = 0.0

2. **Trial counts will match MATLAB**
   - Both CANON and NEW will include the same trials

3. **Mean activity will match for zero-activity cases**
   - Where CANON has mean=0.0, NEW should now also have mean=0.0

---

## Verification Steps

### Step 1: Re-run Preprocessing

Run the [preprocess matlab data v6_modular.ipynb](c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\code\preprocess matlab data v6_modular.ipynb) notebook to generate new time-series with the fix.

### Step 2: Run Diagnostics

Use the diagnostic cells from [DIAGNOSTIC_NOTEBOOK_CELLS.md](c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\code\DIAGNOSTIC_NOTEBOOK_CELLS.md) to verify:

```python
# Test neuron with previously different means
test_neuron = '10_3_HET_RS1-1'
test_stage = 'Early_IA_Correct'

# Check if means now match
canon_mean = canon_df[(canon_df['unique_ID'] == test_neuron) &
                       (canon_df['task_phase_vec'] == test_stage)][canon_ts_cols].mean().mean()

new_mean = new_df[(new_df['neuron_id'] == test_neuron) &
                   (new_df['task_phase_vec'] == test_stage)][new_ts_cols].mean().mean()

print(f"CANON mean: {canon_mean:.6f}")
print(f"NEW mean: {new_mean:.6f}")
print(f"Match: {np.isclose(canon_mean, new_mean)}")
```

### Step 3: Compare All Neurons

Run the full comparison to check how many cells still differ:

```python
# Your existing comparison code
# Should now show significantly fewer (or zero) neurons with differences
```

---

## Files Modified

1. **[helper_functions.py:501-575](c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\code\Function .py Storage\helper_functions.py#L501-L575)**
   - Added `filter_zero_max` parameter (default=False)
   - Added division-by-zero handling
   - Added comprehensive docstring

2. **No changes needed to calling code** (backward compatible)
   - [preprocess matlab data v6_modular.ipynb:769](c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\code\preprocess matlab data v6_modular.ipynb#L769)
   - [preprocess_data.py:91](c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\code\Function .py Storage\preprocess_data.py#L91)

---

## Notes

- **Backward compatible**: Default behavior now matches MATLAB
- **Safe**: Explicit handling of division by zero
- **Flexible**: Can restore OLD behavior with `filter_zero_max=True` if needed
- **Well-documented**: Clear parameter docstring explains both behaviors

---

## Related Investigation Files

- [FINDINGS_SUMMARY.md](c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\code\FINDINGS_SUMMARY.md) - Complete investigation summary
- [DIAGNOSTIC_NOTEBOOK_CELLS.md](c:\Users\13car\Dropbox\local_github_repos_personal\dlx56_mPFC_1p_SohalLab\code\DIAGNOSTIC_NOTEBOOK_CELLS.md) - Diagnostic code to verify fix
- [Investigation Plan](C:\Users\13car\.claude\plans\golden-gathering-dream.md) - Detailed hypothesis and solution design
