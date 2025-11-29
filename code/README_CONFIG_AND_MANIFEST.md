# Configuration and Provenance Tracking System

This directory contains a complete configuration and provenance tracking system for reproducible computational research.

## Files Overview

### Core Configuration Files
- **`config.yaml`** - Central configuration file with all processing parameters
- **`config_preprocessing.py`** - Configuration loader with validation and helper functions

### Provenance Tracking Files
- **`run_manifest.py`** - Functions for creating run manifests and tracking computational provenance
- **`run_manifest_usage_example.py`** - Examples showing how to use the manifest system

## Quick Start

### 1. Load Configuration in Your Notebook

```python
from config_preprocessing import load_config, print_config_summary

# Load configuration
config = load_config('config.yaml')

# Print summary to verify settings
print_config_summary(config)

# Access parameters
n_shuffles = config['shuffles']['n_shuffles_per_subject']
normalization = config['preprocessing']['normalization']
```

### 2. Add Run Tracking to Your Notebook

**At the beginning:**
```python
from run_manifest import create_run_manifest, update_run_database
import time
from datetime import datetime

# Initialize run
RUN_ID = datetime.now().strftime('%Y%m%d_%H%M%S')
START_TIME = time.time()

print(f"Run ID: {RUN_ID}")
print(f"Started: {datetime.now()}")
```

**At the end:**
```python
# Calculate runtime
runtime = time.time() - START_TIME

# Create comprehensive manifest
manifest = create_run_manifest(
    config=config,
    output_dir=results_dir / 'shuffles' / f'shuffle_run_{RUN_ID}',
    run_id=RUN_ID,
    inputs={
        'source_data': str(config['data']['source_dataset_location']),
        'n_subjects': len(config['subjects']),
    },
    outputs={
        'shuffle_parquets': str(run_output_dir),
        'n_files': 35,
    },
    performance={
        'runtime_seconds': int(runtime),
        'runtime_human': f"{runtime/3600:.2f} hours",
        'n_cores_used': config['shuffles']['n_cores'],
    },
    status={
        'success': True,
        'errors': [],
        'warnings': [],
    }
)

# Update central run database
run_db = update_run_database(manifest, db_path=results_dir / 'run_log.csv')

print(f"\n✓ Run complete: {RUN_ID}")
print(f"✓ Runtime: {runtime/3600:.2f} hours")
```

### 3. Save Data with Metadata

```python
from run_manifest import save_with_metadata

save_with_metadata(
    df=enrichment_df,
    filepath='results/enrichment/all_chunked_ensembles.parquet',
    config=config,
    description='Ensemble enrichment from circular shuffle analysis',
    n_shuffles=5000,
    analysis_type='enrichment_detection'
)
```

## Configuration System

### config.yaml Structure

```yaml
data:
  source_dataset_location: "path/to/data"
  results_dir: "path/to/results"
  data_type_used: 'dff'

preprocessing:
  gaussian_sigma: 1
  normalization: 'baseline_zscore'
  post_outcome_duration: 15
  drop_inactive_cells: true

shuffles:
  n_shuffles_per_subject: 5000
  base_seed: 42
  chunk_size: 1000

timeseries:
  fps: 20
  bin_size: 0.25
  pre_frames: 60
  post_frames: 300

umap:
  n_neighbors: 15
  min_dist: 0.1
  metric: 'hamming'

subjects:
  - "10_3_HET_RS1"
  - "10_3_HET_RS2"
  # ... all 35 subjects
```

### Helper Functions

```python
from config_preprocessing import (
    load_config,
    get_subject_list,
    get_genotype,
    get_session_type,
    get_subject_metadata,
    print_config_summary
)

# Get subject information
subjects = get_subject_list(config)
genotype = get_genotype('10_3_HET_RS1')  # Returns 'HET'
session = get_session_type('10_3_HET_RS1')  # Returns 'Reversal_Shifting'

# Get complete metadata
metadata = get_subject_metadata('10_3_HET_RS1')
# Returns: {'subject_name': '10_3_HET_RS1', 'genotype': 'HET',
#           'session_type': 'Reversal_Shifting', 'session_number': 1}
```

## Provenance Tracking System

### What Gets Tracked

Each run manifest includes:

1. **Run Information**
   - Unique run ID (timestamp)
   - User and hostname
   - Working directory

2. **Input Data**
   - Source data location
   - Number of subjects
   - Data checksums (optional)

3. **Parameters**
   - Complete copy of config.yaml
   - All processing parameters

4. **Code Version**
   - Git commit hash
   - Git branch
   - Whether there are uncommitted changes
   - Remote repository URL

5. **Environment**
   - Python version
   - Platform information
   - Package versions (numpy, pandas, etc.)

6. **Outputs**
   - Output file locations
   - Number of files created
   - Total output size

7. **Performance**
   - Runtime (seconds and human-readable)
   - Peak memory usage (if tracked)
   - Number of cores used

8. **Status**
   - Success/failure
   - Errors encountered
   - Warnings generated

### Output Directory Structure

