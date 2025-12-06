# matlab_obj_to_python.py contains functions for loading and checking MATLAB .mat files
## Matlab file handling functions:
import h5py
import pandas as pd
from pathlib import Path
import numpy as np
from trial_detection import return_trial_num_at_frame, build_phase_masks, get_trial_stage_map

## TASK STAGE ANNOTATION FUNCTIONS for python originating dfs
def add_task_stage_to_raster_df(raster_df, analysis_config):
    """ Joins all the trial stage functions into one function for ease of use (function imported elsewhere).2s per raster 
    #workflow: 
        # 1) Call "trial num at frame" function
        # 2. Add trial number to raster_df
        # 3. drop frames that are not in a trial
        # 4. Add task stage to raster_df based off trial number at frame
    """
    stage_names = analysis_config.task_phase_names
    # 1. Transform frame label vector into trial vector
    labels = raster_df['labels']
    trial_num_at_frame, _, num_trials = return_trial_num_at_frame(labels)
    raster_df.loc[:, 'trial_num'] = trial_num_at_frame 

    # 2. Add trial number to raster_df
    # Or filter in-place and drop:
    raster_df.drop(raster_df[raster_df['trial_num'] == 0].index, inplace=True) # raster_df = raster_df[raster_df['trial_num'] > 0].copy() #  dropping trial_num == 0
    # 4. Add task stage to raster_df based off trial number at frame
    stage_dict = build_phase_masks(labels,analysis_config)
    #5. map trial num to stage
    trial_stage_map = get_trial_stage_map(stage_dict, stage_names, num_trials)
    raster_df.loc[:, 'task_stage'] = raster_df['trial_num'].map(trial_stage_map)
    return raster_df

def label_frame_sections_df(df: pd.DataFrame, label_col: str,*,
                            section_names=("pre_outcome", "post_outcome", "ITI"),
                            ):
    """    Vectorized: assign each frame one of {pre_outcome, post_outcome, ITI}.

    Label assignments match MATLAB's slice_trim_raster behavior:
    - IA pre_outcome: labels 2, 3, 4 (MATLAB: 2 <= labels <= 4)
    - IA post_outcome: labels 5, 6, 7 (MATLAB: 4 <= labels <= 7, but 4 is also in pre)
    - RS pre_outcome: labels 9, 10, 11 (MATLAB: 9 <= labels <= 11)
    - RS post_outcome: labels 12, 13, 14 (MATLAB: 11 <= labels <= 14, but 11 is also in pre)

    Note: MATLAB includes boundary labels (4, 11) in BOTH sections. Since Python
    requires mutually exclusive categories, we assign boundary labels to pre_outcome
    to match MATLAB's pre-outcome extraction for time-series analysis.

    Inputs:
    df : DataFrame with one row per frame
    label_col : name of column holding per-frame integer labels
    section_names : (pre_outcome, post_outcome, ITI)

    Returns:    pd.Series (object) of section names aligned to df.index """
    pre_outcome, post_outcome, iti = section_names
    labels = df[label_col].to_numpy()
    out = np.full(labels.shape[0], None, dtype=object)

    # IA ranges (2–8) - label 4 goes to pre_outcome to match MATLAB
    ia_pre  = (labels >= 2)  & (labels <= 4)     # pre_outcome: labels 2, 3, 4
    ia_post = (labels >= 5)  & (labels <= 7)     # post_outcome: labels 5, 6, 7
    ia_iti  = (labels == 8)                      # ITI

    # RS ranges (9–15) - label 11 goes to pre_outcome to match MATLAB
    rs_pre  = (labels >= 9)  & (labels <= 11)    # pre_outcome: labels 9, 10, 11
    rs_post = (labels >= 12) & (labels <= 14)    # post_outcome: labels 12, 13, 14
    rs_iti  = (labels == 15)                     # ITI

    # No overlap now, order doesn't matter
    out[ia_pre  | rs_pre]  = pre_outcome
    out[ia_post | rs_post] = post_outcome
    out[ia_iti  | rs_iti]  = iti
    return out

def truncate_post_outcome_to_15s(raster_df, fps=20, max_seconds=15, truncate_post = True):
    """     Truncate post_outcome periods to first 15 seconds (300 frames at 20fps). Modifies task_stage labels for frames beyond truncation.    """
    max_frames = fps * max_seconds  # 300 frames
    
    raster_df['truncated_post'] =  truncate_post # New column to indicate truncation
    if truncate_post: 
        # For each trial's post_outcome section
        post_outcome_mask = raster_df['trial_section'] == 'post_outcome'
        
        for trial in raster_df['trial_num'].unique():
            if trial <= 0:
                continue
                
            # Get post_outcome frames for this trial
            trial_post = raster_df[post_outcome_mask & (raster_df['trial_num'] == trial)]
            if len(trial_post) == 0:
                continue
                
            # Get frame indices (they're sorted)
            frame_indices = trial_post.index
            
            # Mark frames beyond first 300 as truncated
            if len(frame_indices) > max_frames:
                frames_to_truncate = frame_indices[max_frames:]
                raster_df.loc[frames_to_truncate, 'task_stage'] = 'truncated_post_outcome'
        
    return raster_df


