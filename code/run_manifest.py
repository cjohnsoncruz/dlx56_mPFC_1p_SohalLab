"""
Run Manifest and Provenance Tracking Module

This module provides functions to create comprehensive manifests for each
processing run, enabling full reproducibility and computational provenance.

Key functions:
- create_run_manifest(): Generate complete manifest for a run
- save_with_metadata(): Save DataFrame with embedded metadata
- update_run_database(): Maintain central log of all runs
- compute_file_checksum(): Verify data integrity

Author: Generated for dlx56_mPFC_1p_SohalLab
"""

import json
import yaml
import hashlib
import subprocess
import platform
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import warnings

# Try to import pandas (required for update_run_database)
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    warnings.warn("pandas not available - update_run_database() will not work")

# Try to import pkg_resources, fallback to importlib.metadata for Python 3.8+
try:
    import pkg_resources
    def get_package_version(package_name):
        try:
            return pkg_resources.get_distribution(package_name).version
        except:
            return 'not installed'
except ImportError:
    from importlib import metadata
    def get_package_version(package_name):
        try:
            return metadata.version(package_name)
        except:
            return 'not installed'


def get_git_info() -> Dict[str, Any]:
    """
    Get git version control information if in a git repository.

    Returns
    -------
    dict
        Dictionary with keys:
        - git_commit: Short hash of current commit
        - git_branch: Current branch name
        - git_dirty: Whether there are uncommitted changes
        - git_remote: Remote URL if available

    Examples
    --------
    >>> git_info = get_git_info()
    >>> print(git_info['git_commit'])
    a3f4b2c1
    """
    try:
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()

        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()

        # Check if there are uncommitted changes
        status = subprocess.check_output(
            ['git', 'status', '--porcelain'],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        dirty = status != ''

        # Try to get remote URL
        try:
            remote = subprocess.check_output(
                ['git', 'config', '--get', 'remote.origin.url'],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
        except:
            remote = 'unknown'

        return {
            'git_commit': commit[:8],  # Short hash
            'git_commit_full': commit,
            'git_branch': branch,
            'git_dirty': dirty,
            'git_remote': remote,
        }
    except Exception as e:
        return {
            'git_commit': 'unknown',
            'git_commit_full': 'unknown',
            'git_branch': 'unknown',
            'git_dirty': None,
            'git_remote': 'unknown',
            'git_error': str(e)
        }


def get_package_versions(packages: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Get versions of installed packages.

    Parameters
    ----------
    packages : list of str, optional
        List of package names to check. If None, checks key scientific packages.

    Returns
    -------
    dict
        Dictionary mapping package names to version strings

    Examples
    --------
    >>> versions = get_package_versions()
    >>> print(versions['numpy'])
    1.24.3
    """
    if packages is None:
        packages = [
            'numpy', 'pandas', 'scipy', 'matplotlib',
            'seaborn', 'joblib', 'umap-learn', 'scikit-learn',
            'pyyaml', 'psutil'
        ]

    versions = {}
    for package in packages:
        versions[package] = get_package_version(package)

    return versions


def compute_file_checksum(filepath: Path, algorithm: str = 'md5') -> str:
    """
    Compute checksum of a file for integrity verification.

    Parameters
    ----------
    filepath : Path or str
        Path to file
    algorithm : str
        Hash algorithm ('md5', 'sha256', etc.)

    Returns
    -------
    str
        Checksum in format "algorithm:hash"

    Examples
    --------
    >>> checksum = compute_file_checksum('data.parquet')
    >>> print(checksum)
    md5:a3f4b2c1d5e6f7g8h9i0
    """
    filepath = Path(filepath)
    hash_func = hashlib.new(algorithm)

    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)

    return f"{algorithm}:{hash_func.hexdigest()}"


def compute_directory_size(directory: Path) -> Dict[str, Any]:
    """
    Compute total size and file count of a directory.

    Parameters
    ----------
    directory : Path
        Directory to analyze

    Returns
    -------
    dict
        Dictionary with 'total_size_bytes', 'total_size_mb', 'n_files'
    """
    directory = Path(directory)
    total_size = 0
    n_files = 0

    for file in directory.rglob('*'):
        if file.is_file():
            total_size += file.stat().st_size
            n_files += 1

    return {
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'total_size_gb': round(total_size / (1024 * 1024 * 1024), 3),
        'n_files': n_files
    }


def create_run_manifest(
    config: Dict[str, Any],
    output_dir: Path,
    run_id: Optional[str] = None,
    inputs: Optional[Dict[str, Any]] = None,
    outputs: Optional[Dict[str, Any]] = None,
    performance: Optional[Dict[str, Any]] = None,
    status: Optional[Dict[str, Any]] = None,
    custom_metadata: Optional[Dict[str, Any]] = None,
    save: bool = True
) -> Dict[str, Any]:
    """
    Create comprehensive manifest for a processing run.

    This function generates a complete record of a computational run including
    configuration parameters, input/output files, code version, environment,
    and performance metrics.

    Parameters
    ----------
    config : dict
        Configuration dictionary (from load_config())
    output_dir : Path
        Directory where outputs and manifest will be saved
    run_id : str, optional
        Unique run identifier. If None, uses timestamp.
    inputs : dict, optional
        Information about input files/data
    outputs : dict, optional
        Information about output files/data
    performance : dict, optional
        Runtime and resource usage metrics
    status : dict, optional
        Success/error/warning information
    custom_metadata : dict, optional
        Any additional metadata to include
    save : bool
        If True, saves manifest to YAML file

    Returns
    -------
    dict
        Complete manifest dictionary

    Examples
    --------
    >>> manifest = create_run_manifest(
    ...     config=config,
    ...     output_dir=Path('results/shuffles/run_20250128'),
    ...     performance={'runtime_seconds': 12047}
    ... )
    >>> print(manifest['run_info']['run_id'])
    20250128_143022
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if run_id is None:
        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Build manifest
    manifest = {
        'run_info': {
            'run_id': run_id,
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'user': os.getenv('USERNAME') or os.getenv('USER') or 'unknown',
            'hostname': platform.node(),
            'working_directory': str(Path.cwd()),
        },

        'inputs': inputs or {},

        'parameters': config,  # Entire config dict for full reproducibility

        'code_version': get_git_info(),

        'environment': {
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'processor': platform.processor(),
            'packages': get_package_versions(),
        },

        'outputs': outputs or {},

        'performance': performance or {},

        'status': status or {'success': True, 'errors': [], 'warnings': []},
    }

    # Add custom metadata if provided
    if custom_metadata:
        manifest['custom'] = custom_metadata

    # Save manifest to file
    if save:
        manifest_path = output_dir / f"run_manifest_{run_id}.yaml"

        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

        print(f"[OK] Manifest saved to: {manifest_path}")

        # Also save as JSON for easier programmatic access
        json_path = output_dir / f"run_manifest_{run_id}.json"
        with open(json_path, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)

        manifest['_manifest_path'] = str(manifest_path)
        manifest['_manifest_json_path'] = str(json_path)

    return manifest


def save_with_metadata(
    df,  # pd.DataFrame type hint removed for compatibility
    filepath: Path,
    config: Dict[str, Any],
    description: str = "",
    **metadata
) -> None:
    """
    Save DataFrame with embedded metadata.

    Note: Requires pandas to be installed.

    Saves the DataFrame as parquet and creates a separate JSON file with
    complete metadata about how the data was generated.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save
    filepath : Path
        Output file path (will save as .parquet)
    config : dict
        Configuration dictionary
    description : str
        Human-readable description of the data
    **metadata : dict
        Additional metadata key-value pairs

    Examples
    --------
    >>> save_with_metadata(
    ...     df=enrichment_df,
    ...     filepath='results/enrichment.parquet',
    ...     config=config,
    ...     description='Ensemble enrichment from shuffle analysis',
    ...     n_shuffles=5000
    ... )
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for save_with_metadata(). Install with: pip install pandas")

    filepath = Path(filepath)

    # Save DataFrame
    df.to_parquet(filepath)

    # Create metadata
    full_metadata = {
        'file_info': {
            'filename': filepath.name,
            'filepath': str(filepath),
            'created': datetime.now().isoformat(),
            'size_mb': round(filepath.stat().st_size / (1024 * 1024), 2),
            'n_rows': len(df),
            'n_columns': len(df.columns),
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        },
        'description': description,
        'config': config,
        'code_version': get_git_info(),
        'environment': {
            'python_version': platform.python_version(),
            'packages': get_package_versions(),
        },
        'custom': metadata
    }

    # Save metadata as JSON
    metadata_path = filepath.with_suffix('.meta.json')
    with open(metadata_path, 'w') as f:
        json.dump(full_metadata, f, indent=2, default=str)

    print(f"[OK] Saved data to: {filepath}")
    print(f"[OK] Saved metadata to: {metadata_path}")
    print(f"     Shape: {df.shape}, Size: {full_metadata['file_info']['size_mb']} MB")


def update_run_database(
    manifest: Dict[str, Any],
    db_path: Path = None,
    auto_create: bool = True
):  # Returns pd.DataFrame when pandas is available
    """
    Update central run log database with information from this run.

    Maintains a CSV file with one row per run, making it easy to query
    and compare different processing runs.

    Parameters
    ----------
    manifest : dict
        Run manifest dictionary from create_run_manifest()
    db_path : Path, optional
        Path to run database CSV. If None, uses 'run_log.csv' in current dir.
    auto_create : bool
        If True, creates database if it doesn't exist

    Returns
    -------
    pd.DataFrame
        Updated run database

    Examples
    --------
    >>> run_db = update_run_database(manifest)
    >>> print(run_db.tail())
    >>> print(f"Total runs: {len(run_db)}")
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for update_run_database(). Install with: pip install pandas")

    if db_path is None:
        db_path = Path('run_log.csv')
    else:
        db_path = Path(db_path)

    # Extract key information from manifest
    run_record = {
        'run_id': manifest['run_info']['run_id'],
        'timestamp': manifest['run_info']['timestamp'],
        'date': manifest['run_info']['date'],
        'user': manifest['run_info']['user'],
        'hostname': manifest['run_info']['hostname'],

        # Code version
        'git_commit': manifest['code_version'].get('git_commit', 'unknown'),
        'git_branch': manifest['code_version'].get('git_branch', 'unknown'),
        'git_dirty': manifest['code_version'].get('git_dirty', None),

        # Parameters (key ones)
        'data_type': manifest['parameters']['data'].get('data_type_used', 'unknown'),
        'normalization': manifest['parameters']['preprocessing'].get('normalization', 'unknown'),
        'n_shuffles': manifest['parameters']['shuffles'].get('n_shuffles_per_subject', 0),
        'base_seed': manifest['parameters']['shuffles'].get('base_seed', 0),
        'n_cores': manifest['parameters']['shuffles'].get('n_cores', 0),

        # Inputs
        'n_subjects': manifest['inputs'].get('n_subjects', 0),
        'source_data': manifest['inputs'].get('source_data', 'unknown'),

        # Outputs
        'output_dir': manifest['outputs'].get('shuffle_parquets',
                                            manifest['outputs'].get('output_dir', 'unknown')),
        'n_output_files': manifest['outputs'].get('n_files', 0),
        'output_size_mb': manifest['outputs'].get('total_size_mb', 0),

        # Performance
        'runtime_seconds': manifest['performance'].get('runtime_seconds', 0),
        'runtime_hours': manifest['performance'].get('runtime_seconds', 0) / 3600,
        'peak_memory_gb': manifest['performance'].get('peak_memory_gb', 0),

        # Status
        'success': manifest['status'].get('success', False),
        'n_errors': len(manifest['status'].get('errors', [])),
        'n_warnings': len(manifest['status'].get('warnings', [])),

        # Manifest location
        'manifest_path': manifest.get('_manifest_path', 'unknown'),
    }

    # Load existing database or create new
    if db_path.exists():
        db = pd.read_csv(db_path)
    else:
        if not auto_create:
            raise FileNotFoundError(f"Run database not found: {db_path}")
        db = pd.DataFrame()

    # Append new record
    db = pd.concat([db, pd.DataFrame([run_record])], ignore_index=True)

    # Save updated database
    db.to_csv(db_path, index=False)

    print(f"[OK] Run database updated: {db_path}")
    print(f"     Total runs recorded: {len(db)}")

    return db


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load a previously saved manifest file.

    Parameters
    ----------
    manifest_path : Path
        Path to manifest YAML or JSON file

    Returns
    -------
    dict
        Manifest dictionary
    """
    manifest_path = Path(manifest_path)

    if manifest_path.suffix == '.yaml':
        with open(manifest_path, 'r') as f:
            return yaml.safe_load(f)
    elif manifest_path.suffix == '.json':
        with open(manifest_path, 'r') as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported manifest format: {manifest_path.suffix}")


def compare_manifests(manifest1: Dict, manifest2: Dict) -> Dict[str, Any]:
    """
    Compare two manifests to identify parameter differences.

    Parameters
    ----------
    manifest1 : dict
        First manifest
    manifest2 : dict
        Second manifest

    Returns
    -------
    dict
        Dictionary showing differences
    """
    def get_param_path(d, prefix=''):
        """Flatten nested dict to dot-notation paths."""
        items = {}
        for k, v in d.items():
            if isinstance(v, dict):
                items.update(get_param_path(v, f"{prefix}{k}."))
            else:
                items[f"{prefix}{k}"] = v
        return items

    params1 = get_param_path(manifest1.get('parameters', {}))
    params2 = get_param_path(manifest2.get('parameters', {}))

    differences = {}
    all_keys = set(params1.keys()) | set(params2.keys())

    for key in all_keys:
        val1 = params1.get(key, 'NOT_SET')
        val2 = params2.get(key, 'NOT_SET')

        if val1 != val2:
            differences[key] = {
                'manifest1': val1,
                'manifest2': val2
            }

    return {
        'run1': manifest1['run_info']['run_id'],
        'run2': manifest2['run_info']['run_id'],
        'differences': differences,
        'n_differences': len(differences)
    }


def print_manifest_summary(manifest: Dict[str, Any]) -> None:
    """
    Print a human-readable summary of a manifest.

    Parameters
    ----------
    manifest : dict
        Manifest dictionary
    """
    print("=" * 70)
    print("RUN MANIFEST SUMMARY")
    print("=" * 70)

    print(f"\n[Run Info]")
    print(f"  ID: {manifest['run_info']['run_id']}")
    print(f"  Timestamp: {manifest['run_info']['timestamp']}")
    print(f"  User: {manifest['run_info']['user']}@{manifest['run_info']['hostname']}")

    print(f"\n[Code Version]")
    print(f"  Git commit: {manifest['code_version']['git_commit']}")
    print(f"  Git branch: {manifest['code_version']['git_branch']}")
    print(f"  Uncommitted changes: {manifest['code_version']['git_dirty']}")

    print(f"\n[Key Parameters]")
    params = manifest['parameters']
    print(f"  Data type: {params['data'].get('data_type_used', 'N/A')}")
    print(f"  Normalization: {params['preprocessing'].get('normalization', 'N/A')}")
    print(f"  Shuffles per subject: {params['shuffles'].get('n_shuffles_per_subject', 'N/A')}")
    print(f"  Random seed: {params['shuffles'].get('base_seed', 'N/A')}")

    print(f"\n[Performance]")
    perf = manifest['performance']
    if 'runtime_seconds' in perf:
        print(f"  Runtime: {perf['runtime_seconds']/3600:.2f} hours")
    if 'peak_memory_gb' in perf:
        print(f"  Peak memory: {perf['peak_memory_gb']:.1f} GB")
    if 'n_cores_used' in perf:
        print(f"  Cores used: {perf['n_cores_used']}")

    print(f"\n[Status]")
    status = manifest['status']
    print(f"  Success: {status.get('success', 'unknown')}")
    print(f"  Errors: {len(status.get('errors', []))}")
    print(f"  Warnings: {len(status.get('warnings', []))}")

    print("=" * 70)


if __name__ == "__main__":
    # Test the module
    print("Testing run_manifest module...\n")

    # Test git info
    print("[Test 1] Git information:")
    git_info = get_git_info()
    for key, value in git_info.items():
        print(f"  {key}: {value}")

    # Test package versions
    print("\n[Test 2] Package versions:")
    versions = get_package_versions()
    for pkg, ver in list(versions.items())[:5]:  # Show first 5
        print(f"  {pkg}: {ver}")

    # Test checksum computation
    print("\n[Test 3] File checksum:")
    test_file = Path(__file__)
    if test_file.exists():
        checksum = compute_file_checksum(test_file)
        print(f"  {test_file.name}: {checksum}")

    print("\n[OK] All tests passed!")
    print("\nModule functions available:")
    print("  - create_run_manifest()")
    print("  - save_with_metadata()")
    print("  - update_run_database()")
    print("  - compute_file_checksum()")
    print("  - get_git_info()")
    print("  - get_package_versions()")
    print("  - load_manifest()")
    print("  - compare_manifests()")
    print("  - print_manifest_summary()")
