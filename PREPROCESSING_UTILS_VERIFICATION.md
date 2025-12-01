# Preprocessing Utils Function Transfer Verification

**Date:** 2025-11-29
**Purpose:** Verify that functions were transferred from notebook to preprocessing_utils.py
**Status:** ⚠️ **SIGNIFICANT ALTERATIONS DETECTED**

---

## Verification Method

1. **Extracted original code** from notebook using automated search
2. **Compared line-by-line** with preprocessing_utils.py
3. **Documented all differences** between original and transferred versions
4. **Categorized changes** as intentional refactoring vs. potential bugs

---

## Critical Finding: Functions Were NOT Transferred Unchanged

❌ **The functions in preprocessing_utils.py are SIGNIFICANTLY DIFFERENT from the notebook originals.**

These are **refactored versions**, not direct copies. While many changes improve modularity and reusability, some may introduce bugs or change behavior.

---

## Function-by-Function Comparison

### 1. dataset_obj_to_df() - ⚠️ HEAVILY MODIFIED

**Original Location:** Notebook line ~491
**Lines in Original:** ~70 lines
**Lines in preprocessing_utils.py:** ~150 lines (with docstring)

#### CRITICAL DIFFERENCES:

| Aspect | Original Notebook | preprocessing_utils.py | Impact |
|--------|-------------------|------------------------|--------|
| **Gaussian parameters** | Hardcoded `sigma=1, truncate=1.0` | Parameterized `gaussian_sigma`, `gaussian_truncate` | ✅ Better - allows config control |
| **Labels column** | Adds `raster_df['labels'] = dataset_obj['labels']` | Does NOT add labels | ⚠️ **MISSING FEATURE** |
| **Baseline calculation** | Computes `baseline_mean`, `baseline_std` from data | Does NOT compute baseline stats | ⚠️ **MISSING - baseline_zscore won't work!** |
| **Config access** | Uses `config['preprocessing']['drop_inactive_cells']` | Parameter `drop_inactive_cells=False` | ✅ Better - dependency injection |
| **Task stage function** | Calls `add_task_stage_to_raster_df(raster_df, analysis_config)` | Calls `add_task_stage_fn(raster_df, dataset_obj)` | ⚠️ **DIFFERENT SIGNATURE** |
| **Frame sections** | Calls `label_frame_sections_df(raster_df, 'labels', section_names=...)` | Calls `label_frame_sections_fn(raster_df, dataset_obj)` | ⚠️ **DIFFERENT SIGNATURE** |
| **Truncation** | Calls `truncate_post_outcome_to_15s(raster_df, truncate_post=True)` | Does NOT call truncation | ⚠️ **MISSING FEATURE** |
| **Metadata creation** | Uses `.assign(**{...})` | Creates `metadata_df`, then `pd.concat()` | ✅ Better - clearer pattern |
| **Inactive cell mask** | `trial_section == 'post_outcome'` | `task_stage.isin(['in_RS', 'postout'])` | ⚠️ **DIFFERENT LOGIC** |
| **Imaging data version** | Not in original | Added `imaging_data_version` metadata | ✅ Better - more metadata |

#### CODE COMPARISON:

