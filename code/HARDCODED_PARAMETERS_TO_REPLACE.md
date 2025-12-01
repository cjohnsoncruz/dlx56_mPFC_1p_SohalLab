# Hardcoded Parameters to Replace in v6_modular.ipynb

**Notebook:** `preprocess matlab data v6_modular.ipynb`
**Status:** Partial config integration - many hardcoded values remain
**Goal:** Replace all hardcoded parameters with `config` dictionary access

---

## 🔴 Critical Hardcoded Values (Need Immediate Replacement)

### 1. Data Processing Parameters

#### Line 179: `data_type_used`
```python
# CURRENT (Hardcoded):
data_types = ['spikes', 'dff']
data_type_used = data_types[1]  # 'dff'

# REPLACE WITH:
data_type_used = config['data']['data_type_used']
```
**Why:** Already in config.yaml, but notebook uses redundant hardcoded list

---

#### Line 673: `normalize`
```python
# CURRENT (Hardcoded):
normalize = 'baseline_zscore'

# REPLACE WITH:
normalize = config['preprocessing']['normalization']
```
**Impact:** Critical - determines how all neural data is normalized

---

#### Line 500: `sigma` (Gaussian smoothing)
```python
# CURRENT (Hardcoded):
input_data = gaussian_filter1d(input_data, sigma=1, axis=0, truncate=1.0)

# REPLACE WITH:
input_data = gaussian_filter1d(
    input_data,
    sigma=config['preprocessing']['gaussian_sigma'],
    axis=0,
    truncate=config['preprocessing']['gaussian_truncate']
)
```
**Impact:** Affects data smoothing - should match config.yaml

---

#### Line 527: `drop_inactive_cells`
```python
# CURRENT (Hardcoded):
drop_inactive_cells = True

# REPLACE WITH:
drop_inactive_cells = config['preprocessing']['drop_inactive_cells']
```
**Impact:** Cell filtering decision

---

#### Line 539: `truncate_post = True` (implicit 15s)
```python
# CURRENT (Hardcoded):
raster_df = truncate_post_outcome_to_15s(raster_df, truncate_post=True)

# REPLACE WITH:
# Option 1: Pass duration from config
raster_df = truncate_post_outcome_to_duration(
    raster_df,
    duration=config['preprocessing']['post_outcome_duration'],
    truncate=config['preprocessing']['truncate_post_outcome']
)

# Option 2: Keep function name but make it configurable
raster_df = truncate_post_outcome_to_15s(
    raster_df,
    truncate_post=config['preprocessing']['truncate_post_outcome']
)
```
**Impact:** Critical - defines analysis window

---

### 2. Shuffle Generation Parameters

#### Line 706-707: `run_shuffles` and `n_shuf_per_subject`
```python
# CURRENT (Hardcoded):
run_shuffles = False
n_shuf_per_subject = 5000

# REPLACE WITH:
run_shuffles = config['shuffles']['run_shuffles']
n_shuf_per_subject = config['shuffles']['n_shuffles_per_subject']
```
**Impact:** Controls whether to generate shuffles and how many

---

#### Line 725: `base_seed`
```python
# CURRENT (Hardcoded):
base_seed = 42

# REPLACE WITH:
base_seed = config['shuffles']['base_seed']
```
**Impact:** Critical for reproducibility

---

#### Line 719: `n_jobs` (CPU cores)
```python
# CURRENT (Hardcoded):
total_cpu_physical = psutil.cpu_count(logical=False)
n_jobs = total_cpu_physical - 2

# REPLACE WITH:
n_jobs = config['shuffles']['n_cores']
# Note: config_preprocessing.py already computes this
```
**Impact:** Parallelization efficiency

---

#### Lines 1154, 1422, 1904: `chunk_size`
```python
# CURRENT (Hardcoded):
chunk_size = 1000
all_chunked_ensembles = chunk_shuffles_by_subject(..., chunk_size=1000)

# REPLACE WITH:
chunk_size = config['shuffles']['chunk_size']
all_chunked_ensembles = chunk_shuffles_by_subject(
    ...,
    chunk_size=config['shuffles']['chunk_size']
)
```
**Impact:** Affects stability testing

