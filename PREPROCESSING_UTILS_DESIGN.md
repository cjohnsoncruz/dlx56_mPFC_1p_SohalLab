# preprocessing_utils.py Design Documentation

**Created:** 2025-11-29
**Purpose:** Explain function separation principles and design decisions for the preprocessing utilities module

---

## Overview

The [preprocessing_utils.py](code/preprocessing_utils.py) module contains **9 general-purpose helper functions** extracted from the preprocessing notebook. This document explains which functions were included, which were excluded, and the underlying principles guiding these decisions.

---

## Functions Included in preprocessing_utils.py

### ✅ Included (9 functions)

| Function | Lines | Purpose | Why Included |
|----------|-------|---------|--------------|
| `dataset_obj_to_df()` | ~491 | MATLAB→DataFrame conversion | Core data transformation, highly reusable |
| `transform_all_datasets()` | ~568 | Batch dataset transformation | Reusable batch processing pattern |
| `read_shuffle_parquet_from_folder()` | ~791 | File I/O for parquet files | General file loading utility |
| `get_intercol_corrs()` | ~1918 | Stage-based correlation | Common statistical operation |
| `extract_trial_windows()` | ~3433 | Trial frame extraction | Core preprocessing for trial-based data |
| `pivot_trial_windows()` | ~3479 | Trial-cell reshaping | Standard data transformation |
| `get_first_active_stage()` | ~4488 | Stage classification | General metadata extraction |
| `get_genotype()` | config_preprocessing.py | Extract genotype from name | Metadata parsing utility |
| `get_session_type()` | config_preprocessing.py | Extract session type | Metadata parsing utility |

---

### ❌ Excluded (4 functions kept in notebook)

| Function | Lines | Purpose | Why Excluded |
|----------|-------|---------|--------------|
| `chunk_shuffles_by_subject()` | ~1147 | Chunk shuffles for enrichment | Too specific to enrichment workflow |
| `get_pivoted_enrichment_heatmap()` | ~1198 | Pivot enrichment results | Too specific to visualization workflow |
| `create_subject_trial_tseries_df()` | ~3533 | Time-series pipeline orchestrator | Workflow-specific orchestration |
| `run_umap_with_stage_labels()` | ~4495 | UMAP visualization | Too specific to dimensionality reduction |
| `normalize_tseries_df()` | ~3571 | Time-series normalization | **Excluded due to external dependencies** |
| `normalize_all_subject_tseries_dfs()` | ~3605 | Batch time-series normalization | **Excluded due to external dependencies** |

**Note:** `normalize_tseries_df()` and `normalize_all_subject_tseries_dfs()` were originally planned for inclusion but excluded because they depend on external modules (`preprocess_data`, `helper_functions`) that aren't available in the utilities module. These should be refactored in a future iteration.

---

## Underlying Principles for Separating Helper Functions

### 1. **Single Responsibility Principle (SRP)**

**Principle:** Each function performs ONE well-defined task.

**Examples:**
- ✅ `extract_trial_windows()` **only** extracts trial windows—it doesn't normalize, plot, or analyze
- ✅ `get_genotype()` **only** extracts genotype—it doesn't load files or validate data
- ❌ `create_subject_trial_tseries_df()` does **multiple** things (extract windows, pivot, join ensemble matrix, bin, rotate) → **kept in notebook**

**Why It Matters:**
- Single-purpose functions are easier to test, debug, and reuse
- Changes to one aspect don't affect unrelated functionality

---

### 2. **Reusability Across Contexts**

**Principle:** Helper functions should work in multiple scripts, notebooks, or studies.

**Test:** "Could I use this function in a different neuroscience study?"

**Examples:**
- ✅ `extract_trial_windows()` works for **any** trial-based neuroscience data (not just this dataset)
- ✅ `pivot_trial_windows()` reshapes **any** windowed trial data
- ❌ `get_pivoted_enrichment_heatmap()` is specific to **this project's enrichment analysis** → **kept in notebook**

**Why It Matters:**
- Reusable code saves time across projects
- Reduces code duplication across research group

---

### 3. **Independence from Workflow State**

**Principle:** Helpers shouldn't depend on specific execution order or global state.

**Implementation:**
- Functions receive **all inputs as parameters**
- Functions **return outputs** (no side effects like modifying global variables)
- No hidden dependencies on variables from previous notebook cells