**ORIGINAL (Notebook):**
```python
def dataset_obj_to_df(dataset_obj, datatype:str = 'raster', normalize:str = 'none'):
    # ... validation ...

    input_data = dataset_obj[datatype]
    if datatype == 'dff':
        input_data = gaussian_filter1d(input_data, sigma=1, axis=0, truncate=1.0)  # HARDCODED

    # ... create raster_df ...

    raster_df['labels'] = dataset_obj['labels']  # ADDS LABELS
    raster_df['labels'] = raster_df['labels'].astype('Int16')

    # COMPUTES BASELINE STATS
    baseline_mask = raster_df['labels'] == 1
    if normalize is not 'none':
        baseline_data = raster_df.loc[baseline_mask, cell_cols]
        baseline_mean = baseline_data.mean()
        baseline_std = baseline_data.std()

    # READS FROM CONFIG
    drop_inactive_cells = config['preprocessing']['drop_inactive_cells']

    raster_df = raster_df.assign(**{
        'normalized': normalize,
        'datatype': datatype,
        'subject_name': dataset_obj['name'],
        'geno': dataset_obj['geno'],
        'session': dataset_obj['session'],
        'drop_inactive_cells': drop_inactive_cells,
    })

    # CALLS SPECIFIC FUNCTIONS
    raster_df = add_task_stage_to_raster_df(raster_df, analysis_config)
    raster_df['trial_section'] = label_frame_sections_df(raster_df, 'labels', section_names=analysis_config.trial_section_names)
    raster_df = truncate_post_outcome_to_15s(raster_df, truncate_post=True)

    if drop_inactive_cells:
        selection_mask = raster_df['trial_section'] == 'post_outcome'  # USES trial_section
        # ... drop inactive cells ...

    # USES COMPUTED BASELINE
    if normalize == 'baseline_zscore':
        zscored_dff = (raster_df[cell_cols] - baseline_mean[cell_cols]) / baseline_std[cell_cols]
        raster_df[cell_cols] = zscored_dff
```

**PREPROCESSING_UTILS.PY:**
```python
def dataset_obj_to_df(
    dataset_obj: Dict[str, Any],
    datatype: str = 'raster',
    normalize: str = 'none',
    gaussian_sigma: float = 1.0,  # PARAMETERIZED
    gaussian_truncate: float = 1.0,  # PARAMETERIZED
    drop_inactive_cells: bool = False,  # PARAMETERIZED
    label_frame_sections_fn=None,  # DEPENDENCY INJECTION
    add_task_stage_fn=None  # DEPENDENCY INJECTION
) -> pd.DataFrame:
    # ... validation ...

    input_data = dataset_obj[datatype]
    if datatype == 'dff':
        input_data = gaussian_filter1d(input_data, sigma=gaussian_sigma, axis=0, truncate=gaussian_truncate)

    # ... create raster_df ...

    # NO LABELS COLUMN ADDED

    # NO BASELINE CALCULATION

    metadata_df = pd.DataFrame({
        'subject_name': dataset_obj['name'],
        'session': dataset_obj['session'],
        'geno': dataset_obj['geno'],
        'imaging_data_version': dataset_obj['imaging_data_version'],  # ADDED
        'normalized': normalize,
        'datatype': datatype,
    }, index=raster_df.index)

    raster_df = pd.concat([metadata_df, raster_df], axis=1)

    # DEPENDENCY INJECTION
    if label_frame_sections_fn is not None:
        raster_df = label_frame_sections_fn(raster_df, dataset_obj)
    if add_task_stage_fn is not None:
        raster_df = add_task_stage_fn(raster_df, dataset_obj)

    # NO TRUNCATION CALL

    if drop_inactive_cells and datatype == 'dff':
        if 'task_stage' in raster_df.columns:
            selection_mask = raster_df['task_stage'].isin(['in_RS', 'postout'])  # DIFFERENT LOGIC
            # ... drop inactive cells ...

    # BASELINE_ZSCORE WON'T WORK - NO baseline_mean/baseline_std
    elif normalize == 'baseline_zscore':
        print(" Warning: baseline_zscore requires external baseline_mean and baseline_std")
        print(" Skipping normalization - implement baseline calculation in calling code")
```

**VERDICT:** ⚠️ **This is a refactored version with MISSING FEATURES**

---

### 2. transform_all_datasets() - ✅ MINOR CHANGES

**Original Location:** Notebook line ~568
**Lines in Original:** ~7 lines

#### DIFFERENCES:

| Aspect | Original Notebook | preprocessing_utils.py | Impact |
|--------|-------------------|------------------------|--------|
| **Docstring** | Missing docstring | Added comprehensive docstring | ✅ Better - documentation |
| **Type hints** | Minimal | Full type hints | ✅ Better - type safety |
| **Core logic** | Identical | Identical | ✅ Unchanged |

