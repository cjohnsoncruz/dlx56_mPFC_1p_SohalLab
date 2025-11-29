# Configuration Systems Comparison

This document explains the difference between the two configuration systems in this codebase.

---

## Overview: Two Separate Configuration Systems

### 1. **`analysis_config.yaml`** (Existing - Downstream Analysis)
**Purpose:** Configuration for **downstream statistical analyses** and **ensemble detection methods**

### 2. **`config.yaml`** (New - Data Preprocessing)
**Purpose:** Configuration for **data preprocessing pipeline** (loading, shuffling, time-series generation)

---

## Detailed Comparison

| Aspect | `analysis_config.yaml` (Existing) | `config.yaml` (New) |
|--------|-----------------------------------|---------------------|
| **When Used** | Downstream analysis (after preprocessing) | During preprocessing pipeline |
| **Loader** | `analysis_config_loader.py` | `config_preprocessing.py` |
| **Data Structure** | Python dataclass (`AnalysisConfig`) | Dictionary |
| **Primary Focus** | Analysis methods and statistical parameters | Data processing and infrastructure |

---

## `analysis_config.yaml` - Downstream Analysis Configuration

### What It Contains

#### 1. **Shuffle/Statistical Parameters**
```yaml
num_shuffles: 1000              # For statistical testing
percentile: 95.0                # Significance threshold
threshold_with_shuffle: true
```

#### 2. **Trial Section Names** (Analysis Labels)
```yaml
trial_section_names:
  - pre_outcome
  - post_outcome
  - ITI
```

#### 3. **Task Phase Definitions** (Scientific Categorization)
```yaml
task_phase_names:
  - Early_IA_Error     # Initial Acquisition, Early trials, Error
  - Early_IA_Correct   # Initial Acquisition, Early trials, Correct
  - Late_IA            # Initial Acquisition, Late trials
  - Early_RS_Error     # Reversal Shifting, Early trials, Error
  - Early_RS_Correct   # Reversal Shifting, Early trials, Correct
  - Late_RS            # Reversal Shifting, Late trials

simple_phase_names:
  - IA_Error
  - IA_Correct
  - RS_Error
  - RS_Correct
```

#### 4. **Phase Division Criteria** (How to Split Data)
```yaml
early_division_criteria_types:
  - count
  - first_2
early_criteria_type: count
early_criteria_value: 5        # First 5 trials = "early"
```

#### 5. **Time-Series Analysis Parameters**
```yaml
time_series_bin_size: 0.25           # Temporal binning for analysis
corr_time_series_bin_size: 0.5       # Bin size for correlation analysis
seconds_before_post_to_keep: 5
```

#### 6. **Spike Modulation Detection** (Neuroscience-Specific)
```yaml
final_thresh: 2.5
final_thresh2: 12.5
final_thresh3: 20
final_thresh4_abs: 0.01

drop_low_value_peak_events: false
cutoff_filter: bimodality
peak_event_cutoff_percentile: 1
```

#### 7. **Feature Comparison Types**
```yaml
feature_type_names:
  - correct_error      # Compare correct vs error trials
  - IA_RS             # Compare Initial Acquisition vs Reversal Shifting
  - task_phase        # Compare across all task phases
```

#### 8. **Data Processing Flags**
```yaml
use_dff_not_spikes: false            # Use delta F/F or spikes
zscore_dff: false
zscore_dff_to_baseline: false
drop_low_act_cell_in_dataset_obj: false
```

### Who Uses It
- **Ensemble detection algorithms**
- **Statistical comparison functions**
- **Phase-based analysis scripts**
- **Correlation analysis code**

### Example Usage
```python
from analysis_config_loader import load_analysis_config

# Load analysis configuration
analysis_cfg = load_analysis_config('analysis_config.yaml')

# Access task phase names
print(analysis_cfg.task_phase_names)
# ['Early_IA_Error', 'Early_IA_Correct', ...]

# Get comparison pairs (automatically computed)
print(analysis_cfg.all_interphase_comparisons)
# [('Early_IA_Error', 'Early_IA_Correct'), ...]

# Use in analysis
if analysis_cfg.threshold_with_shuffle:
    threshold = np.percentile(shuffle_dist, analysis_cfg.percentile)
```

---

## `config.yaml` - Preprocessing Pipeline Configuration

### What It Contains

#### 1. **Data Paths and Locations**
```yaml
data:
  source_dataset_location: "path/to/dataset_objects_24-Nov-2024_hour_19"
  results_dir: "path/to/results"
  data_type_used: 'dff'
```

#### 2. **Preprocessing Parameters**
```yaml
preprocessing:
  gaussian_sigma: 1                    # Smoothing parameter
  normalization: 'baseline_zscore'     # How to normalize data
  post_outcome_duration: 15            # Truncation time (seconds)
  drop_inactive_cells: true            # Filter out inactive neurons
```

#### 3. **Shuffle Generation Parameters**
```yaml
shuffles:
  n_shuffles_per_subject: 5000         # Number of circular shuffles
  base_seed: 42                        # Random seed for reproducibility
  n_cores: 14                          # Parallel processing cores
  chunk_size: 1000                     # Shuffles per chunk
```

#### 4. **Time-Series Generation Parameters**
```yaml
timeseries:
  fps: 20                              # Frame rate (imaging)
  bin_size: 0.25                       # Temporal bin size
  pre_frames: 60                       # Frames before outcome
  post_frames: 300                     # Frames after outcome
  n_start_timebins_to_drop: 8         # Drop first N bins
  n_end_timebins_to_drop: 0           # Drop last N bins
```

#### 5. **UMAP Visualization Parameters**
```yaml
umap:
  n_neighbors: 15
  min_dist: 0.1
  metric: 'hamming'
  random_state: 42
```

