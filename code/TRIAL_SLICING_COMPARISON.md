# Trial Slicing Logic Comparison: MATLAB vs Python

## Summary

After detailed analysis of the MATLAB and Python implementations, the **trial detection and stage assignment logic are IDENTICAL** when accounting for 0-based vs 1-based indexing.

## Detailed Comparison

### 1. Trial Detection (`return_trial_num_at_frame`)

**MATLAB** (vectorize_raster_methods.m:95-113):
```matlab
for i = 2:length(labels)
    if ((labels(i-1) ~= 2) && (labels(i) == 2)) || ...
       ((labels(i-1) ~= 9) && (labels(i) == 9))
        trial_start_index(j) = i;
        j = j+1;
    end
end
```

**Python** (trial_detection.py:7-46):
```python
for i in range(1, T):
    prev_val = labels[i - 1]
    cur_val = labels[i]
    if ((prev_val != 2 and cur_val == 2) or
        (prev_val != 9 and cur_val == 9)):
        starts0.append(i)
```

**Status:** ✅ **IDENTICAL LOGIC**
- Both detect trial start when label transitions to 2 (IA trial) or 9 (RS trial)
- Same condition: previous label ≠ 2/9 AND current label = 2/9

---

### 2. Trial Classification (`get_inRS_isError`)

**MATLAB** (vectorize_raster_methods.m:43-52):
```matlab
in_RS(i) = sum(unique(input_labels(trial_num_at_frame == i)) > 8) > 1;
is_error(i) = sum(ismember([6, 13], input_labels(trial_num_at_frame == i))) > 0;
```

**Python** (trial_detection.py:156-183):
```python
in_RS[i - 1] = np.sum(np.unique(trial_vals) > 8) > 1
is_error[i - 1] = np.isin(trial_vals, [6, 13]).any()
```

**Status:** ✅ **IDENTICAL LOGIC**
- **in_RS:** Trial is RS if it has more than 1 unique label > 8
- **is_error:** Trial is error if it contains label 6 (IA error outcome) or 13 (RS error outcome)

---

### 3. Stage Assignment (`build_phase_masks` / `return_phase_index_count`)

#### Early/Late Boundary Definition

**MATLAB** (phase_index.m:95-97):
```matlab
[early_IA_end.index, early_RS_end.index] = deal(analysis_config.early_criteria_value);
early_IA_end.trial = index_obj.IA_trials(early_IA_end.index);
early_RS_end.trial = index_obj.RS_trials(early_RS_end.index);
```

**Python** (trial_detection.py:81-82):
```python
early_IA_end = ia_pos[min(earlyN, ia_pos.size) - 1]
early_RS_end = rs_pos[min(earlyN, rs_pos.size) - 1]
```

**Example with earlyN=5, 20 IA trials:**
- **MATLAB:** IA_trials(5) = trial #5 (1-indexed) → trials 1-5 are early
- **Python:** ia_pos[4] = trial index 4 (0-indexed) → trials 0-4 are early

**Status:** ✅ **IDENTICAL** (accounting for indexing)

#### Late IA Calculation

**MATLAB** (phase_index.m:133-140):
```matlab
late_IA_start = index_obj.last_IA_trials - analysis_config.early_criteria_value + 1;
last_N_index_obj.IA_trials = late_IA_start:index_obj.last_IA_trials;
late_IA_trial_logical = false(1, length(inRS_bool_vec));
late_IA_trial_logical(last_N_index_obj.IA_trials) = logical(true);
index_obj.phase_vec.(analysis_config.task_phase_names(3)) = ...
    late_IA_trial_logical & ~IsError_bool_vec;
```

**Python** (trial_detection.py:105-109):
```python
late_ia_start = last_IA - earlyN + 1
late_ia_idx = np.arange(late_ia_start, last_IA + 1, dtype=int)
mask_late_ia = np.zeros(T, dtype=bool)
mask_late_ia[late_ia_idx] = True
out[canon["late_ia"]] = mask_late_ia & (~is_error)
```

**Example with last_IA=19 (0-indexed), earlyN=5:**
- **MATLAB:** 20-5+1 = 16 → trials 16:20 (1-indexed) = trials 16,17,18,19,20 (5 trials)
- **Python:** 19-5+1 = 15 → trials 15:20 (0-indexed) = trials 15,16,17,18,19 (5 trials)

**Status:** ✅ **IDENTICAL** (accounting for indexing)

#### Error Trial Fallback Logic

**MATLAB** (phase_index.m:113-124):
```matlab
if index_obj.early_IA_errors_exist
    index_obj.phase_vec.(analysis_config.task_phase_names(1)) = trial_is_error_notRS_inEarlyIA;
elseif sum(trial_isError_notRS) > 0
    n_IA_errors_to_use = min([sum(trial_isError_notRS), analysis_config.early_criteria_value]);
    IA_errors_indices_to_use = index_obj.IA_error(1:n_IA_errors_to_use);
    IA_early_error_bool = false(1, length(inRS_bool_vec));
    IA_early_error_bool(IA_errors_indices_to_use) = logical(true);
    index_obj.phase_vec.(analysis_config.task_phase_names(1)) = IA_early_error_bool;
end
```

