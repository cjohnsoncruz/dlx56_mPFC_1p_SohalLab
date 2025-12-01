# preprocessing_utils.py Quick Start Guide

**Module:** [preprocessing_utils.py](preprocessing_utils.py)
**Documentation:** [../PREPROCESSING_UTILS_DESIGN.md](../PREPROCESSING_UTILS_DESIGN.md)

---

## Quick Import

```python
import sys
sys.path.append('code/')

from preprocessing_utils import (
    # MATLAB conversion
    dataset_obj_to_df,
    transform_all_datasets,
    # File I/O
    read_shuffle_parquet_from_folder,
    # Statistics
    get_intercol_corrs,
    # Time-series
    extract_trial_windows,
    pivot_trial_windows,
    # Metadata
    get_first_active_stage,
    get_genotype,
    get_session_type,
    get_subject_metadata
)
```

---

## Common Use Cases

### 1. Load MATLAB Data

```python
from matlab_obj_to_python import load_matlab_object
from preprocessing_utils import dataset_obj_to_df

dataset = load_matlab_object('dataset.mat')
df = dataset_obj_to_df(
    dataset,
    datatype='dff',
    normalize='baseline_zscore',
    gaussian_sigma=1.0
)
```

---

### 2. Process Multiple Subjects

```python
from preprocessing_utils import transform_all_datasets

all_dfs = transform_all_datasets(
    loaded_objects,
    datatype='dff',
    normalize='baseline_zscore',
    gaussian_sigma=1.0,
    drop_inactive_cells=True
)

# Access by subject name
subject_df = all_dfs['10_3_HET_RS1']
```

---

### 3. Extract Trial Windows

```python
from preprocessing_utils import extract_trial_windows, pivot_trial_windows

# Step 1: Extract windows (long format)
windowed = extract_trial_windows(
    df,
    pre_frames=60,   # 60 frames before outcome
    post_frames=300  # 300 frames after outcome
)

# Step 2: Pivot to trial-cell format (wide format)
pivoted = pivot_trial_windows(windowed)

# Result: each row = one neuron × one trial
# Columns: -f_60, -f_59, ..., -f_1, f_1, f_2, ..., f_300
```

---

### 4. Compute Correlations

```python
from preprocessing_utils import get_intercol_corrs

stages = ['Early_IA_Error', 'Late_IA', 'Early_RS_Error', 'Late_RS']
corrs = get_intercol_corrs(
    df,
    stage_names=stages,
    suffix1='_dff',
    suffix2='_spikes'
)
```

---

### 5. Extract Metadata

```python
from preprocessing_utils import get_subject_metadata, get_first_active_stage

# Parse subject name
metadata = get_subject_metadata('10_3_HET_RS1')
# {'genotype': 'HET', 'session_type': 'RS'}

# Find first enrichment stage
ensemble_df['first_active'] = ensemble_df.apply(
    get_first_active_stage,
    axis=1,
    stage_order=['Early_IA', 'Late_IA', 'Early_RS', 'Late_RS']
)
```

---

## Integration with Config System

```python
from config_preprocessing import load_config
from preprocessing_utils import transform_all_datasets, extract_trial_windows

# Load config
config = load_config('config.yaml')

# Use config parameters
all_dfs = transform_all_datasets(
    loaded_objects,
    datatype=config['data']['data_type_used'],
    normalize=config['preprocessing']['normalization'],
    gaussian_sigma=config['preprocessing']['gaussian_sigma']
)

windowed = extract_trial_windows(
    df,
    pre_frames=config['timeseries']['pre_frames'],
    post_frames=config['timeseries']['post_frames']
)
```

---

## Function Reference

### MATLAB Conversion

| Function | Purpose | Key Parameters |
|----------|---------|----------------|
| `dataset_obj_to_df()` | Convert MATLAB object to DataFrame | `datatype`, `normalize`, `gaussian_sigma` |
| `transform_all_datasets()` | Batch convert multiple subjects | Same as above |

---

### File I/O

| Function | Purpose | Key Parameters |
|----------|---------|----------------|
| `read_shuffle_parquet_from_folder()` | Load shuffle parquet files | `shuffle_storage_folder` |

---

### Statistics

| Function | Purpose | Key Parameters |
|----------|---------|----------------|
| `get_intercol_corrs()` | Correlate column pairs by stage | `stage_names`, `suffix1`, `suffix2` |

---

### Time-Series

| Function | Purpose | Key Parameters |
|----------|---------|----------------|
| `extract_trial_windows()` | Extract trial frames around outcome | `pre_frames`, `post_frames` |
| `pivot_trial_windows()` | Reshape to trial-cell format | `samples_col`, `frame_prefix` |

---

### Metadata

| Function | Purpose | Key Parameters |
|----------|---------|----------------|
| `get_first_active_stage()` | Find first enrichment stage | `stage_order`, `non_enriched_label` |
| `get_genotype()` | Extract genotype from name | `subject_name` |
| `get_session_type()` | Extract session type from name | `subject_name` |
| `get_subject_metadata()` | Extract all metadata | `subject_name` |

---

## Replacing Notebook Code

### Before (Hardcoded in Notebook)

```python
# Cell in notebook
def dataset_obj_to_df(dataset_obj, datatype='raster', normalize='none'):
    # ... 80 lines of code ...
    return raster_df

raster_df = dataset_obj_to_df(obj, datatype='dff', normalize='baseline_zscore')
```

---

### After (Using preprocessing_utils)

```python
# Cell in notebook
from preprocessing_utils import dataset_obj_to_df
from config_preprocessing import load_config

config = load_config('config.yaml')

raster_df = dataset_obj_to_df(
    obj,
    datatype=config['data']['data_type_used'],
    normalize=config['preprocessing']['normalization'],
    gaussian_sigma=config['preprocessing']['gaussian_sigma']
)
```

**Benefits:**
- ✅ Removes 80 lines from notebook
- ✅ Function is tested and reusable
- ✅ Parameters come from config (reproducible)
- ✅ Easier to maintain and debug

---

## Next Steps

1. **Update notebook** to use preprocessing_utils functions
2. **Remove duplicate code** from notebook cells
3. **Create tests** for preprocessing_utils (see [PREPROCESSING_UTILS_DESIGN.md](../PREPROCESSING_UTILS_DESIGN.md#testing-strategy))
4. **Replace hardcoded parameters** with config values (see [HARDCODED_PARAMETERS_TO_REPLACE.md](../HARDCODED_PARAMETERS_TO_REPLACE.md))

---

## Support

- **Full documentation:** [PREPROCESSING_UTILS_DESIGN.md](../PREPROCESSING_UTILS_DESIGN.md)
- **Config system:** [README_CONFIG_AND_MANIFEST.md](../README_CONFIG_AND_MANIFEST.md)
- **Design principles:** See "Underlying Principles" section in PREPROCESSING_UTILS_DESIGN.md