#### 6. **Subject List** (Infrastructure)
```yaml
subjects:
  - "10_3_HET_RS1"
  - "10_3_HET_RS2"
  # ... all 35 subjects
```

### Who Uses It
- **Data loading scripts** (load_matlab_data.py)
- **Shuffle generation** (generate_shuffles.py)
- **Time-series creation** (generate_timeseries.py)
- **UMAP analysis** (run_umap_analysis.py)
- **Preprocessing notebooks**

### Example Usage
```python
from config_preprocessing import load_config, get_subject_list

# Load preprocessing configuration
config = load_config('config.yaml')

# Access preprocessing parameters
sigma = config['preprocessing']['gaussian_sigma']
normalization = config['preprocessing']['normalization']

# Get subject list
subjects = get_subject_list(config)

# Use in preprocessing
smoothed_data = gaussian_filter1d(data, sigma=sigma)
```

---

## Key Differences

### Scope
- **`analysis_config.yaml`**: What to analyze, how to categorize, what comparisons to make
- **`config.yaml`**: What data to load, how to process it, where to save it

### Abstraction Level
- **`analysis_config.yaml`**: High-level scientific concepts (task phases, trial types)
- **`config.yaml`**: Low-level infrastructure (paths, cores, random seeds)

### When They're Used
- **`analysis_config.yaml`**: During ensemble detection, statistical testing, comparisons
- **`config.yaml`**: During data loading, shuffling, normalization, file I/O

### Mutability
- **`analysis_config.yaml`**: Changes less often (defined by experimental design)
- **`config.yaml`**: Changes more often (different runs, parameter sweeps)

---

## How They Work Together

### Workflow

```
1. DATA PREPROCESSING (uses config.yaml)
   ↓
   - Load raw MATLAB data
   - Apply normalization (baseline_zscore)
   - Generate shuffles (5000 per subject)
   - Create time-series (0.25s bins)
   ↓
   Outputs: Preprocessed data files

2. STATISTICAL ANALYSIS (uses analysis_config.yaml)
   ↓
   - Load preprocessed data
   - Divide trials into phases (Early_IA_Error, etc.)
   - Run ensemble detection (using shuffle threshold)
   - Compute inter-phase comparisons
   ↓
   Outputs: Ensemble membership, statistics
```

### Example: Complete Pipeline

```python
# STEP 1: Preprocessing (uses config.yaml)
from config_preprocessing import load_config
config = load_config('config.yaml')

# Load and normalize data
raster_data = load_and_normalize(
    subjects=config['subjects'],
    normalization=config['preprocessing']['normalization']
)

# Generate shuffles
shuffles = generate_shuffles(
    raster_data,
    n_shuffles=config['shuffles']['n_shuffles_per_subject'],
    seed=config['shuffles']['base_seed']
)

# STEP 2: Analysis (uses analysis_config.yaml)
from analysis_config_loader import load_analysis_config
analysis_cfg = load_analysis_config('analysis_config.yaml')

# Detect ensembles with statistical thresholding
ensembles = detect_ensembles(
    raster_data,
    shuffles,
    percentile=analysis_cfg.percentile,
    threshold_with_shuffle=analysis_cfg.threshold_with_shuffle
)

# Compare across task phases
for phase1, phase2 in analysis_cfg.all_interphase_comparisons:
    compare_activity(ensembles, phase1, phase2)
```

---

## When to Use Which

### Use `config.yaml` when:
- Setting up the preprocessing pipeline
- Running shuffle generation
- Specifying data locations
- Configuring computational resources (cores, memory)
- Setting up time-series binning for preprocessing

### Use `analysis_config.yaml` when:
- Defining task phases and trial divisions
- Specifying statistical thresholds
- Configuring ensemble detection algorithms
- Setting up inter-phase comparisons
- Defining feature categories for analysis

---

## Recommendation: Keep Both

**Do NOT merge these configurations.** They serve different purposes:

1. **`config.yaml`** controls the **preprocessing infrastructure**
   - Changes when you want to reprocess data differently
   - Example: "Let's try 10,000 shuffles instead of 5,000"

2. **`analysis_config.yaml`** controls the **scientific analysis**
   - Changes when your experimental design or analysis strategy changes
   - Example: "Let's split into Early/Late using first 10 trials instead of 5"

### Future Integration
You could reference one from the other:
```yaml
# In config.yaml
analysis_config_path: "analysis_config.yaml"  # Reference to analysis config
```

This allows the preprocessing pipeline to know about downstream analysis requirements while keeping configurations modular.

---

## Summary Table

| Configuration | Purpose | Primary Users | Key Parameters |
|---------------|---------|---------------|----------------|
| **analysis_config.yaml** | Statistical analysis and scientific categorization | Ensemble detection, comparison scripts | Task phases, thresholds, feature types |
| **config.yaml** | Data preprocessing infrastructure | Data loading, shuffling, normalization | Paths, cores, shuffles, normalization |

---

## Questions?

**Q: Can I combine them?**
A: Not recommended. They have different lifecycles and purposes.

**Q: Which one do I modify for parameter sweeps?**
A: Depends on what you're sweeping:
- Normalization methods, shuffle counts → `config.yaml`
- Statistical thresholds, phase divisions → `analysis_config.yaml`

**Q: Which loads first?**
A: `config.yaml` loads first (during preprocessing), then `analysis_config.yaml` (during analysis)

**Q: Can they reference each other?**
A: Yes! You could add paths to cross-reference:
```yaml
# config.yaml
analysis:
  config_path: "analysis_config.yaml"

# analysis_config.yaml
preprocessing:
  config_path: "config.yaml"
```

---

**Created:** 2025-11-28
**For:** dlx56_mPFC_1p_SohalLab
**Purpose:** Clarify the two-config system