---

### 3. Time-Series Parameters

#### Line 3421: `pre_frames` and `post_frames`
```python
# CURRENT (Hardcoded):
def extract_trial_windows(df, pre_frames=60, post_frames=300):
    ...

# REPLACE WITH:
def extract_trial_windows(df,
                         pre_frames=config['timeseries']['pre_frames'],
                         post_frames=config['timeseries']['post_frames']):
    ...

# OR at call site:
trial_windows = extract_trial_windows(
    df,
    pre_frames=config['timeseries']['pre_frames'],
    post_frames=config['timeseries']['post_frames']
)
```
**Impact:** Defines temporal analysis window

---

#### Lines 3558, 3592: `n_start_timebins_to_drop` and `n_end_timebins_to_drop`
```python
# CURRENT (Hardcoded):
n_end_timebins_to_drop = 0
n_start_timebins_to_drop = 8

# REPLACE WITH:
n_start_timebins_to_drop = config['timeseries']['n_start_timebins_to_drop']
n_end_timebins_to_drop = config['timeseries']['n_end_timebins_to_drop']
```
**Impact:** Affects time-series preprocessing

---

#### Line 3521: `n_sec_to_rotate`
```python
# CURRENT (Hardcoded):
n_sec_to_rotate = 0

# REPLACE WITH:
n_sec_to_rotate = config['timeseries']['n_sec_to_rotate']
```
**Impact:** Time-series shifting (currently disabled)

---

### 4. UMAP Parameters

#### Lines 4481-4482: UMAP parameters in function definition
```python
# CURRENT (Hardcoded):
def run_umap_with_stage_labels(...,
                                n_neighbors=15,
                                min_dist=0.1,
                                metric='hamming',
                                random_state=42):

# REPLACE WITH:
def run_umap_with_stage_labels(...,
                                n_neighbors=config['umap']['n_neighbors'],
                                min_dist=config['umap']['min_dist'],
                                metric=config['umap']['metric'],
                                random_state=config['umap']['random_state']):
```

#### Lines 4590, 4594: UMAP function calls
```python
# CURRENT (Hardcoded):
run_umap_with_stage_labels(..., n_neighbors=15, min_dist=0.2, metric=metric, random_state=42)

# REPLACE WITH:
run_umap_with_stage_labels(
    ...,
    n_neighbors=config['umap']['n_neighbors'],
    min_dist=config['umap']['min_dist'],  # Note: notebook uses 0.2, config has 0.1
    metric=config['umap']['metric'],
    random_state=config['umap']['random_state']
)
```
**⚠️ WARNING:** Notebook uses `min_dist=0.2` but config.yaml has `0.1` - need to decide which is correct!

---

## 🟡 Medium Priority (Should Replace)

### 5. Hardcoded Paths

#### Lines 156-158: Backup hardcoded paths
```python
# CURRENT (Hardcoded):
hardcode_results_dir = Path(r"C:\Users\13car\...\results")
hardcode_data_dir = Path(r'c:\\Users\\13car\\...\\data')
hardcode_source_dataset_location = Path(r"C:\Users\...\dataset_objects_24-Nov-2024_hour_19")

# ACTION:
# These appear to be backups - DELETE if config paths work correctly
# Or rename to backup_* and add comment explaining they're fallbacks
```

---

#### Line 124: `root_dir`
```python
# CURRENT (Hardcoded):
root_dir = Path(r'c:\\Users\\13car\\...\\code')

# REPLACE WITH:
root_dir = config['data']['root_dir']
# OR if always current directory:
root_dir = Path.cwd()
```

---

### 6. Hardcoded Result File Paths