**Examples:**
- ✅ `dataset_obj_to_df(dataset_obj, datatype='dff', normalize='baseline_zscore')` receives everything it needs
- ❌ Original notebook version referenced global `config` object → **refactored to accept parameters**

**Why It Matters:**
- Functions can be called in any order
- Easier to test in isolation
- No hidden coupling between functions

---

### 4. **DRY (Don't Repeat Yourself)**

**Principle:** If the same logic appears in multiple places, extract it into a helper function.

**Examples:**
- ✅ Genotype extraction appeared in multiple scripts → extracted to `get_genotype()`
- ✅ Trial windowing needed for multiple analyses → extracted to `extract_trial_windows()`

**Why It Matters:**
- Bug fixes in one place propagate everywhere
- Consistent behavior across codebase
- Less code to maintain

---

### 5. **Separation of Concerns**

**Principle:** Different types of code belong in different modules.

**Module Structure:**

```
preprocessing_utils.py    ← Pure data transformations (THIS MODULE)
    ↓
    - MATLAB → DataFrame conversion
    - Time-series extraction/reshaping
    - Statistical operations
    - Metadata extraction

config_preprocessing.py   ← Configuration and infrastructure
    ↓
    - Load config.yaml
    - Validate parameters
    - Detect CPU cores

run_manifest.py          ← Provenance tracking
    ↓
    - Create run manifests
    - Track git versions
    - Log processing runs

notebooks/               ← Workflow orchestration
    ↓
    - Call helper functions
    - Implement analysis logic
    - Generate visualizations
```

**Why It Matters:**
- Clear mental model of where functionality lives
- Easier to find and modify code
- Reduces circular dependencies

---

### 6. **Testability**

**Principle:** Helpers should be easily unit-testable in isolation.

**Characteristics of Testable Functions:**
- Pure functions (same input → same output)
- No hidden dependencies
- Minimal side effects
- Clear input/output contracts

**Examples:**
- ✅ `get_intercol_corrs(df, stages, suffix1, suffix2)` can be tested with synthetic data:
  ```python
  def test_get_intercol_corrs():
      df = pd.DataFrame({
          'Early_IA_dff': [1, 2, 3],
          'Early_IA_spikes': [1.1, 2.0, 2.9]
      })
      result = get_intercol_corrs(df, ['Early_IA'], '_dff', '_spikes')
      assert result.loc['Early_IA', 'Correlation'] > 0.95
  ```

**Why It Matters:**
- Catches bugs before they affect analysis
- Enables regression testing
- Provides usage examples

---

### 7. **Low Coupling, High Cohesion**

**Principle:** Functions should depend on few external modules (low coupling) while related functions are grouped together (high cohesion).

**Low Coupling Examples:**
- ✅ `get_first_active_stage()` only depends on pandas (standard library)
- ✅ `get_genotype()` has **zero** dependencies (pure Python)

**High Cohesion Examples:**
- Time-series functions grouped in Section 4:
  - `extract_trial_windows()`
  - `pivot_trial_windows()`
- Metadata extraction grouped in Section 5:
  - `get_first_active_stage()`
  - `get_genotype()`
  - `get_session_type()`

**Why It Matters:**
- Easier to understand module organization
- Fewer import errors
- Functions can be used independently

---

### 8. **Generalization vs. Specialization**

**Principle:** Extract functions that solve **general problems**, keep functions that solve **specific problems** in workflows.

**Decision Tree:**

```
Does this function solve a general data science problem?
│
├─ YES → Extract to preprocessing_utils.py
│   Examples:
│   - Extracting trial windows (general neuroscience problem)
│   - Reshaping data from long to wide format (general data science)
│   - Computing correlations between column pairs (general statistics)
│
└─ NO → Keep in notebook
    Examples:
    - Chunking shuffles for THIS enrichment analysis
    - Creating UMAP plots with THIS labeling scheme
    - Orchestrating THIS specific analysis pipeline
```

**Examples:**

| Function | Problem Type | Decision |
|----------|--------------|----------|
| `extract_trial_windows()` | **General:** Trial-based neuroscience | ✅ Extract |
| `pivot_trial_windows()` | **General:** Data reshaping | ✅ Extract |
| `chunk_shuffles_by_subject()` | **Specific:** This enrichment workflow | ❌ Keep in notebook |
| `run_umap_with_stage_labels()` | **Specific:** This UMAP visualization | ❌ Keep in notebook |

