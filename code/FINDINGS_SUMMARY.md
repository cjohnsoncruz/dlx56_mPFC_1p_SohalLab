# Investigation Summary: CANON vs NEW Time-Series Differences

## TL;DR

**91% of cells show differences** between CANON and NEW time-series files. After thorough investigation:

✅ **NOT the cause:**
- Trial detection logic (IDENTICAL)
- Stage assignment logic (IDENTICAL)
- Label range definitions for pre/post/ITI sections (IDENTICAL)
- Binning parameters (both use window_size=5)
- Rotation parameters (both use rotate_by=3)
- Normalization method (both use min-max)

⚠️ **LIKELY causes:**
1. **MATLAB trimming parameters unknown** - We don't know the value of `trim_params.trial_len`
2. **Python truncates post-outcome to 15s** - MATLAB might not
3. **Different handling of truncated trials**

## What Was Verified

### 1. Trial Detection ✅ IDENTICAL

**MATLAB** (vectorize_raster_methods.m:100-104):
```matlab
if ((labels(i-1) ~= 2) && (labels(i) == 2)) || ((labels(i-1) ~= 9) && (labels(i) == 9))
    trial_start_index(j) = i;
```

**Python** (trial_detection.py:23-27):
```python
if ((prev_val != 2 and cur_val == 2) or (prev_val != 9 and cur_val == 9)):
    starts0.append(i)
```

**Result:** Same trials detected

---

### 2. Stage Assignment ✅ IDENTICAL

Both use `early_criteria_value = 5` to define early/late boundaries.
Both apply fallback logic when <5 errors exist in early window.

**Result:** Same trials assigned to each stage

---

### 3. Label Range Definitions ✅ IDENTICAL

**MATLAB** (vectorize_raster_methods.m:83-90):
```matlab
% IA: pre=2-4, post=4-7, ITI=8
% RS: pre=9-11, post=11-14, ITI=15
```

**Python** (matlab_obj_to_python.py:49-56):
```python
ia_pre  = (labels >= 2)  & (labels <= 4)
ia_post = (labels >= 4)  & (labels <= 7)
ia_iti  = (labels == 8)
rs_pre  = (labels >= 9)  & (labels <= 11)
rs_post = (labels >= 11) & (labels <= 14)
rs_iti  = (labels == 15)
```

**Result:** Same frames assigned to each section

---

### 4. Binning and Rotation ✅ SAME PARAMETERS

**Both use:**
- `window_size = 5` frames (0.25s bins at 20 Hz)
- `rotate_by = 3` seconds (12 bins offset)

**Result:** Same binning structure

---

### 5. Normalization Method ✅ IDENTICAL

**Both use:**
- Min-max normalization
- Max value computed per neuron across all trials
- Filters neurons where max = 0 or NaN

**Result:** Same normalization approach

---

## Remaining Differences to Investigate

### 1. MATLAB Trimming Parameters ⚠️ UNKNOWN

**MATLAB** (return_section_activity_timeseries.m:61-63):
```matlab
num_bins_before_post_to_keep = round(analysis_config.seconds_before_post_to_keep * 20);
pre_section_end = trim_params.trial_len * 20;
pre_bins_kept = strcat("f_", string(pre_section_end - num_bins_before_post_to_keep : pre_section_end));
```

**Questions:**
- What is `trim_params.trial_len`? (15 seconds? 20 seconds?)
- What is `analysis_config.seconds_before_post_to_keep`? (3 seconds = 60 frames?)

**Python equivalent:**
```python
extract_trial_windows(df, pre_frames=60, post_frames=300)
```

**Impact:**
- If `trim_params.trial_len * 20` ≠ 300, different number of post-frames included
- If `seconds_before_post_to_keep * 20` ≠ 60, different number of pre-frames included

---

### 2. Post-Outcome Truncation ⚠️ POTENTIAL DIFFERENCE

**Python** (preprocessing_utils.py:71):
```python
raster_df = truncate_post_outcome_to_15s(raster_df, truncate_post=True)
```

**Code** (matlab_obj_to_python.py:64-87):
```python
def truncate_post_outcome_to_15s(raster_df, fps=20, max_seconds=15, truncate_post=True):
    max_frames = fps * max_seconds  # 300 frames

    # For each trial, count post_outcome frames
    # If > 300 frames, relabel excess as 'truncated_post_outcome'
    # Changes task_stage for those frames
```

**Question:** Does MATLAB also truncate post-outcome to 15 seconds?

**Impact:**
- If MATLAB keeps all post-outcome frames, different trials might have different effective lengths
- Trials with >15s post-outcome would differ
- This could affect which trials contribute to each stage's mean

---

### 3. Handling of Truncated Trials ⚠️ DIFFERENT IMPLEMENTATION

**MATLAB** (vectorize_raster_methods.m:32-38):
```matlab
case 'end'   % Keep last N frames
    window_to_keep = min(size(raster_cell_array{t}, 2), trim_length);
    trimmed_raster_cell_array{t} = raster_cell_array{t}(:, [1+size(raster_cell_array{t}, 2)-window_to_keep]:end);
```

- If trial has fewer frames than requested, **keeps all available frames**
- No padding, no NaN