**Python** (trial_detection.py:89-99):
```python
ia_err_early = is_error & (~in_RS) & in_early_IA
if ia_err_early.any():
    out[canon["early_ia_error"]] = ia_err_early
else:
    ia_err_idx = np.where(is_error & (~in_RS))[0]
    if ia_err_idx.size > 0:
        pick = ia_err_idx[:min(ia_err_idx.size, earlyN)]
        mask = np.zeros(T, dtype=bool)
        mask[pick] = True
        out[canon["early_ia_error"]] = mask
```

**Status:** ✅ **IDENTICAL LOGIC**
- First check if errors exist in early window
- If not, take first N error trials (wherever they are)
- Use min() to handle case where fewer than N errors exist

---

## Conclusion: Trial Slicing Logic is Correct

The trial detection and stage assignment logic between MATLAB and Python are **functionally identical**. Any differences in the final time-series data are **NOT** caused by:
- ❌ Different trial boundary detection
- ❌ Different IA/RS classification
- ❌ Different error trial detection
- ❌ Different early/late stage boundaries
- ❌ Different fallback logic for sparse errors

## Where to Look Next

Since trial slicing is correct, the differences must come from **downstream processing**:

### 1. Frame-Level Slicing (Pre/Post/ITI Sections)

**MATLAB** (vectorize_raster_methods.m:83-91):
```matlab
% For RS trials:
sliced_struct.pre{i} = raster_by_trial{i}(:, (9 <= labels_by_trial{i}) & (labels_by_trial{i} <= 11));
sliced_struct.post{i} = raster_by_trial{i}(:, (11 <= labels_by_trial{i}) & (labels_by_trial{i} <= 14));
sliced_struct.ITI{i} = raster_by_trial{i}(:, (labels_by_trial{i} == 15));

% For IA trials:
sliced_struct.pre{i} = raster_by_trial{i}(:, (2 <= labels_by_trial{i}) & (labels_by_trial{i} <= 4));
sliced_struct.post{i} = raster_by_trial{i}(:, (4 <= labels_by_trial{i}) & (labels_by_trial{i} <= 7));
sliced_struct.ITI{i} = raster_by_trial{i}(:, (labels_by_trial{i} == 8));
```

**Python** - Check `matlab_obj_to_python.py` for equivalent function

**ACTION NEEDED:** Verify that Python uses same label ranges for pre/post/ITI

### 2. Trial Window Extraction

**Python** (preprocessing_utils.py:164-207):
```python
def extract_trial_windows(df, pre_frames=60, post_frames=300):
    # Extract last N pre-outcome and M post-outcome frames
```

**ACTION NEEDED:**
- Does MATLAB use same pre_frames=60, post_frames=300?
- How does MATLAB handle truncated trials (padding with NaN)?
- Are the same frames included in mean calculation?

### 3. Binning and Rotation

**Python** (preprocessing_utils.py:285):
```python
outcome_post = bin_rotate_timeseries(outcome_post, window_size=window_to_bin, rotate_by=n_sec_to_rotate)
```

**ACTION NEEDED:**
- Verify MATLAB uses same window_size and rotate_by values
- Confirm binning method (mean vs sum)
- Check rotation offset calculation

### 4. Min-Max Normalization

**Python** (helper_functions.py:501-519):
```python
max_e_rate = get_unit_max_event_rate_of_all_trials(...)
normed_ts_df.loc[:, numeric_col] = normed_ts_df.loc[:, numeric_col].values / normed_ts_df.loc[:, max_val_col_name].values[:,np.newaxis]
```

**ACTION NEEDED:**
- Does MATLAB compute max the same way?
- Are the same trials included in max calculation?
- Is filtering (removing neurons with max=0) applied the same way?

### 5. Bin Dropping

**Python** (notebook lines 4127-4128):
```python
trial_tseries_df_norm = drop_end_bins_of_trials(trial_tseries_df_norm, numeric_col, n_end_timebins_to_drop)
trial_tseries_df_norm = drop_start_bins_of_trials(trial_tseries_df_norm, numeric_col, n_start_timebins_to_drop)
```

**ACTION NEEDED:**
- Does MATLAB drop bins BEFORE or AFTER normalization?
- Same n_start and n_end values?

## Recommended Next Steps

1. ✅ Trial slicing verification (COMPLETE - IDENTICAL)
2. ⏭️ Verify frame-level pre/post/ITI extraction uses same label ranges
3. ⏭️ Verify trial window extraction (pre_frames, post_frames, padding)
4. ⏭️ Verify binning and rotation parameters match
5. ⏭️ Verify normalization max calculation includes same trials
6. ⏭️ Verify bin dropping happens at same step in pipeline

## Files to Investigate

- `matlab_obj_to_python.py` - Check label_frame_sections_df and truncate_post_outcome_to_15s
- MATLAB preprocessing script - Find values for pre_frames, post_frames, window_size, rotate_by
- MATLAB normalization code - How is max_trial_val computed?