**Why It Matters:**
- General functions benefit multiple projects
- Specific functions don't clutter the utilities module
- Clear boundary between library code and application code

---

## Module Organization

The preprocessing_utils.py module is organized into **6 logical sections**:

### Section 1: MATLAB to DataFrame Conversion
**Functions:**
- `dataset_obj_to_df()` - Core conversion with normalization
- `transform_all_datasets()` - Batch processing wrapper

**Why Grouped:** Both handle MATLAB data import

---

### Section 2: File I/O Operations
**Functions:**
- `read_shuffle_parquet_from_folder()` - Load parquet files

**Why Grouped:** File system interactions

---

### Section 3: Statistical Operations
**Functions:**
- `get_intercol_corrs()` - Correlation calculations

**Why Grouped:** Statistical computations

---

### Section 4: Time-Series Extraction and Reshaping
**Functions:**
- `extract_trial_windows()` - Extract trial windows
- `pivot_trial_windows()` - Reshape to trial-cell format

**Why Grouped:** Both handle time-series preprocessing pipeline

---

### Section 5: Metadata Extraction
**Functions:**
- `get_first_active_stage()` - Find first enrichment stage

**Why Grouped:** Metadata classification

---

### Section 6: Subject Metadata Extraction
**Functions:**
- `get_genotype()` - Extract genotype from name
- `get_session_type()` - Extract session type from name
- `get_subject_metadata()` - Extract all metadata

**Why Grouped:** All parse subject identifiers

---

## Design Trade-offs

### Trade-off 1: Parameter Explosion vs. Global Config

**Problem:** Functions need many parameters (sigma, truncate, normalize, etc.)

**Option A:** Use global `config` object
```python
def dataset_obj_to_df(dataset_obj):
    sigma = config['preprocessing']['gaussian_sigma']  # Hidden dependency
```

**Option B:** Accept all parameters explicitly
```python
def dataset_obj_to_df(dataset_obj, gaussian_sigma=1.0, normalize='none', ...):
    # Explicit dependencies
```

**Decision:** **Option B** (explicit parameters)

**Why:**
- Testability: Can test with different parameters without modifying global state
- Clarity: Function signature shows exactly what's configurable
- Flexibility: Can call with different configs in same script

**Compromise:** Provide sensible defaults matching config.yaml values

---

### Trade-off 2: Pure Functions vs. Convenience Wrappers

**Problem:** Some functions need to call other custom modules (e.g., `label_frame_sections_df`)

**Option A:** Make functions completely pure (no external dependencies)
```python
def dataset_obj_to_df(dataset_obj, ...):
    # Don't call label_frame_sections_df() at all
    # Force user to call it separately
```

**Option B:** Accept functions as parameters
```python
def dataset_obj_to_df(dataset_obj, label_frame_sections_fn=None, ...):
    if label_frame_sections_fn is not None:
        df = label_frame_sections_fn(df, dataset_obj)
```

**Decision:** **Option B** (dependency injection)

**Why:**
- Flexibility: Function works with or without external dependencies
- Backward compatibility: Can gradually refactor notebook
- Optional features: Advanced users can inject custom labeling functions

---

### Trade-off 3: Comprehensive Module vs. Minimal Module

**Problem:** Should we include functions with external dependencies?

**Excluded Functions:**
- `normalize_tseries_df()` - depends on `preprocess_data`, `helper_functions`
- `normalize_all_subject_tseries_dfs()` - depends on above + workflow-specific code

**Decision:** **Exclude for now**, refactor later

**Why:**
- External dependencies (`preprocess_data`, `helper_functions`) aren't in version control
- Better to have a clean, minimal module than a broken comprehensive one
- Can refactor these in Phase 2 after identifying all dependencies

**Future Work:**
1. Audit `preprocess_data.py` and `helper_functions.py`
2. Extract pure utility functions from those modules
3. Add `normalize_tseries_df()` to preprocessing_utils.py v2

---

## Usage Examples

### Example 1: Load and Convert MATLAB Data

