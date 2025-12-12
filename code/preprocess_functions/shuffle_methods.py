# code for shuffling dataframes
## imports 
import numpy as np
import pandas as pd
import numba
from preprocessing_utils import read_shuffle_parquet_from_folder
import time
from datetime import datetime
from pathlib import Path
from typing import List, Any, Dict


## functions for saving shuffle info:
## create info df + save
def log_shuffle_run(results_dir: Path, shuffle_storage_folder: Path, 
                    n_shuf_per_subject: int, n_subjects: int, base_seed: int, shuffle_type = None) -> None:
    """Log a completed shuffle run to the run log CSV.
    Parameters:
    - results_dir: Directory containing the run log
    - shuffle_storage_folder: Folder where shuffle parquet files were saved
    - n_shuf_per_subject: Number of shuffles per subject
    - n_subjects: Number of subjects processed
    - base_seed: Random seed used
    """
    shuffle_run_log_path = results_dir / "shuffle_run_log.csv"

    #find shuffle type from name of save

    run_info = {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "shuffle_type": str(shuffle_type),
                'shuffle_folder': str(shuffle_storage_folder),
                'n_shuffles_per_subject': n_shuf_per_subject,
                'n_subjects': n_subjects,
                'base_seed': base_seed}
    # Load existing log or create new one
    if shuffle_run_log_path.exists():
        run_log_df = pd.read_csv(shuffle_run_log_path)
        run_log_df = pd.concat([run_log_df, pd.DataFrame([run_info])], ignore_index=True)
    else:
        run_log_df = pd.DataFrame([run_info])
    # Save updated log
    run_log_df.to_csv(shuffle_run_log_path, index=False)
    print(f"Saved latest shuffle run to {shuffle_run_log_path}")

## function to read the saved log csv and determine the right folder to pick from 
def get_latest_shuffle_folder(results_dir, shuffle_type):
    """Get most recent shuffle folder for 'dff' or 'raster'."""
    log = pd.read_csv(results_dir / "shuffle_run_log.csv")
    log['type'] = log['shuffle_folder'].apply(lambda x: "dff" if "dff" in x else "raster" if "raster" in x else None)
    latest = log[log['type'] == shuffle_type].iloc[-1]
    return Path(latest['shuffle_folder']) 

## loading saved info df
def load_latest_shuffle_run(results_dir: Path, shuffle_storage_folder= None, shuffle_type_to_load = 'raster'):
    """    Load shuffles from the most recent run in the log.
    Parameters:
        results_dir: Directory containing the run log
        shuffle_storage_folder=
    Returns:
    - shuffle_storage_folder: Path to the shuffle folder
    - all_subject_shuffles: Loaded shuffle data
    - latest_run: Series with run metadata (timestamp, n_shuffles, etc.)
    """
    #new- v7- add check for what data type
    shuffle_storage_folder = get_latest_shuffle_folder(results_dir, shuffle_type_to_load)
    ## given last function folder 
    # Load all parquet files from that folder
    print(f" Loading from folder: {shuffle_storage_folder}")
    all_subject_shuffles = read_shuffle_parquet_from_folder(shuffle_storage_folder)
    return shuffle_storage_folder, all_subject_shuffles


# OPTIMIZATION 1: Numba-accelerated column rolling
from numba import jit, prange

@jit(nopython=True, parallel=True)
def random_roll_columns_numba(matrix, shifts):
    """
    Fast column rolling using Numba JIT compilation.
    
    Parameters:
    matrix: (n_frames, n_cells) array
    shifts: (n_cells,) array of shift amounts for each cell
    
    Returns:
    (n_frames, n_cells) array with each column circularly shifted
    """
    n_frames, n_cells = matrix.shape
    result = np.empty_like(matrix)
    
    # Parallel loop over cells
    for cell in prange(n_cells):
        shift = shifts[cell]
        for frame in range(n_frames):
            result[frame, cell] = matrix[(frame - shift) % n_frames, cell]
    
    return result

def random_roll_columns_fast(matrix, max_shift=None, random_seed=None):
    """
    Wrapper for numba-accelerated rolling that matches original API.
    """
    if random_seed is not None:
        rng = np.random.default_rng(random_seed)
    else:
        rng = np.random.default_rng()
    
    n_rows, n_cols = matrix.shape
    if max_shift is None:
        max_shift = n_rows - 1
    
    # Generate shifts (positive-only, matching MATLAB)
    shifts = rng.integers(1, max_shift + 1, size=n_cols)
    
    # Call numba-accelerated function
    return random_roll_columns_numba(matrix, shifts)

def get_mean_postoutcome_stage_activity(input_df, cell_col, label_col='task_stage', section_col = 'trial_section', post_outcome_label='post_outcome'):
    """ For groupby operation that returns mean activity for post-outcome stage of each cell in each section """
    mean_section_stage_act = input_df.groupby(by = [label_col, section_col])[cell_col].mean() #325 ms
    return mean_section_stage_act.loc[(slice(None),post_outcome_label),:]    

# old unoptimized version for reference
def create_shuffled_df_old(args):
    """Helper function for parallel processing"""
    df, cell_col, random_seed = args
    roll_data = random_roll_columns(df[cell_col].values, random_seed= random_seed)
    rolled_df = pd.DataFrame(roll_data, columns=cell_col, index=df.index).join(df.drop(columns = cell_col))
    mean_section_stage_act = get_mean_postoutcome_stage_activity(rolled_df, cell_col)
    #new- 11.8.25- add shuffle seed record 
    mean_section_stage_act['shuffle_seed'] = random_seed
    return mean_section_stage_act

