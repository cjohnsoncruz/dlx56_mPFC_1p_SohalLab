# Pipeline Comparison: CANON (MATLAB → Colab) vs NEW (Python-only)

## Executive Summary

The CANON time-series was created through a **two-stage pipeline**:
1. MATLAB: Frame-level extraction → CSV export
2. Colab (Python): Binning, rotation, normalization → Parquet export

The NEW time-series uses a **single-stage Python pipeline**:
1. Python: Frame-level extraction → binning → rotation → normalization → Parquet export

**Root Cause of Differences:** The critical difference is in **how frames are selected from each trial**.

---

## CANON Pipeline (MATLAB → Colab)

### Stage 1: MATLAB (`return_section_activity_timeseries.m`)

**Location:** `C:\Users\13car\Dropbox\UCSF\vikaas\code GITHUB repos\Github Sohal Lab folders\ruleshifting-inscopix\Analysis Scripts\Analysis- Return section sig activity time-series\return_section_activity_timeseries.m`

#### Step 1: Slice into Sections

**Code** (line 35):
```matlab
raster = vectorize_raster_methods.slice_trim_raster(new_spikes, dataset_object.labels);
```

**How it works** (vectorize_raster_methods.m:66-93):
```matlab
% For RS trials (lines 83-86):
sliced_struct.pre{i}  = raster_by_trial{i}(:, (9 <= labels_by_trial{i}) & (labels_by_trial{i} <= 11));
sliced_struct.post{i} = raster_by_trial{i}(:, (11 <= labels_by_trial{i}) & (labels_by_trial{i} <= 14));
sliced_struct.ITI{i}  = raster_by_trial{i}(:, (labels_by_trial{i} == 15));

% For IA trials (lines 88-90):
sliced_struct.pre{i}  = raster_by_trial{i}(:, (2 <= labels_by_trial{i}) & (labels_by_trial{i} <= 4));
sliced_struct.post{i} = raster_by_trial{i}(:, (4 <= labels_by_trial{i}) & (labels_by_trial{i} <= 7));
sliced_struct.ITI{i}  = raster_by_trial{i}(:, (labels_by_trial{i} == 8));
```

**What this means:**
- IA trials: pre = labels 2-4, post = labels 4-7, ITI = label 8
- RS trials: pre = labels 9-11, post = labels 11-14, ITI = label 15
- **Note:** Label 4 (IA) and label 11 (RS) appear in BOTH pre and post!

#### Step 2: Trim Sections

**Code** (vectorize_raster_methods.m:56-64):
```matlab
function [trim_raster_struct] = trim_sliced_raster(sliced_struct)
    param_multiple = 20; % frames per second
    section_names = analysis_config.trial_section_names;
    trim_raster_struct.pre  = trim_raster_sec_in_cell_array(sliced_struct.pre,  param_multiple * trim_params.trial_len, trim_params.Pre);
    trim_raster_struct.post = trim_raster_sec_in_cell_array(sliced_struct.post, param_multiple * trim_params.trial_len, trim_params.Post);
    trim_raster_struct.ITI  = trim_raster_sec_in_cell_array(sliced_struct.ITI,  param_multiple * trim_params.ITI_len, trim_params.ITI);
end
```

**Trim logic** (vectorize_raster_methods.m:25-40):
```matlab
case 'end'   % Keep last N frames
    window_to_keep = min(size(raster_cell_array{t}, 2), trim_length);
    trimmed_raster_cell_array{t} = raster_cell_array{t}(:, [1+size(raster_cell_array{t}, 2)-window_to_keep]:end);

case 'start' % Keep first N frames
    window_to_keep = min(size(raster_cell_array{t}, 2), trim_length);
    trimmed_raster_cell_array{t} = raster_cell_array{t}(:, 1:window_to_keep);
```

**Typical parameters:**
- `trim_params.trial_len` = 15 seconds → 300 frames
- `trim_params.Pre` = 'end' → keep LAST 300 frames of pre-outcome
- `trim_params.Post` = 'start' → keep FIRST 300 frames of post-outcome
- `trim_params.ITI_len` = unknown

#### Step 3: Join Pre and Post