**ORIGINAL:**
```python
def transform_all_datasets(loaded_objects:List[Dict[str, Any]], datatype:str = 'raster', normalize:str = 'none') -> Dict[str, pd.DataFrame]:
    raster_dataframes = {}
    for obj in loaded_objects:
        raster_df = dataset_obj_to_df(obj, datatype = datatype, normalize = normalize)
        raster_dataframes[obj['name']] = raster_df
    print(f"\nTotal DataFrames created: {len(raster_dataframes)}")
    return raster_dataframes
```

**PREPROCESSING_UTILS.PY:**
```python
def transform_all_datasets(
    loaded_objects: List[Dict[str, Any]],
    datatype: str = 'raster',
    normalize: str = 'none',
    **kwargs  # ADDED - allows passing extra params
) -> Dict[str, pd.DataFrame]:
    """[Docstring added]"""
    raster_dataframes = {}
    for obj in loaded_objects:
        raster_df = dataset_obj_to_df(obj, datatype=datatype, normalize=normalize, **kwargs)  # **kwargs added
        raster_dataframes[obj['name']] = raster_df
    print(f"\nTotal DataFrames created: {len(raster_dataframes)}")
    return raster_dataframes
```

**VERDICT:** ✅ **Functionally equivalent with improvements**

---

### 3. read_shuffle_parquet_from_folder() - ✅ UNCHANGED

**Original Location:** Notebook line ~791
**Lines in Original:** ~10 lines

#### DIFFERENCES:

| Aspect | Original Notebook | preprocessing_utils.py | Impact |
|--------|-------------------|------------------------|--------|
| **Core logic** | Identical | Identical | ✅ Unchanged |
| **Docstring** | Original docstring preserved | Added comprehensive docstring | ✅ Better |
| **Print statement** | "from previous run" | "from {folder}" | ✅ Better - more specific |

**ORIGINAL:**
```python
def read_shuffle_parquet_from_folder(shuffle_storage_folder: Path) -> Dict[str, pd.DataFrame]:
    """ Reads  parquet files in folder, containing shuffled mean activity DataFrame """
    all_subject_shuffles = {}
    for parquet_file in shuffle_storage_folder.glob("*_shuffled_mean_activity.parquet"):
        subject_name = parquet_file.stem.replace('_shuffled_mean_activity', '')
        all_subject_shuffles[subject_name] = pd.read_parquet(parquet_file)
        print(f" Loaded: {subject_name}")
    print(f"Loaded {len(all_subject_shuffles)} subjects from previous run")
    return all_subject_shuffles
```

**PREPROCESSING_UTILS.PY:**
```python
def read_shuffle_parquet_from_folder(shuffle_storage_folder: Path) -> Dict[str, pd.DataFrame]:
    """[Enhanced docstring]"""
    all_subject_shuffles = {}
    for parquet_file in shuffle_storage_folder.glob("*_shuffled_mean_activity.parquet"):
        subject_name = parquet_file.stem.replace('_shuffled_mean_activity', '')
        all_subject_shuffles[subject_name] = pd.read_parquet(parquet_file)
        print(f" Loaded: {subject_name}")
    print(f"Loaded {len(all_subject_shuffles)} subjects from {shuffle_storage_folder}")  # Better message
    return all_subject_shuffles
```

**VERDICT:** ✅ **Functionally equivalent**

---

### 4. get_intercol_corrs() - ✅ UNCHANGED

**Original Location:** Notebook line ~1918
**Lines in Original:** ~12 lines

#### DIFFERENCES:

| Aspect | Original Notebook | preprocessing_utils.py | Impact |
|--------|-------------------|------------------------|--------|
| **Core logic** | Identical | Identical | ✅ Unchanged |
| **Docstring** | Missing | Added comprehensive docstring | ✅ Better |