**Python** (preprocessing_utils.py:196-198):
```python
# Reindex to full range - automatically pads with NaN for truncated trials
combined = combined.set_index('trial_window_frame').reindex(full_frame_range)
```

- If trial has fewer frames than requested, **pads with NaN**
- NaN values excluded from mean calculation

**Impact:**
- Both effectively use "available frames only"
- But MATLAB might have different column structure for short trials
- After binning, this difference should disappear

---

### 4. Bin Dropping Order and Values ⚠️ UNKNOWN PARAMETERS

**OLD Pipeline** (Colab → preprocess_data.py:97-98):
```python
normed_trial_tseries_df = drop_end_bins_of_trials(normed_trial_tseries_df, numeric_col,
                                                    n_end_timebins_to_drop=hyper_param_dict['n_post_end_bin_to_drop'])
normed_trial_tseries_df = drop_start_bins_of_trials(normed_trial_tseries_df, numeric_col,
                                                      n_start_timebins_to_drop=hyper_param_dict['n_pre_bin_to_drop'])
```

**NEW Pipeline** (notebook line 4127-4128):
```python
trial_tseries_df_norm = drop_end_bins_of_trials(trial_tseries_df_norm, numeric_col, n_end_timebins_to_drop)
trial_tseries_df_norm = drop_start_bins_of_trials(trial_tseries_df_norm, numeric_col, n_start_timebins_to_drop)
```

**Questions:**
- What were the values in `hyper_param_dict`?
- Are the NEW pipeline values the same?

**Impact:**
- If different bins are dropped, mean activity will differ
- Even dropping 1 extra bin could cause noticeable differences

---

## Recommended Actions

### Immediate: Check Parameters

1. **Find MATLAB trim parameters:**
   ```matlab
   % In analysis_config or trim_params:
   % - seconds_before_post_to_keep = ?
   % - trial_len = ?
   ```

2. **Find OLD Colab hyper_param_dict:**
   ```python
   # In run_autoencoder_lightning_v3.ipynb:
   # hyper_param_dict = {
   #     'n_post_end_bin_to_drop': ?,
   #     'n_pre_bin_to_drop': ?,
   #     ...
   # }
   ```

3. **Check NEW pipeline parameters:**
   ```python
   # In preprocess matlab data v6_modular.ipynb:
   # config['timeseries']['pre_frames'] = ?
   # config['timeseries']['post_frames'] = ?
   # n_start_timebins_to_drop = ?
   # n_end_timebins_to_drop = ?
   ```

### Detailed: Compare One Trial

Pick one neuron-stage pair with large difference and trace through every step:

```python
test_neuron = '13_4_WT_RS2-42'
test_stage = 'Early_IA_Error'
test_trial = 5  # Pick a specific trial

# Step 1: Raw frames
# - CANON: Which frames included?
# - NEW: Which frames included?

# Step 2: After binning
# - CANON: Which bins created?
# - NEW: Which bins created?

# Step 3: After rotation
# - CANON: Column order?
# - NEW: Column order?

# Step 4: After normalization
# - CANON: max_trial_val = ?
# - NEW: max_trial_val = ?

# Step 5: After bin dropping
# - CANON: Which bins remain?
# - NEW: Which bins remain?

# Step 6: Final mean
# - CANON: mean across remaining bins = ?
# - NEW: mean across remaining bins = ?
```

---

## Hypothesis Ranking

**Most Likely (80% confidence):**
1. Different `n_pre_bin_to_drop` or `n_end_timebins_to_drop` values
   - Would affect ALL neurons
   - Would cause systematic shift in mean activity

**Likely (60% confidence):**
2. Different `trim_params.trial_len` in MATLAB (not 15 seconds)
   - Would affect trials with long post-outcome periods
   - Could explain why some neurons match perfectly while others differ

**Possible (40% confidence):**
3. MATLAB doesn't truncate post-outcome to 15s
   - Would cause differences for long trials
   - Fits pattern of some cells matching, others not

**Less Likely (20% confidence):**
4. Different handling of edge cases (NaN, infinity, division by zero)
   - Would only affect small number of cells
   - Doesn't explain 91% differing

---

## Files Created

1. **[TRIAL_SLICING_COMPARISON.md](TRIAL_SLICING_COMPARISON.md)**
   - Detailed comparison of trial detection and stage assignment
   - Conclusion: IDENTICAL

2. **[PIPELINE_COMPARISON_OLD_vs_NEW.md](PIPELINE_COMPARISON_OLD_vs_NEW.md)**
   - Complete processing pipeline comparison
   - MATLAB → Colab vs Python-only

3. **[TIMESERIES_DIFFERENCES_INVESTIGATION.md](TIMESERIES_DIFFERENCES_INVESTIGATION.md)**
   - Initial investigation plan
   - 7 potential sources of differences

4. **This file: FINDINGS_SUMMARY.md**
   - Consolidated findings
   - Action items

---

## Next Steps

1. **Find missing parameters** (trim_params.trial_len, hyper_param_dict values)
2. **Run diagnostic on one trial** (trace through all processing steps)
3. **Once parameters match, re-run NEW pipeline**
4. **Verify differences resolved**

If differences persist after matching all parameters, the issue may be in:
- Floating-point precision differences
- Order of operations in matrix calculations
- Library version differences (numpy, pandas)