**Code** (return_section_activity_timeseries.m:96-104):
```matlab
if s == 2  % if post_decision section
    % Get last N frames from pre section
    num_bins_before_post_to_keep = round(analysis_config.seconds_before_post_to_keep * 20);
    pre_section_end = trim_params.trial_len * 20;
    pre_bins_kept = strcat("f_", string(pre_section_end - num_bins_before_post_to_keep : pre_section_end));

    prev_section_act = section_tables.pre(:, [pre_bins_kept, 'trial_num', 'neuron_ID']);
    new_pre_bin_names = strcat("-f_", string(fliplr(1:length(pre_bins_kept))));
    pre_section_table = renamevars(prev_section_act, pre_bins_kept, new_pre_bin_names);

    % Join pre with post
    section_tables.post = innerjoin(section_tables.post, pre_section_table, 'Keys', ["trial_num", "neuron_ID"]);
end
```

**What this does:**
- Takes last `analysis_config.seconds_before_post_to_keep * 20` frames from pre-outcome
- Renames them with negative indices: -f_100, -f_99, ..., -f_1
- Joins them with post-outcome frames
- **Result:** Post table has both pre and post frames

**Typical value:** `seconds_before_post_to_keep` = 3 seconds → 60 frames

#### Step 4: Export to CSV

**File:** `post_outcome_main_datasets_neurons_trial activity timeseries data_{date}_timeseries.csv`

**Structure:**
- Each row = one neuron in one trial
- Columns: `-f_60`, `-f_59`, ..., `-f_1`, `f_1`, `f_2`, ..., `f_300` (frame-level, 20 Hz)
- Metadata: `trial_num`, `neuron_ID`, `task_phase_vec`, etc.

---

### Stage 2: Colab Notebook (`run_autoencoder_lightning_v3.ipynb`)

**Location:** `G:\My Drive\Colab Notebooks\Previous Script Versions\run_autoencoder_lightning_v3.ipynb`

**Function:** `get_normed_trial_tseries(enriched_by_stage_path, post_activity_timeseries, hyper_param_dict)`

**Code** (preprocess_data.py:66-100):
```python
def get_normed_trial_tseries(stage_enriched_csv_path, act_tseries_path, hyper_param_dict):
    # Load CSV from MATLAB
    outcome_post = pd.read_csv(act_tseries_path, header=0, low_memory=False)

    # 1. Bin and rotate time-series
    outcome_post = bin_rotate_timeseries(outcome_post,
                                          window_size=window_to_bin,  # Default: 5 frames
                                          rotate_by=n_sec_to_rotate)   # Default: 3 seconds

    # 2. Min-max normalize
    numeric_col = get_numeric_cols_timeseries(outcome_post, " to ")
    normed_trial_tseries_df = run_min_max_norm_on_timeseries(
        norm_data, trial_tseries_df_raw,
        ['name', 'unique_ID'], numeric_col, 'max_trial_val')

    # 3. Drop bins from start and end
    normed_trial_tseries_df = drop_end_bins_of_trials(normed_trial_tseries_df, numeric_col,
                                                        n_end_timebins_to_drop=hyper_param_dict['n_post_end_bin_to_drop'])
    normed_trial_tseries_df = drop_start_bins_of_trials(normed_trial_tseries_df, numeric_col,
                                                          n_start_timebins_to_drop=hyper_param_dict['n_pre_bin_to_drop'])

    return normed_trial_tseries_df
```

#### Binning and Rotation

**Code** (preprocess_data.py:124-141):
```python
def bin_rotate_timeseries(input_df, window_size=5, rotate_by=3):
    # Bin frames (default: 5 frames → 0.25s bins at 20 Hz)
    input_df = bin_post_outcome(bin_post=True, outcome_post=input_df, win_n=window_size)

    # Rotate bins (default: 3 seconds → 12 bins at 0.25s/bin)
    bin_size = window_size / 20  # 5/20 = 0.25s
    offset = int(rotate_by / bin_size)  # 3 / 0.25 = 12 bins
    print(f" Moving numeric columns by {offset} bins")
    if offset > 0:
        input_df = rotate_df_numeric_cols(input_df, num_cols, offset)

    return input_df
```

**Result:**
- Columns: `-3.0s to -2.75s`, `-2.75s to -2.5s`, ..., `14.75s to 15.0s`
- 72 bins total

---

## NEW Pipeline (Python-only)

**Location:** `code/preprocess matlab data v6_modular.ipynb` + `preprocessing_utils.py`

### Step 1: Load MATLAB Objects