**ORIGINAL:**
```python
def get_intercol_corrs(df: pd.DataFrame, stage_names: List[str], suffix1: str, suffix2: str) -> pd.DataFrame:
    correlations = {}
    for stage in stage_names:
        col1 = f"{stage}{suffix1}"
        col2 = f"{stage}{suffix2}"
        if col1 in df.columns and col2 in df.columns:
            corr_value = df[col1].corr(df[col2])
            correlations[stage] = corr_value
        else:
            print(f"Warning: Columns {col1} or {col2} not found in DataFrame.")
    corr_df = pd.DataFrame.from_dict(correlations, orient='index', columns=['Correlation'])
    return corr_df
```

**PREPROCESSING_UTILS.PY:**
```python
# IDENTICAL - only docstring added
```

**VERDICT:** ✅ **Unchanged except for documentation**

---

### 5. extract_trial_windows() - ⚠️ HEAVILY MODIFIED

**Original Location:** Notebook line ~3433
**Lines in Original:** ~48 lines

#### CRITICAL DIFFERENCES:

| Aspect | Original Notebook | preprocessing_utils.py | Impact |
|--------|-------------------|------------------------|--------|
| **Default parameters** | Uses `config['timeseries']['pre_frames']` | Uses `pre_frames=60` (hardcoded default) | ✅ Better - no config dependency |
| **Trial extraction logic** | Uses `trial_section == 'pre_outcome'` | Searches for `task_stage == 'outcome'` frame | ⚠️ **COMPLETELY DIFFERENT ALGORITHM** |
| **Frame indexing** | Simple `.tail(pre_frames)` and `.head(post_frames)` | Complex calculation with outcome frame detection | ⚠️ **DIFFERENT APPROACH** |
| **Padding logic** | Reindex to full range | Uses `-np.inf` and `np.inf` for padding | ⚠️ **DIFFERENT PADDING** |

**ORIGINAL:**
```python
def extract_trial_windows(df,
                          pre_frames=config['timeseries']['pre_frames'],
                          post_frames=config['timeseries']['post_frames']) -> pd.DataFrame:
    """Extract last N pre-outcome and M post-outcome frames for each trial, padded to consistent length."""

    grouped = df.groupby(['subject_name', 'session', 'trial_num'])

    # ... validation ...

    for trial_id, trial_data in grouped:
        # SIMPLE APPROACH - uses trial_section labels
        pre = trial_data[trial_data['trial_section'] == 'pre_outcome'].tail(pre_frames)
        post = trial_data[trial_data['trial_section'] == 'post_outcome'].head(post_frames)

        # Create frame indices
        n_pre = len(pre)
        n_post = len(post)
        pre_indices = list(range(-n_pre, 0))
        post_indices = list(range(1, n_post + 1))

        pre_with_idx = pre.assign(trial_window_frame=pre_indices)
        post_with_idx = post.assign(trial_window_frame=post_indices)

        # ... concatenate and reindex ...
```

**PREPROCESSING_UTILS.PY:**
```python
def extract_trial_windows(df: pd.DataFrame, pre_frames: int = 60, post_frames: int = 300) -> pd.DataFrame:
    """[Docstring]"""

    grouped = df.groupby(['subject_name', 'session', 'trial_num'])

    # ... validation ...

    for trial_id, trial_data in grouped:
        # COMPLEX APPROACH - finds outcome frame explicitly
        outcome_mask = trial_data['task_stage'] == 'outcome'
        if not outcome_mask.any():
            continue  # Skip trials without outcome

        outcome_idx = trial_data[outcome_mask].index[0]
        outcome_frame_num = int(outcome_idx.split('_')[1])

        # Extract pre-outcome frames (relative to outcome)
        pre_mask = (trial_data.index.str.extract(r'frame_(\d+)')[0].astype(int) <= outcome_frame_num - 1)
        pre_data = trial_data[pre_mask]

        if len(pre_data) > 0:
            pre_frame_nums = pre_data.index.str.extract(r'frame_(\d+)')[0].astype(int).values
            trial_window_frames = pre_frame_nums - outcome_frame_num

            # Pad to pre_frames length
            n_to_pad = pre_frames - len(trial_window_frames)
            if n_to_pad > 0:
                trial_window_frames = np.concatenate([np.full(n_to_pad, -np.inf), trial_window_frames])
            # ... much more complex logic ...
```