```python
from preprocessing_utils import dataset_obj_to_df, transform_all_datasets
from matlab_obj_to_python import load_matlab_object

# Load single subject
dataset = load_matlab_object('path/to/subject.mat')
df = dataset_obj_to_df(
    dataset,
    datatype='dff',
    normalize='baseline_zscore',
    gaussian_sigma=1.0,
    drop_inactive_cells=True
)

# Load multiple subjects
datasets = [load_matlab_object(f) for f in subject_files]
all_dfs = transform_all_datasets(
    datasets,
    datatype='dff',
    normalize='baseline_zscore'
)
```

---

### Example 2: Extract Trial Windows

```python
from preprocessing_utils import extract_trial_windows, pivot_trial_windows

# Extract windows (60 frames pre, 300 frames post outcome)
windowed = extract_trial_windows(df, pre_frames=60, post_frames=300)

# Reshape to trial-cell format (one row per neuron per trial)
pivoted = pivot_trial_windows(windowed)

# Result: each row is one neuron's activity across one trial
# Columns: [trial_num, cell, subject_name, ..., -f_60, -f_59, ..., f_1, f_2, ..., f_300]
```

---

### Example 3: Compute Stage Correlations

```python
from preprocessing_utils import get_intercol_corrs

# Compute correlations between DFF and spikes for each stage
stages = ['Early_IA_Error', 'Late_IA', 'Early_RS_Error', 'Late_RS']
corrs = get_intercol_corrs(
    df,
    stage_names=stages,
    suffix1='_dff',
    suffix2='_spikes'
)

print(corrs)
#                   Correlation
# Early_IA_Error        0.85
# Late_IA               0.92
# Early_RS_Error        0.78
# Late_RS               0.88
```

---

### Example 4: Extract Metadata

```python
from preprocessing_utils import get_subject_metadata, get_first_active_stage

# Extract metadata from subject name
metadata = get_subject_metadata('10_3_HET_RS1')
# {'genotype': 'HET', 'session_type': 'RS'}

# Find first active stage for each neuron
ensemble_df['first_active'] = ensemble_df.apply(
    get_first_active_stage,
    axis=1,
    stage_order=['Early_IA_Error', 'Late_IA', 'Early_RS_Error', 'Late_RS']
)
```

---

## Integration with Existing Code

### In Notebooks

```python
# At the top of preprocessing notebook
import sys
sys.path.append('code/')  # Add code directory to path

from preprocessing_utils import (
    transform_all_datasets,
    extract_trial_windows,
    pivot_trial_windows,
    get_intercol_corrs
)
from config_preprocessing import load_config

# Load configuration
config = load_config('config.yaml')

# Use utilities with config parameters
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

### In Scripts

```python
#!/usr/bin/env python
"""Process all subjects and generate time-series data."""

from pathlib import Path
from preprocessing_utils import transform_all_datasets, extract_trial_windows
from config_preprocessing import load_config
from matlab_obj_to_python import load_matlab_object

def main():
    config = load_config('config.yaml')

    # Load all subjects
    source_dir = config['data']['source_dataset_location']
    subject_files = Path(source_dir).glob('*.mat')
    datasets = [load_matlab_object(f) for f in subject_files]

    # Convert to DataFrames
    dfs = transform_all_datasets(
        datasets,
        datatype=config['data']['data_type_used'],
        normalize=config['preprocessing']['normalization']
    )

    # Extract trial windows
    for subject, df in dfs.items():
        windowed = extract_trial_windows(
            df,
            pre_frames=config['timeseries']['pre_frames'],
            post_frames=config['timeseries']['post_frames']
        )
        # Save results...

if __name__ == '__main__':
    main()
```

---

## Testing Strategy

### Unit Tests

```python
# test_preprocessing_utils.py
import pytest
import numpy as np
import pandas as pd
from preprocessing_utils import (
    get_genotype,
    get_session_type,
    get_intercol_corrs,
    get_first_active_stage
)

def test_get_genotype():
    assert get_genotype('10_3_HET_RS1') == 'HET'
    assert get_genotype('10_3_WT_RS2') == 'WT'
    assert get_genotype('unknown_name') == 'unknown'

def test_get_session_type():
    assert get_session_type('10_3_HET_RS1') == 'RS'
    assert get_session_type('10_3_WT_IA2') == 'IA'