#### Lines 2762, 2928: Ensemble file loading
```python
# CURRENT (Hardcoded - specific run dates):
dff_ens_path = results_dir / Path(r"dff_ensemble_detection_21-Nov-2025_5000 shuffles\dff_postoutcome_python_ensembles_5000_shuff_21-Nov-2025_.parquet")
spikes_ens_path = results_dir / Path(r"spikes_ensemble_detection_20-Nov-2025_5000 shuffles\spikes_postoutcome_python_ensembles_5000_shuff_20-Nov-2025_.parquet")

# REPLACE WITH (using manifest/log to find latest):
from run_manifest import load_manifest

# Find latest run from run_log.csv
run_log = pd.read_csv(results_dir / 'run_log.csv')
latest_dff_run = run_log[run_log['data_type'] == 'dff'].iloc[-1]
latest_spikes_run = run_log[run_log['data_type'] == 'spikes'].iloc[-1]

dff_ens_path = Path(latest_dff_run['manifest_path']).parent / 'enrichment_results.parquet'
spikes_ens_path = Path(latest_spikes_run['manifest_path']).parent / 'enrichment_results.parquet'
```
**Impact:** Currently requires manually updating paths after each run

---

## 🟢 Low Priority (Nice to Have)

### 7. Data Type Assignment

#### Line 1125, 2765, 2931: Redundant data_type assignment
```python
# CURRENT (Hardcoded):
all_ensembles['data_type'] = data_type_used  # data_type_used is from config, so this is OK
dff_ens['data_type'] = 'dff'  # Hardcoded string
spikes_ens['data_type'] = 'spikes'  # Hardcoded string

# REPLACE WITH (for consistency):
all_ensembles['data_type'] = config['data']['data_type_used']
dff_ens['data_type'] = 'dff'  # OK to keep as is (self-documenting)
spikes_ens['data_type'] = 'spikes'  # OK to keep as is (self-documenting)
```

---

### 8. Normalization Type for Spikes

#### Line 1903: Spikes normalization
```python
# CURRENT (Hardcoded):
raster_dataframes_spikes = transform_all_datasets(loaded_objects, datatype='raster', normalize='none')

# COULD ADD TO CONFIG:
# In config.yaml:
# spike_normalization: 'none'  # Spikes typically don't need normalization

# Then use:
raster_dataframes_spikes = transform_all_datasets(
    loaded_objects,
    datatype='spikes',
    normalize=config.get('spike_normalization', 'none')
)
```
**Note:** Currently fine as-is since spikes typically aren't normalized

---

## 📋 Function Default Parameters (Consider Updating)

### 9. Function Signatures with Hardcoded Defaults

These functions have hardcoded defaults that work, but could reference config:

#### `dataset_obj_to_df()` - Line 491
```python
# CURRENT:
def dataset_obj_to_df(dataset_obj, datatype:str = 'raster', normalize:str = 'none'):

# OPTION 1: Pass config to function
def dataset_obj_to_df(dataset_obj, config, datatype:str = None, normalize:str = None):
    if datatype is None:
        datatype = config['data']['data_type_used']
    if normalize is None:
        normalize = config['preprocessing']['normalization']

# OPTION 2: Keep defaults, override at call site (current approach - OK)
```

#### `transform_all_datasets()` - Line 568
```python
# CURRENT:
def transform_all_datasets(loaded_objects, datatype:str = 'raster', normalize:str = 'none'):

# SAME OPTIONS as above
```

**Recommendation:** Keep defaults as-is for backward compatibility, override at call sites

---

## ✅ Already Using Config (Verify Correct)

These are already pulling from config - verify they work:

```python
✓ Line 136: data_type = config['data']['data_type_used']
✓ Line 147: results_dir = config['data']['results_dir']
✓ Line 153: source_dataset_location = config['data']['source_dataset_location']
✓ Line 5057: 'source_data': str(config['data']['source_dataset_location'])
✓ Line 5079: db_path=results_dir / 'run_log.csv'
```

---

## 🎯 Recommended Replacement Order

### Phase 1: Critical Parameters (Do First)
1. ✅ `normalize = 'baseline_zscore'` → `config['preprocessing']['normalization']`
2. ✅ `n_shuf_per_subject = 5000` → `config['shuffles']['n_shuffles_per_subject']`
3. ✅ `base_seed = 42` → `config['shuffles']['base_seed']`
4. ✅ `drop_inactive_cells = True` → `config['preprocessing']['drop_inactive_cells']`
5. ✅ `sigma=1` → `config['preprocessing']['gaussian_sigma']`