**VERDICT:** ⚠️ **COMPLETELY REWRITTEN - Different algorithm!**

---

### 6. pivot_trial_windows() - ⚠️ MODIFIED

**Original Location:** Notebook line ~3479
**Lines in Original:** ~35 lines

#### DIFFERENCES:

| Aspect | Original Notebook | preprocessing_utils.py | Impact |
|--------|-------------------|------------------------|--------|
| **Core pivot logic** | Identical | Identical | ✅ Unchanged |
| **Spot check** | Uses `sample_cell = cell_cols[0]` | Uses `sample_cell = pivoted[new_cell_col_name].iloc[0]` | ✅ Better - more robust |
| **Assertion logic** | Gets frame columns differently | Gets frame columns with startswith | ⚠️ Different approach |

**ORIGINAL:**
```python
# Value spot check
sample_trial = pivoted['trial_num'].iloc[0]
sample_cell = cell_cols[0]  # USES FIRST CELL FROM ORIGINAL
frame_cols = [col for col in pivoted.columns if col.startswith(('f_', '-f_'))]

original = windowed_df[windowed_df['trial_num'] == sample_trial][sample_cell].values
pivoted_vals = pivoted[(pivoted['trial_num'] == sample_trial) & (pivoted[new_cell_col_name] == sample_cell)][frame_cols].values.flatten()
```

**PREPROCESSING_UTILS.PY:**
```python
# Value spot check
sample_trial = pivoted['trial_num'].iloc[0]
sample_cell = pivoted[new_cell_col_name].iloc[0]  # USES FIRST CELL FROM PIVOTED
original = windowed_df[(windowed_df['trial_num'] == sample_trial)][cell_cols].values
pivoted_vals = pivoted[(pivoted['trial_num'] == sample_trial) & (pivoted[new_cell_col_name] == sample_cell)][[col for col in new_columns]].values
```

**VERDICT:** ⚠️ **Minor modifications to validation logic**

---

### 7. get_first_active_stage() - ✅ UNCHANGED

**Original Location:** Notebook line ~4488
**Lines in Original:** ~5 lines

#### DIFFERENCES:

| Aspect | Original Notebook | preprocessing_utils.py | Impact |
|--------|-------------------|------------------------|--------|
| **Core logic** | Identical | Identical | ✅ Unchanged |
| **Docstring** | Original preserved | Added comprehensive docstring | ✅ Better |

**VERDICT:** ✅ **Unchanged except for documentation**

---

## Summary of Alterations

### Functions Transferred Unchanged (3/7):
1. ✅ `transform_all_datasets()` - Minor improvement (**kwargs added)
2. ✅ `read_shuffle_parquet_from_folder()` - Print message improved
3. ✅ `get_intercol_corrs()` - Unchanged
4. ✅ `get_first_active_stage()` - Unchanged

### Functions Significantly Modified (3/7):
1. ⚠️ `dataset_obj_to_df()` - **HEAVILY REFACTORED** - Missing features!
2. ⚠️ `extract_trial_windows()` - **COMPLETELY REWRITTEN** - Different algorithm!
3. ⚠️ `pivot_trial_windows()` - **MODIFIED** - Minor validation changes

---

## Critical Issues Found

### Issue 1: dataset_obj_to_df() Missing Baseline Calculation
**Problem:** Original computes `baseline_mean` and `baseline_std` from data, but preprocessing_utils.py version does not.

**Impact:** `normalize='baseline_zscore'` will NOT work in preprocessing_utils.py version.

**Original Code:**
```python
baseline_mask = raster_df['labels'] == 1
if normalize is not 'none':
    baseline_data = raster_df.loc[baseline_mask, cell_cols]
    baseline_mean = baseline_data.mean()
    baseline_std = baseline_data.std()

# Later...
if normalize == 'baseline_zscore':
    zscored_dff = (raster_df[cell_cols] - baseline_mean[cell_cols]) / baseline_std[cell_cols]
```

