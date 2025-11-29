"""
Example Usage: run_manifest.py

This file shows how to use the run_manifest module to track computational
provenance in your preprocessing pipeline.

Use this code in your Jupyter notebooks or Python scripts.
"""

from pathlib import Path
import time
from datetime import datetime
import pandas as pd

# Import manifest tracking functions
from run_manifest import (
    create_run_manifest,
    save_with_metadata,
    update_run_database,
    print_manifest_summary,
)

# Import configuration
from config_preprocessing import load_config

# ============================================================================
# EXAMPLE 1: Basic Run Tracking in a Notebook
# ============================================================================

def example_basic_run_tracking():
    """
    Minimal example: Track parameters and outputs for a processing run.

    Add this to the beginning and end of your notebook.
    """

    # --- AT THE START OF YOUR NOTEBOOK ---

    # Load configuration
    config = load_config('config.yaml')

    # Create unique run ID
    RUN_ID = datetime.now().strftime('%Y%m%d_%H%M%S')
    START_TIME = time.time()

    print(f"Run ID: {RUN_ID}")
    print(f"Started: {datetime.now()}")

    # Create output directory
    results_dir = config['data']['results_dir']
    run_output_dir = results_dir / 'shuffles' / f"shuffle_run_{RUN_ID}"
    run_output_dir.mkdir(parents=True, exist_ok=True)

    # Copy config to output directory for reference
    import shutil
    shutil.copy('config.yaml', run_output_dir / 'config_used.yaml')

    # --- DO YOUR PROCESSING HERE ---
    print("\n... processing data ...")
    time.sleep(1)  # Simulated work

    # --- AT THE END OF YOUR NOTEBOOK ---

    # Calculate runtime
    runtime = time.time() - START_TIME

    # Create manifest
    manifest = create_run_manifest(
        config=config,
        output_dir=run_output_dir,
        run_id=RUN_ID,
        inputs={
            'source_data': str(config['data']['source_dataset_location']),
            'n_subjects': len(config['subjects']),
        },
        outputs={
            'shuffle_parquets': str(run_output_dir),
            'n_files': 35,  # Example: number of output files
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

    # Update central run log
    run_db = update_run_database(manifest, db_path=results_dir / 'run_log.csv')

    print(f"\n{'='*60}")
    print(f"Run complete: {RUN_ID}")
    print(f"Runtime: {runtime:.1f} seconds")
    print(f"Outputs: {run_output_dir}")
    print(f"{'='*60}")

    return manifest


# ============================================================================
# EXAMPLE 2: Save DataFrame with Metadata
# ============================================================================

def example_save_with_metadata():
    """
    Example: Save a DataFrame with full metadata tracking.
    """

    # Load config
    config = load_config('config.yaml')

    # Create example DataFrame
    df = pd.DataFrame({
        'subject': ['10_3_HET_RS1', '13_4_WT_RS1'],
        'n_enriched_cells': [45, 38],
        'mean_enrichment_score': [2.3, 1.9],
    })

    # Save with metadata
    output_path = Path('results/enrichment/example_enrichment.parquet')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_with_metadata(
        df=df,
        filepath=output_path,
        config=config,
        description="Example ensemble enrichment results from circular shuffle analysis",
        n_shuffles=config['shuffles']['n_shuffles_per_subject'],
        analysis_type='enrichment_detection',
        custom_note='This is an example output'
    )

    print("\nMetadata saved alongside data file!")
    print(f"Data: {output_path}")
    print(f"Metadata: {output_path.with_suffix('.meta.json')}")


# ============================================================================
# EXAMPLE 3: Compare Two Runs
# ============================================================================

def example_compare_runs():
    """
    Example: Load and compare two manifests to see what changed.
    """
    from run_manifest import load_manifest, compare_manifests

    # Load two manifests (replace with actual paths)
    manifest1 = load_manifest('results/shuffles/shuffle_run_20250128_143022/run_manifest_20250128_143022.yaml')
    manifest2 = load_manifest('results/shuffles/shuffle_run_20250129_091533/run_manifest_20250129_091533.yaml')

    # Compare them
    comparison = compare_manifests(manifest1, manifest2)

    print(f"\nComparing runs:")
    print(f"  Run 1: {comparison['run1']}")
    print(f"  Run 2: {comparison['run2']}")
    print(f"  Number of differences: {comparison['n_differences']}")

    if comparison['differences']:
        print("\nParameter differences:")
        for param, values in comparison['differences'].items():
            print(f"  {param}:")
            print(f"    Run 1: {values['manifest1']}")
            print(f"    Run 2: {values['manifest2']}")


# ============================================================================
# EXAMPLE 4: Query Run Database
# ============================================================================

def example_query_run_database():
    """
    Example: Query the run log database to find specific runs.
    """

    # Load run database
    run_db = pd.read_csv('results/run_log.csv')

    print("\n=== Run Database Summary ===")
    print(f"Total runs: {len(run_db)}")

    # Show most recent runs
    print("\nMost recent 5 runs:")
    print(run_db[['run_id', 'date', 'n_shuffles', 'normalization', 'success']].tail())

    # Find successful runs with 5000 shuffles
    print("\nSuccessful runs with 5000 shuffles:")
    filtered = run_db[(run_db['n_shuffles'] == 5000) & (run_db['success'] == True)]
    print(filtered[['run_id', 'date', 'normalization', 'runtime_hours']])

    # Find runs by specific user
    print("\nRuns by current user:")
    import os
    current_user = os.getenv('USERNAME') or os.getenv('USER')
    user_runs = run_db[run_db['user'] == current_user]
    print(f"Found {len(user_runs)} runs by {current_user}")


# ============================================================================
# EXAMPLE 5: Comprehensive Notebook Template
# ============================================================================

def comprehensive_notebook_template():
    """
    Complete template for a notebook with full provenance tracking.

    Copy this structure into your preprocessing notebook.
    """

    print("="*70)
    print("COMPREHENSIVE NOTEBOOK TEMPLATE WITH PROVENANCE TRACKING")
    print("="*70)

    # ========== SETUP CELL ==========
    print("\n[CELL 1: Setup and Configuration]")

    from run_manifest import create_run_manifest, update_run_database, save_with_metadata
    from config_preprocessing import load_config
    import time
    from datetime import datetime

    # Load configuration
    config = load_config('config.yaml')

    # Initialize run tracking
    RUN_ID = datetime.now().strftime('%Y%m%d_%H%M%S')
    START_TIME = time.time()

    results_dir = config['data']['results_dir']
    run_output_dir = results_dir / 'shuffles' / f"shuffle_run_{RUN_ID}"
    run_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Run ID: {RUN_ID}")
    print(f"Output directory: {run_output_dir}")

    # ========== PROCESSING CELLS ==========
    print("\n[CELLS 2-N: Your Processing Code]")
    print("... load data ...")
    print("... run shuffles ...")
    print("... detect enrichment ...")
    print("... generate time-series ...")

    # ========== SAVE OUTPUTS WITH METADATA ==========
    print("\n[CELL N+1: Save Outputs]")

    # Example: Save enrichment results
    # save_with_metadata(
    #     df=enrichment_df,
    #     filepath=run_output_dir / 'enrichment_results.parquet',
    #     config=config,
    #     description='Ensemble enrichment from shuffle analysis',
    #     n_shuffles=config['shuffles']['n_shuffles_per_subject']
    # )

    # ========== FINAL CELL: CREATE MANIFEST ==========
    print("\n[FINAL CELL: Create Run Manifest]")

    runtime = time.time() - START_TIME

    manifest = create_run_manifest(
        config=config,
        output_dir=run_output_dir,
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
        },
        status={'success': True}
    )

    # Update run log
    run_db = update_run_database(manifest, db_path=results_dir / 'run_log.csv')

    print(f"\n✓ Run complete: {RUN_ID}")
    print(f"✓ Manifest saved: {run_output_dir / f'run_manifest_{RUN_ID}.yaml'}")
    print(f"✓ Runtime: {runtime/3600:.2f} hours")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("RUN MANIFEST MODULE - USAGE EXAMPLES")
    print("="*70)

    print("\n1. Basic run tracking - see example_basic_run_tracking()")
    print("2. Save with metadata - see example_save_with_metadata()")
    print("3. Compare runs - see example_compare_runs()")
    print("4. Query database - see example_query_run_database()")
    print("5. Full template - see comprehensive_notebook_template()")

    print("\n" + "="*70)
    print("To use in your notebook, add these cells:")
    print("="*70)

    print("""
# Cell 1: Setup
from run_manifest import create_run_manifest, update_run_database
from config_preprocessing import load_config
import time
from datetime import datetime

config = load_config('config.yaml')
RUN_ID = datetime.now().strftime('%Y%m%d_%H%M%S')
START_TIME = time.time()

# ... your processing code ...

# Final Cell: Create manifest
runtime = time.time() - START_TIME
manifest = create_run_manifest(
    config=config,
    output_dir=results_dir / 'shuffles' / f'shuffle_run_{RUN_ID}',
    run_id=RUN_ID,
    performance={'runtime_seconds': int(runtime)}
)
run_db = update_run_database(manifest)
    """)
