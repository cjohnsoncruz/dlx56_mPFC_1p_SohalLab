# Investigation: NEW vs CANON Time-Series Differences

## Files Being Compared

**CANON (MATLAB-generated):**
- Path: `data/Dlx56_Normalized Trial Calcium Timeseries_20_Jun_2025.parquet`
- Source: Created in MATLAB, then converted to parquet
- Used in published paper

**NEW (Python-generated):**
- Path: `results/python-made_trial_timeseries_raster_2025-12-04 15.parquet`
- Source: Created via Python pipeline in [preprocess matlab data v6_modular.ipynb](preprocess matlab data v6_modular.ipynb)
- Created from: `raster` data type with `normalize='none'` initially

## Python Pipeline Overview

The NEW file is created through this pipeline:

1. **Load MATLAB objects** → `loaded_objects`
2. **Transform to DataFrames** ([preprocessing_utils.py:100-108](preprocessing_utils.py#L100-L108))
   ```python
   raster_dataframes = transform_all_datasets(loaded_objects, config, analysis_config,
                                               datatype='raster', normalize='none')
   ```
   - Calls `dataset_obj_to_df()` for each subject
   - Applies Gaussian smoothing if `datatype='dff'` (NOT applied for raster)
   - Adds task stage info
   - Truncates post-outcome to 15 seconds
   - Optionally drops inactive cells

3. **Create trial time-series** ([preprocessing_utils.py:255-291](preprocessing_utils.py#L255-L291))
   ```python
   create_subject_trial_tseries_df(input_df, ens_matrix, ...)
   ```
   - Extracts trial windows (pre/post outcome frames)
   - Pivots to wide format (one row per trial-cell)
   - **Bins time-series** with `window_to_bin=5` frames
   - **Rotates bins** by `n_sec_to_rotate` seconds

4. **Normalize** (in notebook around line 4116)
   ```python
   trial_tseries_df_norm = run_min_max_norm_on_timeseries(...)
   ```
   - Calculates max activity value per neuron across all trials
   - Normalizes each neuron's time-series by dividing by its max value
   - **CRITICAL:** Filters out neurons with max_trial_val = 0 or NaN

5. **Drop bins** (lines 4127-4128)
   - Drops N bins from start (`n_start_timebins_to_drop`)
   - Drops M bins from end (`n_end_timebins_to_drop`)

6. **Save** → `trial_tseries_df_norm.to_parquet(save_name)`

## Potential Sources of Differences

### 1. **Inactive Cell Filtering**
- **Location:** [preprocessing_utils.py:74-80](preprocessing_utils.py#L74-L80)
- **Logic:** Drops cells with 0 activity in `post_outcome` section
- **Impact:** If MATLAB and Python use different thresholds or time windows for determining "inactive", different cells may be dropped
- **Check:**
  ```python
  # Compare neuron lists
  canon_neurons = set(canon_df['neuron_id'].unique())
  new_neurons = set(new_df['neuron_id'].unique())
  print(f"Only in CANON: {canon_neurons - new_neurons}")
  print(f"Only in NEW: {new_neurons - canon_neurons}")
  ```

### 2. **Post-Outcome Truncation**
- **Location:** [preprocessing_utils.py:71](preprocessing_utils.py#L71)
- **Function:** `truncate_post_outcome_to_15s(raster_df, truncate_post=True)`
- **Impact:** If MATLAB uses different truncation logic, the time windows might differ
- **Result:** Different frames included in mean calculation

### 3. **Trial Window Extraction**
- **Location:** [preprocessing_utils.py:164-207](preprocessing_utils.py#L164-L207)
- **Default:** `pre_frames=60`, `post_frames=300`
- **Impact:** If MATLAB uses different window sizes, different data is included
- **Padding:** Python pads truncated trials with NaN, which are excluded from mean calculations
- **Result:** Trials cut short will have different mean values

### 4. **Binning and Rotation**
- **Location:** Function `bin_rotate_timeseries()` in `preprocess_data.py`
- **Default:** `window_size=5` frames (0.25s at 20Hz), `rotate_by=3` seconds
- **Binning:** Averages activity within each 5-frame window
- **Rotation:** Shifts time-series columns rightward by 3 seconds
- **Impact:** Even small differences in implementation can cause numerical differences
- **Critical Question:** Does MATLAB use exact same binning window sizes and rotation offset?

### 5. **Min-Max Normalization**
- **Location:** [helper_functions.py:501-519](Function .py Storage/helper_functions.py#L501-L519)
- **Method:**
  ```python
  max_val = max(activity across all trials for this neuron)
  normalized_activity = activity / max_val
  ```
- **Filtering:** Removes neurons where `max_val == 0` or `max_val is NaN`
- **Impact:**
  - If MATLAB computes max differently (e.g., over different time windows), normalization differs
  - If MATLAB includes/excludes certain trials in max calculation, results differ
- **Result:** All time-series values for affected neurons will be different

### 6. **Frame Indexing and Alignment**
- **Python convention:** Pre-outcome frames = `-f_60` to `-f_1`, Post-outcome = `f_1` to `f_300`
- **MATLAB convention:** Unknown - may use different indexing
- **Impact:** If outcome frame is defined differently, all alignment shifts

### 7. **Task Stage Assignment**
- **Function:** `add_task_stage_to_raster_df()` in `matlab_obj_to_python.py`
- **Impact:** If stage boundaries are defined differently, trials get different stage labels
- **Result:** Mean activity "by stage" will differ because different trials are grouped together

## Recommended Investigation Steps

### Step 1: Run Comparison Analysis
Run the script I created:
```bash
python code/compare_timeseries_analysis.py
```

This will:
- Load both files
- Calculate mean activity by neuron and task stage
- Identify which neurons/stages have differences
- Generate visualizations
- Save detailed comparison

### Step 2: Check Neuron Lists
Compare which neurons are present in each file:
```python
canon_neurons = set(canon_df['neuron_id'].unique())
new_neurons = set(new_df['neuron_id'].unique())
missing_from_new = canon_neurons - new_neurons
extra_in_new = new_neurons - canon_neurons
```

**If neurons differ:**
- Check `drop_inactive_cells` parameter
- Check post-outcome truncation logic
- Verify max normalization filtering

### Step 3: Check Trial Counts
For shared neurons, check if they have same number of trials:
```python
canon_trial_counts = canon_df.groupby('neuron_id')['trial_num'].nunique()
new_trial_counts = new_df.groupby('neuron_id')['trial_num'].nunique()
diff = canon_trial_counts - new_trial_counts
neurons_with_diff_trials = diff[diff != 0]
```

**If trial counts differ:**
- Check trial detection logic
- Check task stage filtering
- Verify truncation doesn't drop entire trials

### Step 4: Check Raw Values (Before Normalization)
If possible, compare values before min-max normalization:
```python
# Check if max_trial_val column exists in files
# Compare max values used for normalization
```

### Step 5: Check Time-Series Column Structure
```python
# CANON uses: '0.0s to 0.25s', '0.25s to 0.5s', etc.
# NEW uses: 'f_1', 'f_2', etc.
# Verify they correspond to same time windows
```

### Step 6: Validate Binning and Rotation
- Check if MATLAB code uses same `window_size=5` and `rotate_by=3`
- Verify binning is mean (not sum or max)
- Confirm rotation direction and offset calculation

## Expected Findings

### Small Differences (Expected, Acceptable)
- **Floating-point precision:** Differences < 1e-10 due to rounding
- **Numerical order:** Different computation order can cause tiny differences
- **NaN handling:** Python and MATLAB may handle NaN slightly differently

### Medium Differences (Concerning, Investigate)
- **Binning edge effects:** If bin boundaries differ by 1 frame
- **Normalization:** If max is computed over slightly different sets of trials
- **Padding:** If truncated trials are handled differently

### Large Differences (Critical, Must Resolve)
- **Different neurons:** Missing/extra neurons indicate filtering issues
- **Different task stages:** Stage assignment logic differs
- **Wrong time windows:** Pre/post frames extracted incorrectly
- **Incorrect normalization:** Max values computed completely differently

## Resolution Checklist

- [ ] Run comparison analysis script
- [ ] Identify magnitude of differences (small/medium/large)
- [ ] Check if same neurons are present in both files
- [ ] Verify trial counts match for shared neurons
- [ ] Compare time-series column structures
- [ ] Review MATLAB code for binning/rotation parameters
- [ ] Check normalization max value calculation
- [ ] Verify task stage assignment logic
- [ ] Document any intentional differences
- [ ] Update code if unintentional differences found

## Key Questions to Answer

1. **Are the same neurons present in both files?**
   - If not, why? Different drop_inactive_cells logic?

2. **Do shared neurons have the same number of trials?**
   - If not, why? Different trial detection or filtering?

3. **What is the distribution of differences?**
   - All neurons slightly different? Only some neurons very different?

4. **Do differences correlate with any feature?**
   - Specific subjects? Specific task stages? Low-activity neurons?

5. **Are MATLAB and Python using identical preprocessing parameters?**
   - Same window sizes, rotation offsets, normalization methods?

## Files to Review

- [preprocessing_utils.py](preprocessing_utils.py) - Main preprocessing functions
- `matlab_obj_to_python.py` - MATLAB import and conversion
- `preprocess_data.py` - Binning and rotation functions
- `helper_functions.py` - Normalization functions
- MATLAB preprocessing code (location unknown - need to find)

## Next Steps

After running the comparison analysis, update this document with:
- Actual magnitude of differences found
- Which neurons/stages are affected
- Root cause identified
- Fixes implemented (if needed)
- Verification that fixes resolve the issue