## POST-IMPORT ANNOTATION FUNCTIONS- 

## RAW FILE IMPORT AND CHECKING FUNCTIONS
def check_corrupted_files(loaded_objects, failed_files):
    # Optional Investigate corrupted files
    if len(failed_files) == 0:
        print("No failed files to investigate.")
        return
    
    for fname in failed_files:
        filepath = source_dataset_location / fname
        
        print(f"\n📁 {fname}")
        
        if not filepath.exists():
            print("   File does not exist!")
            continue
        
        # Check file size
        size_bytes = filepath.stat().st_size
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024
        
        print(f"  Size: {size_bytes:,} bytes ({size_mb:.2f} MB)")
        # Read first bytes to check file signature
        with open(filepath, 'rb') as f:
            header = f.read(100)
        
        # Check for MATLAB file signatures
        print(f"  First 20 bytes (hex): {header[:20].hex()}")
        # HDF5 files should start with \x89HDF\r\n\x1a\n
        if header[:4] == b'\x89HDF':
            print("  ✓ Valid HDF5 signature")
        elif header[:4] == b'MATL':
            print("  ⚠️ Old MATLAB format (v5/v6) - needs scipy.io")
        else:
            print(f"   Unknown file signature - file may be corrupted")
            print(f"     Expected: b'\\x89HDF' or b'MATL'")
            print(f"     Got: {header[:4]}")
        
        # Try to detect if file is truncated
        if size_mb < 1:
            print(f"  ⚠️ WARNING: File is unusually small ({size_mb:.2f} MB)")

    # Compare with a working file
    print("COMPARISON WITH WORKING FILES:")
    # Get file sizes of all working files
    working_sizes = []
    for obj in loaded_objects[:5]:
        fname = obj['name'] + '_dataset_object.mat'
        fpath = source_dataset_location / fname
        if fpath.exists():
            size_mb = fpath.stat().st_size / 1024 / 1024
            working_sizes.append(size_mb)
            print(f"  {fname}: {size_mb:.2f} MB")

    if working_sizes:
        avg_size = sum(working_sizes) / len(working_sizes)
        print(f"\n  Average working file size: {avg_size:.2f} MB")

def load_matlab_object(filepath):
    """Load MATLAB dataset_with_spatial_ROI object from .mat file"""
    # Parse metadata from filename
    filename = filepath.stem.replace('_dataset_object', '')
    parts = filename.split('_')
    
    # Extract name, geno from filename (e.g., "10_3_HET_RS1")
    name = filename
    if len(parts) >= 3:
        geno = parts[2]  # HET or WT
        session = parts[3] if len(parts) > 3 else 'RS1'
    else:
        geno = "UNKNOWN"
        session = "RS1"
    
    try:
        with h5py.File(filepath, 'r') as f:            # Load numeric data from known datasets
            raster = f['#refs#']['i'][()]  # (time, cells)
            # Get deduplicated flag from group x
            deduplicated = f['#refs#']['x']['deduplicated'][0, 0] if 'deduplicated' in f['#refs#']['x'] else False
            # Create object dictionary
            obj = {
                'name': name,
                'geno': geno,
                'session': session,
                'geno_day': None,  # Will need to be set externally if needed
                'raster': raster,  # DON"T  Transpose to (cells, time), as df transposes later
                'deduplicated': bool(deduplicated),
                'good_cells': f['#refs#']['k'][()] if 'k' in f['#refs#'] else None,  # Cell IDs
                'labels': f['#refs#']['j'][()] if 'j' in f['#refs#'] else None,  # Trial/time info
                'dff': f['#refs#']['p'][()] if 'p' in f['#refs#'] else None,  # Full C matrix (time, all_components)
            }
            #as dff is pre-cell selection, we can select good cells here if available
            if obj['dff'] is not None and obj['good_cells'] is not None:
                obj['dff'] = obj['dff'][:, obj['good_cells'].flatten().astype(int)-1]  # Adjust for 0-based indexing
            else:
                print(f"  WARNING: 'dff' or 'good_cells' missing in {filepath.name}, cannot subset dff.")
            # Load spatial info if present
            if 'n' in f['#refs#']:
                spatial = f['#refs#']['n']
                obj['spatial_weights'] = spatial['spatial_weights'][()] if 'spatial_weights' in spatial else None
                obj['temporal_weights'] = spatial['temporal_weights'][()] if 'temporal_weights' in spatial else None
                obj['user_labels'] = spatial['user_labels'][()] if 'user_labels' in spatial else None
                obj['subject_name'] = spatial['subject_name'][()] if 'subject_name' in spatial else None
            
            return obj
    
    except (OSError, KeyError) as e:
        print(f"  ERROR loading {filepath.name}: {e}")
        return None