```python
loaded_objects = load_matlab_object(...)  # Imports .mat files
```

### Step 2: Transform to DataFrames

**Code** (preprocessing_utils.py:100-108):
```python
raster_dataframes = transform_all_datasets(loaded_objects, config, analysis_config,
                                            datatype='raster', normalize='none')
```

**This calls** (preprocessing_utils.py:20-97):
```python
def dataset_obj_to_df(dataset_obj, config, analysis_config, datatype='raster', normalize='none'):
    # 1. Create DataFrame from raster/dff
    raster_df = pd.DataFrame(input_data, ...)

    # 2. Add task stage info
    raster_df = add_task_stage_to_raster_df(raster_df, analysis_config)
    raster_df['trial_section'] = label_frame_sections_df(raster_df, 'labels', ...)

    # 3. Truncate post-outcome to 15 seconds
    raster_df = truncate_post_outcome_to_15s(raster_df, truncate_post=True)

    # 4. Drop inactive cells
    if drop_inactive_cells:
        selection_mask = raster_df['trial_section'] == 'post_outcome'
        active_cells = raster_df.loc[selection_mask, cell_cols].sum() > 0
        raster_df = raster_df.loc[:, active_cells.index[active_cells].tolist() + metadata_cols]

    return raster_df
```

### Step 3: Extract Trial Windows

**Code** (preprocessing_utils.py:164-207):
```python
def extract_trial_windows(df, pre_frames=60, post_frames=300):
    """Extract last N pre-outcome and M post-outcome frames for each trial"""

    trial_windows = []
    full_frame_range = list(range(-pre_frames, 0)) + list(range(1, post_frames + 1))

    for trial_id, trial_data in grouped:
        # Get last 60 pre-outcome frames
        pre = trial_data[trial_data['trial_section'] == 'pre_outcome'].tail(pre_frames)

        # Get first 300 post-outcome frames
        post = trial_data[trial_data['trial_section'] == 'post_outcome'].head(post_frames)

        # Create indices: -60, -59, ..., -1, 1, 2, ..., 300
        n_pre = len(pre)
        n_post = len(post)
        pre_indices = list(range(-n_pre, 0))
        post_indices = list(range(1, n_post + 1))

        # Combine and reindex (pads with NaN for truncated trials)
        combined = pd.concat([pre_with_idx, post_with_idx])
        combined = combined.set_index('trial_window_frame').reindex(full_frame_range)

        trial_windows.append(combined)

    return pd.concat(trial_windows)
```

**KEY DIFFERENCE FROM MATLAB:**
- MATLAB: Uses label ranges (pre=2-4, post=4-7 for IA)
- Python: Uses last 60 pre-frames, first 300 post-frames
- **These may not select the same frames!**

### Step 4: Pivot to Wide Format

**Code** (preprocessing_utils.py:209-249):
```python
def pivot_trial_windows(windowed_df):
    """Pivot so each row is one cell from one trial"""

    # Melt: convert cell columns to rows
    melted = windowed_df.melt(id_vars=['trial_num', 'trial_window_frame'],
                               value_vars=cell_cols, var_name='cell', value_name='activity')

    # Pivot: convert frames to columns
    pivoted = melted.pivot(index=['trial_num', 'cell'],
                            columns='trial_window_frame', values='activity')

    # Rename columns: -60 → -f_60, 1 → f_1, 300 → f_300
    pivoted.columns = [f'-f_{abs(frame)}' if frame < 0 else f'f_{frame}' for frame in pivoted.columns]

    return pivoted
```

### Step 5: Create Time-Series DataFrame

**Code** (preprocessing_utils.py:255-291):
```python
def create_subject_trial_tseries_df(input_df, ens_matrix, window_to_bin=5, n_sec_to_rotate=0):
    # Extract trial windows
    trim_df = extract_trial_windows(input_df, pre_frames=60, post_frames=300)

    # Pivot to wide format
    outcome_post = pivot_trial_windows(trim_df)
    outcome_post['neuron_id'] = outcome_post['subject_name'] + '-' + outcome_post['cell'].str.replace('cell_','')

    # Bin and rotate time-series
    outcome_post = bin_rotate_timeseries(outcome_post, window_size=window_to_bin, rotate_by=n_sec_to_rotate)

    # Join with ensemble matrix
    outcome_post = outcome_post.join(ens_matrix, on='neuron_id', how='left')

    return trial_tseries_df_raw
```

