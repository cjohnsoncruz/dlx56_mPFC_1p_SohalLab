"""
Configuration loader and validator for preprocessing pipeline.

Loads configuration from config.yaml and provides helper functions
for accessing subject information and computing derived parameters.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any
import psutil


def load_config(config_path: str = 'config.yaml') -> Dict[str, Any]:
    """
    Load and validate preprocessing configuration from YAML file.

    Parameters
    ----------
    config_path : str
        Path to configuration YAML file (default: 'config.yaml')

    Returns
    -------
    dict
        Configuration dictionary with validated parameters

    Raises
    ------
    FileNotFoundError
        If config file doesn't exist
    ValueError
        If required configuration sections are missing

    Examples
    --------
    >>> config = load_config('config.yaml')
    >>> print(config['preprocessing']['normalization'])
    baseline_zscore
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load YAML
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate required sections
    required_sections = ['data', 'preprocessing', 'shuffles', 'timeseries', 'subjects']
    missing_sections = [sec for sec in required_sections if sec not in config]

    if missing_sections:
        raise ValueError(f"Missing required configuration sections: {missing_sections}")

    # Convert string paths to Path objects
    config['data']['root_dir'] = Path(config['data']['root_dir'])
    config['data']['data_dir'] = Path(config['data']['data_dir'])
    config['data']['results_dir'] = Path(config['data']['results_dir'])
    config['data']['source_dataset_location'] = Path(config['data']['source_dataset_location'])

    # Create results directories if they don't exist
    results_dir = config['data']['results_dir']
    results_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories for different output types
    subdirs = ['raw_data', 'shuffles', 'enrichment', 'timeseries', 'umap', 'diagnostics']
    for subdir in subdirs:
        (results_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Compute number of cores if not explicitly set
    if 'n_cores' not in config['shuffles']:
        total_cpu_physical = psutil.cpu_count(logical=False)
        cores_to_leave = config['shuffles'].get('cores_to_leave_free', 2)
        config['shuffles']['n_cores'] = max(1, total_cpu_physical - cores_to_leave)

    # Validate data type
    if config['data']['data_type_used'] not in config['data']['data_types']:
        raise ValueError(
            f"data_type_used '{config['data']['data_type_used']}' not in "
            f"available data_types {config['data']['data_types']}"
        )

    # Validate normalization method
    valid_normalizations = ['min_max', 'baseline_zscore', 'none']
    if config['preprocessing']['normalization'] not in valid_normalizations:
        raise ValueError(
            f"normalization '{config['preprocessing']['normalization']}' not valid. "
            f"Must be one of: {valid_normalizations}"
        )

    # Validate subjects list
    if len(config['subjects']) != 35:
        print(f"WARNING: Expected 35 subjects, found {len(config['subjects'])}")

    # Validate bin_size calculation
    expected_bin_size = config['timeseries']['window_to_bin'] / config['timeseries']['fps']
    if abs(config['timeseries']['bin_size'] - expected_bin_size) > 0.001:
        print(f"WARNING: bin_size mismatch. Expected {expected_bin_size}, got {config['timeseries']['bin_size']}")

    return config


def get_subject_list(config: Dict[str, Any] = None) -> List[str]:
    """
    Return list of subject names from configuration.

    Parameters
    ----------
    config : dict, optional
        Configuration dictionary. If None, loads from default config.yaml

    Returns
    -------
    list of str
        List of 35 subject names

    Examples
    --------
    >>> subjects = get_subject_list()
    >>> print(len(subjects))
    35
    >>> print(subjects[0])
    10_3_HET_RS1
    """
    if config is None:
        config = load_config()

    return config['subjects']


def get_genotype(subject_name: str) -> str:
    """
    Extract genotype from subject name.

    Parameters
    ----------
    subject_name : str
        Subject identifier (e.g., '10_3_HET_RS1')

    Returns
    -------
    str
        Genotype: 'WT' or 'HET'

    Raises
    ------
    ValueError
        If genotype cannot be determined from subject name

    Examples
    --------
    >>> get_genotype('10_3_HET_RS1')
    'HET'
    >>> get_genotype('13_4_WT_RS1')
    'WT'
    """
    subject_upper = subject_name.upper()

    if 'WT' in subject_upper:
        return 'WT'
    elif 'HET' in subject_upper:
        return 'HET'
    else:
        raise ValueError(f"Cannot determine genotype for subject: {subject_name}")


def get_session_type(subject_name: str) -> str:
    """
    Extract session type from subject name.

    Parameters
    ----------
    subject_name : str
        Subject identifier (e.g., '10_3_HET_RS1')

    Returns
    -------
    str
        Session type: 'Reversal_Shifting' or 'Initial_Acquisition'

    Examples
    --------
    >>> get_session_type('10_3_HET_RS1')
    'Reversal_Shifting'
    >>> get_session_type('10_3_HET_IA1')
    'Initial_Acquisition'
    """
    subject_upper = subject_name.upper()

    if 'RS' in subject_upper:
        return 'Reversal_Shifting'
    elif 'IA' in subject_upper:
        return 'Initial_Acquisition'
    else:
        return 'Unknown'


def get_session_number(subject_name: str) -> int:
    """
    Extract session number from subject name.

    Parameters
    ----------
    subject_name : str
        Subject identifier (e.g., '10_3_HET_RS1')

    Returns
    -------
    int
        Session number (1, 2, or 3)

    Examples
    --------
    >>> get_session_number('10_3_HET_RS1')
    1
    >>> get_session_number('10_3_HET_RS2')
    2
    """
    # Extract last character (session number)
    try:
        return int(subject_name[-1])
    except (ValueError, IndexError):
        return 0


def get_subject_metadata(subject_name: str) -> Dict[str, str]:
    """
    Extract all metadata from subject name.

    Parameters
    ----------
    subject_name : str
        Subject identifier (e.g., '10_3_HET_RS1')

    Returns
    -------
    dict
        Dictionary with keys: 'subject_name', 'genotype', 'session_type', 'session_number'

    Examples
    --------
    >>> metadata = get_subject_metadata('10_3_HET_RS1')
    >>> print(metadata)
    {'subject_name': '10_3_HET_RS1', 'genotype': 'HET',
     'session_type': 'Reversal_Shifting', 'session_number': 1}
    """
    return {
        'subject_name': subject_name,
        'genotype': get_genotype(subject_name),
        'session_type': get_session_type(subject_name),
        'session_number': get_session_number(subject_name)
    }


def get_n_cores(config: Dict[str, Any] = None) -> int:
    """
    Get number of cores to use for parallel processing.

    Parameters
    ----------
    config : dict, optional
        Configuration dictionary. If None, loads from default config.yaml

    Returns
    -------
    int
        Number of cores (total_cpu_physical - cores_to_leave_free)

    Examples
    --------
    >>> n_cores = get_n_cores()
    >>> print(f"Using {n_cores} cores")
    Using 14 cores
    """
    if config is None:
        config = load_config()

    return config['shuffles']['n_cores']


def print_config_summary(config: Dict[str, Any]) -> None:
    """
    Print a summary of the configuration settings.

    Parameters
    ----------
    config : dict
        Configuration dictionary

    Examples
    --------
    >>> config = load_config()
    >>> print_config_summary(config)
    """
    print("=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)

    print("\n[Data]")
    print(f"  Source: {config['data']['source_dataset_location']}")
    print(f"  Results: {config['data']['results_dir']}")
    print(f"  Data type: {config['data']['data_type_used']}")
    print(f"  Number of subjects: {len(config['subjects'])}")

    print("\n[Preprocessing]")
    print(f"  Gaussian sigma: {config['preprocessing']['gaussian_sigma']}")
    print(f"  Normalization: {config['preprocessing']['normalization']}")
    print(f"  Post-outcome duration: {config['preprocessing']['post_outcome_duration']}s")
    print(f"  Drop inactive cells: {config['preprocessing']['drop_inactive_cells']}")

    print("\n[Shuffles]")
    print(f"  Shuffles per subject: {config['shuffles']['n_shuffles_per_subject']}")
    print(f"  Base seed: {config['shuffles']['base_seed']}")
    print(f"  Number of cores: {config['shuffles']['n_cores']}")
    print(f"  Chunk size: {config['shuffles']['chunk_size']}")

    print("\n[Time-series]")
    print(f"  FPS: {config['timeseries']['fps']}")
    print(f"  Bin size: {config['timeseries']['bin_size']}s")
    print(f"  Pre-outcome frames: {config['timeseries']['pre_frames']}")
    print(f"  Post-outcome frames: {config['timeseries']['post_frames']}")

    print("\n[UMAP]")
    print(f"  n_neighbors: {config['umap']['n_neighbors']}")
    print(f"  min_dist: {config['umap']['min_dist']}")
    print(f"  metric: {config['umap']['metric']}")

    print("=" * 60)


if __name__ == "__main__":
    # Test loading configuration
    print("Testing configuration loading...\n")

    try:
        config = load_config('config.yaml')
        print("[OK] Configuration loaded successfully\n")

        # Print summary
        print_config_summary(config)

        # Test helper functions
        print("\n\nTesting helper functions:")
        print("-" * 60)

        subjects = get_subject_list(config)
        print(f"[OK] Loaded {len(subjects)} subjects")

        test_subject = subjects[0]
        print(f"\nTest subject: {test_subject}")
        print(f"  Genotype: {get_genotype(test_subject)}")
        print(f"  Session type: {get_session_type(test_subject)}")
        print(f"  Session number: {get_session_number(test_subject)}")

        metadata = get_subject_metadata(test_subject)
        print(f"\nFull metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

        print(f"\n[OK] Number of cores to use: {get_n_cores(config)}")

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