```
results/
├── run_log.csv                          # Central database of all runs
│
├── shuffles/
│   ├── shuffle_run_20250128_143022/
│   │   ├── run_manifest_20250128_143022.yaml    # Complete manifest
│   │   ├── run_manifest_20250128_143022.json    # Same as JSON
│   │   ├── config_used.yaml                      # Copy of config
│   │   ├── 10_3_HET_RS1_shuffled.parquet        # Data files
│   │   └── ...
│   │
│   └── shuffle_run_20250129_091533/
│       └── ...
│
└── enrichment/
    ├── all_chunked_ensembles.parquet
    └── all_chunked_ensembles.meta.json          # Embedded metadata
```

## Available Functions

### Configuration (config_preprocessing.py)

| Function | Description |
|----------|-------------|
| `load_config(path)` | Load and validate config YAML |
| `get_subject_list(config)` | Get list of all subjects |
| `get_genotype(subject)` | Extract genotype from subject name |
| `get_session_type(subject)` | Extract session type |
| `get_subject_metadata(subject)` | Get complete metadata dict |
| `print_config_summary(config)` | Print human-readable summary |

### Provenance (run_manifest.py)

| Function | Description |
|----------|-------------|
| `create_run_manifest(...)` | Create comprehensive run manifest |
| `save_with_metadata(df, ...)` | Save DataFrame with metadata |
| `update_run_database(manifest)` | Add run to central database |
| `get_git_info()` | Get git version information |
| `get_package_versions()` | Get installed package versions |
| `compute_file_checksum(path)` | Calculate file checksum |
| `load_manifest(path)` | Load saved manifest |
| `compare_manifests(m1, m2)` | Compare two manifests |
| `print_manifest_summary(manifest)` | Print readable summary |

## Benefits

### 1. Reproducibility
- Every run is fully documented
- Can recreate exact results months/years later
- Know exactly what parameters were used

### 2. Debugging
- When results change, quickly identify what changed
- Compare parameters between runs
- Track down when issues were introduced

### 3. Collaboration
- Others can understand your methods
- Easy to share processing parameters
- Standardized documentation

### 4. Publication
- Methods section writes itself from manifests
- Complete audit trail for reviewers
- Transparent computational methods

### 5. Efficiency
- Quickly find "that run with parameter X"
- Query database for specific conditions
- Avoid re-running with wrong parameters

## Example Workflows

### Experiment with Parameters

```python
# Load base config
config = load_config('config.yaml')

# Modify for experiment
config['shuffles']['n_shuffles_per_subject'] = 1000  # Test with fewer
config['umap']['min_dist'] = 0.2  # Try different parameter

# Run pipeline
# ... processing code ...

# Manifest automatically records the modified parameters
manifest = create_run_manifest(config, output_dir, ...)
```

### Compare Two Analysis Runs

```python
from run_manifest import load_manifest, compare_manifests

# Load manifests
run1 = load_manifest('results/shuffles/shuffle_run_20250128/run_manifest_20250128.yaml')
run2 = load_manifest('results/shuffles/shuffle_run_20250129/run_manifest_20250129.yaml')

# Compare
comparison = compare_manifests(run1, run2)

print(f"Found {comparison['n_differences']} parameter differences:")
for param, values in comparison['differences'].items():
    print(f"  {param}: {values['manifest1']} → {values['manifest2']}")
```

### Query Run History

```python
import pandas as pd

# Load run database
run_db = pd.read_csv('results/run_log.csv')

# Find successful runs with specific parameters
good_runs = run_db[
    (run_db['success'] == True) &
    (run_db['n_shuffles'] == 5000) &
    (run_db['normalization'] == 'baseline_zscore')
]

print(f"Found {len(good_runs)} matching runs")
print(good_runs[['run_id', 'date', 'runtime_hours']])
```

## Testing the System

### Test Configuration Loading
```bash
python config_preprocessing.py
```

### Test Manifest Functions
```bash
python run_manifest.py
```

### View Examples
```bash
python run_manifest_usage_example.py
```

## Requirements

```
pyyaml>=6.0
psutil>=5.9.0
pandas>=2.0.0  # For update_run_database() and save_with_metadata()
```

Install with:
```bash
pip install pyyaml psutil pandas
```

## Best Practices

1. **Always use config.yaml** - Never hardcode parameters
2. **Create manifest for every run** - Even test runs
3. **Copy config to output directory** - For reference
4. **Use meaningful run IDs** - Timestamps work well
5. **Update central database** - Makes querying easy
6. **Track git commits** - Enables code version tracking
7. **Save metadata with data files** - Self-documenting outputs
8. **Query before re-running** - Check if already done

## Troubleshooting

**Q: Config won't load**
- Check YAML syntax (indentation, colons, quotes)
- Verify file path is correct
- Run `python config_preprocessing.py` to see errors

**Q: Manifest creation fails**
- Check output directory exists and is writable
- Ensure config is loaded first
- Verify all required parameters are in config

**Q: Run database errors**
- Make sure pandas is installed
- Check file permissions on run_log.csv
- Verify db_path is correct

**Q: Git info shows 'unknown'**
- Make sure you're in a git repository
- Verify git is installed and in PATH
- Check you've made at least one commit

## Further Reading

- See `run_manifest_usage_example.py` for detailed examples
- Refer to docstrings in `run_manifest.py` for function details
- Check `config_preprocessing.py` for configuration options

---

**Created for:** dlx56_mPFC_1p_SohalLab
**Purpose:** Reproducible computational research
**Version:** 1.0
**Date:** 2025-01-28