### Step 6: Normalize

**Code** (notebook around line 4801):
```python
trial_tseries_df_norm = normalize_all_subject_tseries_dfs(raster_dataframes, config=config)
```

**This calls:**
```python
# Min-max normalize
trial_tseries_df_norm = run_min_max_norm_on_timeseries(use_min_max_norm, trial_tseries_df_raw,
                                                         ['name', 'neuron_id'], numeric_col, 'max_trial_val')

# Drop bins
trial_tseries_df_norm = drop_end_bins_of_trials(trial_tseries_df_norm, numeric_col, n_end_timebins_to_drop)
trial_tseries_df_norm = drop_start_bins_of_trials(trial_tseries_df_norm, numeric_col, n_start_timebins_to_drop)
```

---

## Critical Differences

### 1. Frame Selection Method ⚠️ **HIGHEST PRIORITY**

**MATLAB:**
```matlab
% IA trials:
pre  = frames where labels are 2, 3, or 4
post = frames where labels are 4, 5, 6, or 7

% RS trials:
pre  = frames where labels are 9, 10, or 11
post = frames where labels are 11, 12, 13, or 14
```

**Python NEW:**
```python
# All trials:
pre  = last 60 frames where trial_section == 'pre_outcome'
post = first 300 frames where trial_section == 'post_outcome'
```

**Impact:**
- If `label_frame_sections_df()` doesn't use the same label ranges, **different frames are included**
- MATLAB includes label 4 (IA) and label 11 (RS) in BOTH pre and post
- Python might not have this overlap
- **This could explain the differences!**

### 2. Truncation Handling

**MATLAB:**
```matlab
% If trial has fewer frames than requested, keep what exists
window_to_keep = min(size(raster_cell_array{t}, 2), trim_length);
```

**Python:**
```python
# Pads with NaN for truncated trials
combined = combined.set_index('trial_window_frame').reindex(full_frame_range)
# NaN values are excluded from mean calculation
```

**Impact:**
- Same logical result (use available frames)
- But implementation differs

### 3. Pre-Outcome Frame Count

**MATLAB:**
- Joins `seconds_before_post_to_keep * 20` frames (typically 60)
- From the END of the trimmed pre section

**Python:**
- Takes `pre_frames` (default 60) frames
- From the END of pre_outcome section

**Impact:**
- Should be the same IF label ranges match
- But might differ if sections are defined differently

### 4. Processing Order

**MATLAB → Colab:**
1. Slice by labels
2. Trim to max length
3. Export to CSV (frame-level)
4. Bin (5 frames → 0.25s)
5. Rotate (3 seconds)
6. Normalize (min-max)
7. Drop bins

**Python NEW:**
1. Extract windows (last 60 pre, first 300 post)
2. Pivot to wide format
3. Bin (5 frames → 0.25s)
4. Rotate (3 seconds)
5. Normalize (min-max)
6. Drop bins

**Impact:**
- Order is similar except for initial extraction method
- Same binning, rotation, normalization parameters

---

## Recommended Investigation

### Step 1: Verify Label Range Definitions

Check how `label_frame_sections_df()` defines pre/post/ITI sections:

**Question:** Does it use the same label ranges as MATLAB?
- IA: pre=2-4, post=4-7, ITI=8?
- RS: pre=9-11, post=11-14, ITI=15?

**File to check:** `matlab_obj_to_python.py`

### Step 2: Compare Frame Counts

For a specific neuron-trial:
```python
# How many pre-frames does each pipeline include?
# How many post-frames does each pipeline include?
# Are the frame numbers the same?
```

### Step 3: Check Specific Trial

Pick trial with large difference:
```python
test_neuron = '13_4_WT_RS2-42'
test_stage = 'Early_IA_Error'

# In CANON: Which frames are included?
# In NEW: Which frames are included?
# Are they the same frames from the original raster?
```

---

## Hypothesis

**Most Likely Cause:** The NEW pipeline's `label_frame_sections_df()` function does NOT use the exact same label ranges as MATLAB's `slice_raster_into_sections()`.

**Result:** Different frames are selected → different activity values → mean differences

**Next Steps:**
1. Read `matlab_obj_to_python.py` to see how sections are defined
2. Compare with MATLAB's label ranges
3. If different, update Python to match MATLAB
4. Re-run pipeline and verify differences are resolved