**Fix Needed:** Add baseline calculation to preprocessing_utils.py OR document that baseline stats must be computed externally.

---

### Issue 2: dataset_obj_to_df() Missing 'labels' Column
**Problem:** Original adds `raster_df['labels'] = dataset_obj['labels']`, but preprocessing_utils.py does not.

**Impact:** Downstream code expecting 'labels' column will fail.

---

### Issue 3: dataset_obj_to_df() Missing truncate_post_outcome_to_15s()
**Problem:** Original calls `truncate_post_outcome_to_15s(raster_df, truncate_post=True)`, but preprocessing_utils.py does not.

**Impact:** Data won't be truncated to 15s post-outcome as expected.

---

### Issue 4: extract_trial_windows() Uses Completely Different Algorithm
**Problem:** Original uses `trial_section` labels, preprocessing_utils.py searches for `task_stage == 'outcome'` frame.

**Impact:** May extract different frames! Results could differ between notebook and utility version.

**Original Approach:**
```python
pre = trial_data[trial_data['trial_section'] == 'pre_outcome'].tail(pre_frames)
post = trial_data[trial_data['trial_section'] == 'post_outcome'].head(post_frames)
```

**Preprocessing_utils.py Approach:**
```python
outcome_mask = trial_data['task_stage'] == 'outcome'
outcome_idx = trial_data[outcome_mask].index[0]
outcome_frame_num = int(outcome_idx.split('_')[1])
# ... complex frame number calculations ...
```

---

## Verification Evidence

### Evidence 1: Automated Extraction
Used Task agent with "very thorough" setting to extract all function definitions from notebook.

**Command:**
```
Read notebook and extract EXACT, COMPLETE source code for these 7 functions...
For each function, provide the complete function definition with all code including whitespace
```

**Result:** Retrieved all 7 functions with complete source code.

---

### Evidence 2: Line-by-Line Comparison
Read preprocessing_utils.py sections and compared against extracted originals.

**Method:**
- Read preprocessing_utils.py with offset/limit
- Compared function signatures
- Compared core logic blocks
- Identified all differences

---

### Evidence 3: Diff Summary

| Function | Lines Changed | Type of Change |
|----------|---------------|----------------|
| `dataset_obj_to_df()` | ~40 lines | Major refactoring |
| `transform_all_datasets()` | 2 lines | Minor improvement |
| `read_shuffle_parquet_from_folder()` | 1 line | Minor improvement |
| `get_intercol_corrs()` | 0 lines | Docstring only |
| `extract_trial_windows()` | ~30 lines | Complete rewrite |
| `pivot_trial_windows()` | ~5 lines | Minor modification |
| `get_first_active_stage()` | 0 lines | Docstring only |

---

## Conclusion

❌ **The functions were NOT transferred without alteration.**

**Actual Status:**
- 4/7 functions are functionally equivalent (minor documentation improvements)
- 3/7 functions are significantly modified with potential breaking changes

**Reason for Changes:**
- Removing hardcoded config dependencies
- Implementing dependency injection pattern
- Adding comprehensive docstrings
- Attempting to make functions more general-purpose

**Recommendation:**
1. ⚠️ **DO NOT use preprocessing_utils.py as a drop-in replacement** for notebook functions
2. ⚠️ **Fix Issue #1**: Add baseline calculation to dataset_obj_to_df()
3. ⚠️ **Fix Issue #2**: Add 'labels' column support
4. ⚠️ **Fix Issue #3**: Add truncation support or document removal
5. ⚠️ **Fix Issue #4**: Decide which extract_trial_windows() algorithm is correct
6. ✅ **Create unit tests** to verify both versions produce identical output
7. ✅ **Update documentation** to clearly state what was changed and why

---

**Verification Completed:** 2025-11-29
**Verified By:** Automated extraction + manual line-by-line comparison
**Confidence Level:** HIGH - All differences documented with evidence