### Phase 2: Shuffle & Analysis Parameters
6. ✅ `chunk_size = 1000` → `config['shuffles']['chunk_size']`
7. ✅ `n_jobs` → `config['shuffles']['n_cores']`
8. ✅ `run_shuffles = False` → `config['shuffles']['run_shuffles']`

### Phase 3: Time-Series Parameters
9. ✅ `pre_frames=60, post_frames=300` → config values
10. ✅ `n_start_timebins_to_drop = 8` → config value
11. ✅ `n_end_timebins_to_drop = 0` → config value

### Phase 4: UMAP Parameters
12. ✅ UMAP n_neighbors, min_dist, metric, random_state → config values
13. ⚠️ **DECIDE:** min_dist=0.1 or 0.2? (inconsistency between config and notebook)

### Phase 5: Cleanup
14. ✅ Remove hardcoded backup paths (or clearly mark as backups)
15. ✅ Replace hardcoded ensemble file paths with dynamic loading
16. ✅ Remove redundant `data_types = ['spikes', 'dff']` list

---

## ⚠️ Issues to Resolve

### 1. UMAP min_dist Inconsistency
- **config.yaml:** 0.1
- **Notebook:** 0.2 (lines 4590, 4594)
- **Function default:** 0.1 (line 4481)

**Action Required:** Decide which is correct and update accordingly

### 2. Hardcoded File Paths for Loading
Loading specific run results requires manual path updates. Should implement:
- Automatic latest run detection from run_log.csv
- Or: User-specified run_id to load

### 3. Data Type List Redundancy
```python
# Line 178-179
data_types = ['spikes', 'dff']
data_type_used = data_types[1]  # 'dff'

# Line 136
data_type = config['data']['data_type_used']  # 'dff'
```
**Action:** Remove lines 178-179, use only config value

---

## 🔧 Implementation Template

Create a cell at the top of the notebook:
```python
# Load all parameters from config
normalize = config['preprocessing']['normalization']
gaussian_sigma = config['preprocessing']['gaussian_sigma']
gaussian_truncate = config['preprocessing']['gaussian_truncate']
drop_inactive_cells = config['preprocessing']['drop_inactive_cells']
post_outcome_duration = config['preprocessing']['post_outcome_duration']

n_shuf_per_subject = config['shuffles']['n_shuffles_per_subject']
base_seed = config['shuffles']['base_seed']
chunk_size = config['shuffles']['chunk_size']
n_jobs = config['shuffles']['n_cores']
run_shuffles = config['shuffles']['run_shuffles']

pre_frames = config['timeseries']['pre_frames']
post_frames = config['timeseries']['post_frames']
n_start_timebins_to_drop = config['timeseries']['n_start_timebins_to_drop']
n_end_timebins_to_drop = config['timeseries']['n_end_timebins_to_drop']

umap_n_neighbors = config['umap']['n_neighbors']
umap_min_dist = config['umap']['min_dist']
umap_metric = config['umap']['metric']
umap_random_state = config['umap']['random_state']

print("✓ All parameters loaded from config")
```

Then use these variables throughout the notebook instead of hardcoded values.

---

## 📊 Summary Statistics

| Category | # Hardcoded | Priority |
|----------|-------------|----------|
| Data Processing | 5 | 🔴 Critical |
| Shuffle Generation | 4 | 🔴 Critical |
| Time-Series | 4 | 🔴 Critical |
| UMAP | 4 | 🟡 Medium |
| Paths | 5 | 🟡 Medium |
| Function Defaults | 2 | 🟢 Low |
| **Total** | **24** | Mixed |

**Estimated Time to Replace:** 2-3 hours
**Risk Level:** Low (config system already tested)
**Benefit:** Full reproducibility and parameter tracking

---

**Created:** 2025-11-28
**For:** dlx56_mPFC_1p_SohalLab preprocessing pipeline
**Status:** Ready for implementation
