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
                      datatype:str = 'raster', normalize:str = 'none'):
     # Create DataFrame from raster (cells × frames)
    normalize_options = ['min_max', 'baseline_zscore', 'none'] #could add zscore later
    #new- v5 11.21.25, allow datatype argument ('raster' or 'dff')
    print(f"Processing {datatype} of {dataset_obj['name']}: {dataset_obj[datatype].nbytes} bytes")
    
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
    
    #to avoid NaN, compute baseline activity first
    baseline_mask = raster_df['labels'] == 1  # Assuming label '1' indicates baseline period
    if normalize is not 'none':
        baseline_data = raster_df.loc[baseline_mask, cell_cols]
        baseline_mean = baseline_data.mean()
        baseline_std = baseline_data.std()

    # Add metadata columns
    #OPTIONAL- drop cells that are never active
    drop_inactive_cells = config['preprocessing']['drop_inactive_cells']
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
        print(f" Dropping cells with 0 activity {inactive_cells.index[inactive_cells].tolist()}")
        raster_df = raster_df.loc[:, active_cells.index[active_cells].tolist() + metadata_cols]
    
    #optiional normalization/zscore
    #run min max normalization on baseline_dff
    cell_cols = [col for col in raster_df.columns if col.startswith('cell_')]
    activity_data = raster_df[cell_cols]

    if normalize == 'min_max':
        min_vals = activity_data.min()
        max_vals = activity_data.max()
        normalized_dff = (raster_df[cell_cols] - min_vals) / (max_vals - min_vals)
        raster_df[cell_cols] = normalized_dff

    if normalize == 'baseline_zscore':
        zscored_dff = (raster_df[cell_cols] - baseline_mean[cell_cols]) / baseline_std[cell_cols]
        raster_df[cell_cols] = zscored_dff
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

def read_shuffle_parquet_from_folder(shuffle_storage_folder: Path) -> Dict[str, pd.DataFrame]:
    pass


# ==============================================================================
# SECTION 3: Statistical Operations
# ==============================================================================

def get_intercol_corrs(df: pd.DataFrame, stage_names: List[str], suffix1: str, suffix2: str) -> pd.DataFrame:
    pass


# ==============================================================================
# SECTION 4: Time-Series Extraction and Reshaping
# ==============================================================================

def extract_trial_windows(df,
                          pre_frames=60,
                          post_frames=300) -> pd.DataFrame:
    pass


def pivot_trial_windows(windowed_df,
                        samples_col = 'trial_window_frame',
                        frame_prefix:str = 'f_',
                        new_cell_col_name:str = 'cell') -> pd.DataFrame:
    pass


# ==============================================================================
# SECTION 5: Metadata Extraction
# ==============================================================================

def get_first_active_stage(row, stage_order, non_enriched_label = 'Never'):
    pass


# ==============================================================================
# SECTION 6: Subject Metadata Extraction
# ==============================================================================

def get_genotype(subject_name: str) -> str:
    pass


def get_session_type(subject_name: str) -> str:
    pass


def get_subject_metadata(subject_name: str) -> Dict[str, str]:
    pass
