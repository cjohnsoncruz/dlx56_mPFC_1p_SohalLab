# preprocessing_utils.py
"""
Helper functions for neural data preprocessing.
Works on data already imported+ cleaned from matlab .mat.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Any, Dict, Optional
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from matlab_obj_to_python import load_matlab_object,  truncate_post_outcome_to_15s, label_frame_sections_df, add_task_stage_to_raster_df


# ==============================================================================
# SECTION 1: MATLAB to DataFrame Conversion
# ==============================================================================

def dataset_obj_to_df(dataset_obj, config, analysis_config,
                      datatype:str = 'raster',
                        normalize:str = 'none',
                        drop_inactive_cells = None):
     # Create DataFrame from raster (cells × frames)
    normalize_options = ['min_max', 'baseline_zscore', 'none'] #could add zscore later
    #new- v5 11.21.25, allow datatype argument ('raster' or 'dff')
    #note- if you used raster input, min_max normalization here will NOT be meaningful, pre-binning. raster is binary at this stage
    
    input_data = dataset_obj[datatype]
    #smooth data with gaussian filter if dff
    if datatype == 'dff': # C = smoothdata(C, 2, 'gaussian', [1,1]);
        input_data = gaussian_filter1d(input_data, sigma=1, axis=0, truncate=1.0) #truncate=1.0 means the kernel extends only 1*sigma on each side
    #validate inputs
    if normalize not in normalize_options:
        raise ValueError(f"Normalization option '{normalize}' not recognized. Choose from {normalize_options}.")    
    
    #setup dataset df 
    dtype_for_datatype = {'raster': 'Sparse[int]', 'dff' : 'float32'}
    raster_df = pd.DataFrame(
        input_data, #removed transpose, as earlier transpose was incorrect
        index=[f'frame_{i}' for i in range(dataset_obj[datatype].shape[0])],
        columns = [f'cell_{i+1}' for i in range(dataset_obj[datatype].shape[1])],
        dtype = dtype_for_datatype[datatype])
    
    #add labels
    raster_df['labels'] = dataset_obj['labels']
    raster_df['labels'] = raster_df['labels'].astype('Int16')
    cell_cols = [col for col in raster_df.columns if col.startswith('cell_')]
    
    #(Only applicable to DFF, due to binary raster sparsity) to avoid NaN, compute baseline activity first.
    baseline_mask = raster_df['labels'] == 1  # Assuming label '1' indicates baseline period
    if (datatype == 'dff') & (normalize != 'none'):
        baseline_data = raster_df.loc[baseline_mask, cell_cols]
        baseline_mean = baseline_data.mean()
        baseline_std = baseline_data.std()

    # Add metadata columns
    if drop_inactive_cells == None:
        drop_inactive_cells = config['preprocessing']['drop_inactive_cells']     #OPTIONAL- drop cells that are never active
    #cell Id is represented as col name 
    raster_df= raster_df.assign(**{'normalized': normalize, 'datatype': datatype,
                      'subject_name': dataset_obj['name'],
                      'geno': dataset_obj['geno'],
                      'session': dataset_obj['session'],
                      'drop_inactive_cells' : drop_inactive_cells,
                      })
    
    # #add task info
    raster_df = add_task_stage_to_raster_df(raster_df, analysis_config)
    raster_df['trial_section'] = label_frame_sections_df(raster_df, 'labels', section_names=analysis_config.trial_section_names) #annotate pre,post,ITI
    raster_df = truncate_post_outcome_to_15s(raster_df, truncate_post = True)#new- truncate post-outcome to 15 seconds long, and rename rest to truncated
    metadata_cols = [c for c in raster_df.columns if not c.startswith('cell_')]
    
    if drop_inactive_cells:
        #get timepoints you care about for determining inactivity
        selection_mask = raster_df['trial_section'] == 'post_outcome' # print( raster_df.loc[selection_mask, cell_cols].sum() )
        active_cells = raster_df.loc[selection_mask, cell_cols].sum() > 0
        inactive_cells =  raster_df.loc[selection_mask, cell_cols].sum() == 0
        print(f" Dropping {inactive_cells.sum()} cells w. 0 activity: {inactive_cells.index[inactive_cells].tolist()}")
        raster_df = raster_df.loc[:, active_cells.index[active_cells].tolist() + metadata_cols]
    
    #optiional normalization/zscore
    cell_cols = [col for col in raster_df.columns if col.startswith('cell_')]
    activity_data = raster_df[cell_cols]

    if normalize == 'min_max':     #run min max normalization on baseline_dff
        min_vals = activity_data.min()
        max_vals = activity_data.max()
        normalized_dff = (raster_df[cell_cols] - min_vals) / (max_vals - min_vals)
        raster_df[cell_cols] = normalized_dff

    if normalize == 'baseline_zscore':
        zscored_dff = (raster_df[cell_cols] - baseline_mean[cell_cols]) / baseline_std[cell_cols]
        raster_df[cell_cols] = zscored_dff

    print(f"Processed {datatype} of {dataset_obj['name']}: {dataset_obj[datatype].nbytes} bytes")
    return raster_df

def transform_all_datasets(loaded_objects:List[Dict[str, Any]], config, analysis_config,
                            datatype:str = 'raster', normalize:str = 'none') -> Dict[str, pd.DataFrame]:
    """ Loop over imported subject rasters and create pandas DataFrames
    Returns dictionary of DataFrames keyed by subject name """
    raster_dataframes = {}
    for obj in loaded_objects:    # Create DataFrame from raster (cells × frames)
        raster_df = dataset_obj_to_df(obj,config, analysis_config, datatype = datatype, normalize = normalize)
        raster_dataframes[obj['name']] = raster_df
    print(f"\nTotal DataFrames created: {len(raster_dataframes)}")
    return raster_dataframes

# ==============================================================================
# SECTION 2: File I/O Operations
# ==============================================================================

#function to read parquet shuffle df files
def read_shuffle_parquet_from_folder(shuffle_storage_folder: Path) -> Dict[str, pd.DataFrame]:
    """ Reads  parquet files in folder, containing shuffled mean activity DataFrame """
                # Load all parquet files from that folder

    all_subject_shuffles = {}
    for parquet_file in shuffle_storage_folder.glob("*_shuffled_mean_activity.parquet"):
        subject_name = parquet_file.stem.replace('_shuffled_mean_activity', '')
        all_subject_shuffles[subject_name] = pd.read_parquet(parquet_file)
        print(f" Loaded: {subject_name}")
    
    print(f"Loaded {len(all_subject_shuffles)} subjects from previous run")
    return all_subject_shuffles

# ==============================================================================
# SECTION 3: Statistical Operations
# ==============================================================================

def get_intercol_corrs(df: pd.DataFrame, stage_names: List[str], suffix1: str, suffix2: str) -> pd.DataFrame:
    """ Calculate correlations between columns with specified suffixes for each stage name.
    Inputs:
    df : DataFrame with columns to correlate
    stage_names : list of stage names to look for
    suffix1 : first suffix to append to stage names
    suffix2 : second suffix to append to stage names

    Returns: DataFrame of correlations"""
    
    correlations = {}
    for stage in stage_names:
        col1 = f"{stage}{suffix1}"
        col2 = f"{stage}{suffix2}"
        if col1 in df.columns and col2 in df.columns:
            corr_value = df[col1].corr(df[col2])
            correlations[stage] = corr_value
        else:
            print(f"Warning: Columns {col1} or {col2} not found in DataFrame.")
    
    corr_df = pd.DataFrame.from_dict(correlations, orient='index', columns=['Correlation'])
    return corr_df


# ==============================================================================
# SECTION 4: Time-Series Extraction and Reshaping
# ==============================================================================
from preprocess_data import hyper_param_dict, bin_rotate_timeseries, get_numeric_cols_timeseries, get_unit_mean_timeseries_by_phase, drop_end_bins_of_trials, drop_start_bins_of_trials, add_enriched_in_curr_phase_col, get_subject_stage_info_df
from helper_functions import annotate_csv, run_min_max_norm_on_timeseries


# #OLD code
def extract_trial_windows(df, 
                         pre_frames=100,      # Changed from 60 to match MATLAB's 5 seconds
                         post_frames=300,     # Matches MATLAB's 15 seconds
                         trim_pre_to=300):    # New: trim pre-outcome to 300 frames first (like MATLAB)
    """
    Extract trial windows matching MATLAB's behavior.
    
    MATLAB flow:
    1. Slice by labels to get pre_outcome frames
    2. Trim to last 300 frames (15 seconds)
    3. Take last 100 frames (5 seconds) for joining with post
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with frame-level data, must have 'trial_section' column
    pre_frames : int
        Number of pre-outcome frames to keep (default 100 = 5 seconds at 20Hz)
    post_frames : int  
        Number of post-outcome frames to keep (default 300 = 15 seconds at 20Hz)
    trim_pre_to : int
        First trim pre-outcome to this many frames before extracting final pre_frames
        (default 300 = 15 seconds, matches MATLAB's trim_params.trial_len)
    
    Returns:
    --------
    pd.DataFrame with trial windows extracted
    """
    print(f"using new extract trial window code:")
    # Validation: Check monotonicity within each trial
    grouped = df.groupby(['subject_name', 'session', 'trial_num'])
    
    for trial_id, trial_data in grouped:
        frame_nums = trial_data.index.str.extract(r'frame_(\d+)')[0].astype(int)
        if not frame_nums.is_monotonic_increasing:
            raise ValueError(f"Non-monotonic indices in trial {trial_id}")
    
    full_frame_range = list(range(-pre_frames, 0)) + list(range(1, post_frames + 1))
    trial_windows = []
    
    for trial_id, trial_data in grouped:
        # Step 1: Get pre-outcome section (all frames)
        pre_all = trial_data[trial_data['trial_section'] == 'pre_outcome']
        
        # Step 2: Trim to last 'trim_pre_to' frames (matches MATLAB's trim to 300)
        pre_trimmed = pre_all.tail(trim_pre_to)
        
        # Step 3: From trimmed pre, take last 'pre_frames' frames (matches MATLAB's last 100)
        pre = pre_trimmed.tail(pre_frames)
        
        # Step 4: Get post-outcome frames (first N frames)
        post = trial_data[trial_data['trial_section'] == 'post_outcome'].head(post_frames)
        
        # Create frame indices
        n_pre = len(pre)
        n_post = len(post)
        pre_indices = list(range(-n_pre, 0))
        post_indices = list(range(1, n_post + 1))
        
        # Add indices before concatenating (avoids fragmentation)
        pre_with_idx = pre.assign(trial_window_frame=pre_indices)
        post_with_idx = post.assign(trial_window_frame=post_indices)
        
        # Concatenate
        combined = pd.concat([pre_with_idx, post_with_idx], ignore_index=True)
        
        # Reindex to full range - automatically pads with NaN for truncated trials
        combined = combined.set_index('trial_window_frame').reindex(full_frame_range).reset_index()
        
        # Forward-fill metadata (they're constant within trial)
        metadata = ['subject_name', 'session', 'trial_num', 'geno', 'task_stage', 'normalized', 'datatype']
        for col in [c for c in metadata if c in combined.columns]:
            combined[col] = combined[col].ffill()
        
        trial_windows.append(combined)
    
    return pd.concat(trial_windows, ignore_index=True)

# def extract_trial_windows(df, pre_frames=60, #default=60
#                             post_frames= 300, #default= 300
#                             ) -> pd.DataFrame:
#     """Extract last N pre-outcome and M post-outcome frames for each trial, padded to consistent length."""
    
#     # Validation: Check monotonicity within each trial
#     grouped = df.groupby(['subject_name', 'session', 'trial_num'])
    
#     for trial_id, trial_data in grouped:
#         frame_nums = trial_data.index.str.extract(r'frame_(\d+)')[0].astype(int)
#         if not frame_nums.is_monotonic_increasing:
#             raise ValueError(f"Non-monotonic indices in trial {trial_id}")
    
#     full_frame_range = list(range(-pre_frames, 0)) + list(range(1, post_frames + 1))
#     trial_windows = []
    
#     for trial_id, trial_data in grouped:
#         pre = trial_data[trial_data['trial_section'] == 'pre_outcome'].tail(pre_frames)
#         post = trial_data[trial_data['trial_section'] == 'post_outcome'].head(post_frames)
        
#         # Create frame indices
#         n_pre = len(pre)
#         n_post = len(post)
#         pre_indices = list(range(-n_pre, 0))
#         post_indices = list(range(1, n_post + 1))
        
#         # Add indices before concatenating (avoids fragmentation)
#         pre_with_idx = pre.assign(trial_window_frame=pre_indices)
#         post_with_idx = post.assign(trial_window_frame=post_indices)
        
#         # Concatenate
#         combined = pd.concat([pre_with_idx, post_with_idx], ignore_index=True)
        
#         # Reindex to full range - automatically pads with NaN for truncated trials
#         combined = combined.set_index('trial_window_frame').reindex(full_frame_range).reset_index()
        
#         # Forward-fill metadata (they're constant within trial)
#         metadata = ['subject_name', 'session', 'trial_num', 'geno', 'task_stage', 'normalized', 'datatype']
#         for col in [c for c in metadata if c in combined.columns]:
#             combined[col] = combined[col].ffill()
        
#         trial_windows.append(combined)
    
#     return pd.concat(trial_windows, ignore_index=True)

def pivot_trial_windows(windowed_df, 
                        samples_col = 'trial_window_frame',
                        frame_prefix:str = 'f_',
                        new_cell_col_name:str = 'cell') -> pd.DataFrame:
    """  Pivot so each row is one cell from one trial. Columns: metadata + frame_1, frame_2, ..., frame_360 """
    
    cell_cols = [col for col in windowed_df.columns if col.startswith('cell_')]
    # Melt: convert cell columns to rows
    melted = windowed_df.melt(id_vars=['trial_num', samples_col], value_vars=cell_cols, var_name=new_cell_col_name, value_name='activity')
    # Pivot: convert frames to columns
    pivoted = melted.pivot(index=['trial_num', new_cell_col_name],columns=samples_col,values='activity')
    #detect if frame is negative or positive and rename columns # Rename columns: negative = -f_N (pre), positive = f_N (post)
    new_columns = []
    for frame in pivoted.columns:
        if frame < 0:
            new_columns.append(f'-f_{abs(frame)}')  # -60 -> -f_60, -1 -> -f_1
        else:
            new_columns.append(f'f_{frame}')  # 1 -> f_1, 300 -> f_300
    # rename columns
    pivoted.columns = new_columns
    pivoted = pivoted.reset_index()
    
    # Add back metadata
    metadata_cols_kept = ['trial_num', 'subject_name', 'session', 'geno', 'task_stage', 'normalized', 'datatype']
    metadata_cols_kept = [col for col in metadata_cols_kept if col in windowed_df.columns]
    metadata_map = windowed_df[metadata_cols_kept].drop_duplicates()
    pivoted = pivoted.merge(metadata_map, on='trial_num', how='left')
        
    # Value spot check
    sample_trial = pivoted['trial_num'].iloc[0]
    sample_cell = cell_cols[0]
    frame_cols = [col for col in pivoted.columns if col.startswith(('f_', '-f_'))]
    
    original = windowed_df[windowed_df['trial_num'] == sample_trial][sample_cell].values
    pivoted_vals = pivoted[(pivoted['trial_num'] == sample_trial) & (pivoted[new_cell_col_name] == sample_cell)][frame_cols].values.flatten()
    
    # TESTS
    assert not pivoted[['trial_num', new_cell_col_name]].duplicated().any(), "Found duplicate trial-cell combinations!"
    assert np.allclose(original, pivoted_vals, equal_nan=True), "Data corruption detected!"
    
    return pivoted
# ==============================================================================
# SECTION 5: timeseries df  Extraction
# ==============================================================================

## main time-series df creation function for datasets processed in python
def create_subject_trial_tseries_df(input_df: pd.DataFrame,
                                    ens_matrix: pd.DataFrame,
                                    window_to_bin = 5,
                                    n_sec_to_rotate = 0,
                                    cell_col = 'cell',
                                    cols_to_drop= None,
                                    stage_col = 'task_phase_vec',
                                    stage_names = None,
                                    config = None, 
                                    ) -> pd.DataFrame:
    """ Create trial-cell time-series DataFrame for one subject, with ensemble info joined. For python native created dfs
    Inputs:
    raster_df : DataFrame with one row per frame
    """
    #default args
    if cols_to_drop is None:
        cols_to_drop = ['threshold_with_shuffle','peak_dff_threshold_percentile','drop_low_value_peak_events','cutoff_filter','peak_event_cutoff_percentile']   
    if stage_names is None:
        stage_names = ['Early_IA_Error', 'Early_IA_Correct', 'Late_IA', 'Early_RS_Error', 'Early_RS_Correct','Late_RS']
    if config == None: 
        print("Missing config input!")  
    # extract trial windows from df, removing excess frames
    #old, head dependent version:
    # trim_df = extract_trial_windows(input_df, pre_frames=config['timeseries']['pre_frames'], post_frames= config['timeseries']['post_frames'])
    # CHANGE TO:
    trim_df = extract_trial_windows(input_df,
                                    pre_frames=100,      # 5 seconds to match MATLAB
                                    post_frames=300,     # 15 seconds (already correct)
                                    trim_pre_to=300)     # Trim pre first (like MATLAB)
    
    #reshape df into long format: one row per trial-cell, columns = time-series frames
    outcome_post = pivot_trial_windows(trim_df).rename(columns={'task_stage': stage_col})
    outcome_post['neuron_id'] = outcome_post['subject_name'] + '-' + outcome_post[cell_col].str.replace('cell_','') 
    outcome_post =outcome_post.drop([x for x in cols_to_drop if x in outcome_post], axis = 1).dropna(subset = [stage_col])
    annotate_csv(outcome_post, 'subject_name')

    ## begin preprocess- bin and rotate timeseries 
    outcome_post = bin_rotate_timeseries(outcome_post, window_size = window_to_bin, rotate_by = n_sec_to_rotate)
    outcome_post = outcome_post.join(ens_matrix, on='neuron_id', how='left', rsuffix='_ens') #join dff timeseries with ensemble info
    #drop time-series not belonging to any task stage , aka the 0 task stage 
    outcome_post['any_enrichment']= outcome_post[stage_names].sum(axis = 1)
    outcome_post = outcome_post[outcome_post[stage_col].isin(stage_names)]
    trial_tseries_df_raw = add_enriched_in_curr_phase_col(outcome_post, stage_col)
    return trial_tseries_df_raw
# 