# 1s per shuffle is current speed

def prepare_shuffle_data(df, cell_col):
    """
    Pre-convert sparse data to dense ONCE before parallel processing.
    Call this once per subject, then pass the result to create_shuffled_df_preconverted.

    Returns:
        tuple: (cell_data, task_stage, trial_section, index, cell_col)
    """
    cell_data = df[cell_col].values
    # Handle Sparse arrays: convert to dense numpy array with numeric dtype
    if cell_data.dtype == object:
        try:
            cell_data = df[cell_col].sparse.to_dense().to_numpy(dtype=np.float64)
        except AttributeError:
            cell_data = cell_data.astype(np.float64)

    return (
        cell_data,
        df['task_stage'].values,
        df['trial_section'].values,
        df.index,
        cell_col
    )

def create_shuffled_df_preconverted(args):
    """
    Optimized shuffle using pre-converted dense data.
    Use with prepare_shuffle_data() for best performance.

    Args:
        args: tuple of (prepared_data, random_seed) where prepared_data is from prepare_shuffle_data()
    """
    prepared_data, random_seed = args
    cell_data, task_stage, trial_section, index, cell_col = prepared_data

    # Roll using fast numba version (no conversion needed - already dense)
    rolled = random_roll_columns_fast(cell_data, random_seed=random_seed)

    # Create rolled DataFrame with metadata as Series (preserves index alignment)
    rolled_df = pd.DataFrame(rolled, columns=cell_col, index=index)
    rolled_df['task_stage'] = pd.Series(task_stage, index=index)
    rolled_df['trial_section'] = pd.Series(trial_section, index=index)

    # Use same groupby logic as OLD
    mean_section_stage_act = rolled_df[rolled_df['trial_section'] == 'post_outcome'].groupby(by=['task_stage', 'trial_section'])[cell_col].mean()
    # Add shuffle seed as a COLUMN (not row)
    mean_section_stage_act['shuffle_seed'] = random_seed

    return mean_section_stage_act

# OPTIMIZATION shuffle: Numpy-only shuffle processing (FIXED to match OLD output structure)
def create_shuffled_df_optimized(args):
    """Optimized version matching OLD output structure."""
    df, cell_col, random_seed = args

    # Extract numpy arrays once - convert sparse to dense if needed
    cell_data = df[cell_col].values
    # Handle Sparse arrays: convert to dense numpy array with numeric dtype
    if cell_data.dtype == object:
        try:
            cell_data = df[cell_col].sparse.to_dense().to_numpy(dtype=np.float64)
        except AttributeError:
            # Fallback: convert object array directly
            cell_data = cell_data.astype(np.float64)

    # Roll using fast numba version
    rolled = random_roll_columns_fast(cell_data, random_seed=random_seed)

    # Create rolled DataFrame
    rolled_df = pd.DataFrame(rolled, columns=cell_col, index=df.index)
    rolled_df['task_stage'] = df['task_stage']
    rolled_df['trial_section'] = df['trial_section']

    # Use same groupby logic as OLD
    mean_section_stage_act = rolled_df[
        rolled_df['trial_section'] == 'post_outcome'
    ].groupby(by=['task_stage', 'trial_section'])[cell_col].mean()

    # Add shuffle seed as a COLUMN (not row)
    mean_section_stage_act['shuffle_seed'] = random_seed

    return mean_section_stage_act

# random_roll_columns, non optimzed with Numba
def random_roll_columns(matrix, max_shift=None, random_seed=None):
    if random_seed is not None:
        rng = np.random.default_rng(random_seed)
    else:
        rng = np.random.default_rng()
    
    n_rows, n_cols = matrix.shape
    if max_shift is None:
        max_shift = n_rows - 1  # Match MATLAB: num_cols - 1
    
    # Generate POSITIVE-ONLY shifts from 1 to max_shift (matching MATLAB's randi)
    shifts = rng.integers(1, max_shift + 1, size=n_cols)  # 1 to max_shift inclusive
    
    # Apply shifts with wrapping
    rows = np.arange(n_rows)[:, np.newaxis]
    shifted_indices = (rows - shifts) % n_rows
    return matrix[shifted_indices, np.arange(n_cols)]

def random_roll_columns_OLD(matrix, max_shift=None, random_seed=None):
    """
    Roll each column up or down by a random amount.
    Parameters:
    matrix (np.ndarray): 2D input array (rows × columns)
    max_shift (int, optional): Maximum shift amount. If None, uses row count.
    random_seed (int, optional): For reproducible results.
    
    Returns:
    np.ndarray: Matrix with each column rolled independently.
    """
    if random_seed is not None:
        rng = np.random.default_rng(random_seed)
    else:
        rng = np.random.default_rng()
    
    n_rows, n_cols = matrix.shape
    if max_shift is None:
        max_shift = n_rows
    
    # Generate one random shift per column
    shifts = rng.integers(-max_shift, max_shift + 1, size=n_cols)
    # Create row indices for each column
    rows = np.arange(n_rows)[:, np.newaxis]  # Column vector of row indices    
    # Apply shifts with wrapping
    shifted_indices = (rows - shifts) % n_rows #if the shift size is > than the number of rows, it will wrap 
    # Use advanced indexing to get the rolled matrix
    return matrix[shifted_indices, np.arange(n_cols)]