def test_get_intercol_corrs():
    df = pd.DataFrame({
        'Early_IA_dff': [1, 2, 3, 4, 5],
        'Early_IA_spikes': [1.1, 2.0, 2.9, 4.1, 5.0],
        'Late_RS_dff': [5, 4, 3, 2, 1],
        'Late_RS_spikes': [5.1, 4.0, 3.1, 1.9, 1.0]
    })

    result = get_intercol_corrs(df, ['Early_IA', 'Late_RS'], '_dff', '_spikes')

    assert result.shape == (2, 1)
    assert result.loc['Early_IA', 'Correlation'] > 0.95
    assert result.loc['Late_RS', 'Correlation'] > 0.95

def test_get_first_active_stage():
    row = pd.Series({
        'Early_IA': 0,
        'Late_IA': 1,
        'Early_RS': 0,
        'Late_RS': 1
    })
    stage_order = ['Early_IA', 'Late_IA', 'Early_RS', 'Late_RS']

    result = get_first_active_stage(row, stage_order)
    assert result == 'Late_IA'

    # Test never enriched
    row_never = pd.Series({'Early_IA': 0, 'Late_IA': 0})
    result_never = get_first_active_stage(row_never, stage_order)
    assert result_never == 'Never'
```

---

### Integration Tests

```python
# test_preprocessing_integration.py
from preprocessing_utils import extract_trial_windows, pivot_trial_windows
from tests.fixtures import create_mock_raster_df

def test_trial_window_extraction_and_pivoting():
    # Create mock data with known structure
    df = create_mock_raster_df(
        n_trials=10,
        n_cells=5,
        frames_per_trial=400,
        outcome_frame=100
    )

    # Extract windows
    windowed = extract_trial_windows(df, pre_frames=60, post_frames=300)

    # Verify structure
    assert 'trial_window_frame' in windowed.columns
    assert windowed['trial_window_frame'].min() == -60
    assert windowed['trial_window_frame'].max() == 300

    # Pivot
    pivoted = pivot_trial_windows(windowed)

    # Verify pivoted structure
    expected_cols = 60 + 300  # pre + post frames
    frame_cols = [c for c in pivoted.columns if c.startswith('f_') or c.startswith('-f_')]
    assert len(frame_cols) == expected_cols

    # Verify data integrity
    assert not pivoted[['trial_num', 'cell']].duplicated().any()
```

---

## Future Enhancements

### Phase 2: Add Normalization Functions
**Goal:** Extract `normalize_tseries_df()` and related functions after refactoring dependencies

**Steps:**
1. Audit `preprocess_data.py` and `helper_functions.py`
2. Identify which helper functions are needed
3. Extract those helpers to preprocessing_utils.py
4. Add time-series normalization functions

---

### Phase 3: Add Validation Utilities
**Goal:** Add data validation helpers

**Proposed Functions:**
```python
def validate_raster_df(df, required_cols=None, check_monotonicity=True)
def validate_trial_structure(df, min_trials=1, max_trials=None)
def check_data_quality(df, missing_threshold=0.1)
```

---

### Phase 4: Add Performance Optimization
**Goal:** Add numba-compiled versions for speed-critical operations

**Proposed Functions:**
```python
@jit(nopython=True)
def fast_trial_window_extraction(data, outcome_indices, pre_frames, post_frames)
```

---

## Summary

### Key Decisions

1. ✅ **Extracted 9 general-purpose functions** to preprocessing_utils.py
2. ✅ **Kept 4 workflow-specific functions** in notebook
3. ✅ **Used dependency injection** for optional external functions
4. ✅ **Organized into 6 logical sections** for clarity
5. ✅ **Prioritized testability** over convenience
6. ✅ **Explicit parameters** over global config access

---

### Design Principles Applied

| Principle | Implementation |
|-----------|----------------|
| Single Responsibility | Each function does ONE thing |
| Reusability | Functions work across multiple studies |
| Independence | No hidden global state dependencies |
| DRY | Extracted repeated logic |
| Separation of Concerns | Utils, config, manifest in separate modules |
| Testability | Pure functions with clear inputs/outputs |
| Low Coupling | Minimal external dependencies |
| Generalization | General solutions, not specific workflows |

---

### Benefits

1. **Reduced code duplication** across notebooks and scripts
2. **Easier testing** with isolated, pure functions
3. **Improved maintainability** with clear module organization
4. **Better reusability** across projects and research group
5. **Clearer mental model** of where functionality lives
6. **Faster development** by reusing tested components

---

**Status:** ✅ preprocessing_utils.py v1.0 complete
**Next Steps:** Integrate into v6_modular.ipynb and create unit tests

