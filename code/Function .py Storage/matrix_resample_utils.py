# matrix_resample_utils.py
#!/usr/bin/env python3
import numpy as np
import pandas as pd


def fast_pack_data_local(class_0_mat, class_1_mat,class_0_value, class_1_value):
    #TO- given 2 objects containg ['matrix', 'labels'] fields, join each field's content together and export (Transposing for easier use later)
    #returns numpy array which = transpose of concat. data matrix and labels
    concat_matrix = class_0_mat.join(class_1_mat, how = 'inner', lsuffix = '_c0', rsuffix = '_c1') #use inner to avoid having missing cells in a condition if dataset missing that phase's trials
    #outer keeps empty cells from another dataset, which is OBVIOUS clue if condition 1 is e.g. missing early IA error cells from some datasets
    class_label_0 = make_class_label_vector(class_0_mat, class_0_value)
    class_label_1 = make_class_label_vector(class_1_mat, class_1_value)
    concat_labels =  np.concatenate([class_label_0,class_label_1 ]) #concat class 0 and 1 label vector and optionally add as final row of matrix (to shuffle it exactly the same)
    return concat_matrix, concat_labels #transpose matrix and labels to avoid having to ranspose later

#reample data
def make_class_label_vector(class_matrix, class_val):
    class_labels = np.repeat(class_val, class_matrix.shape[1])
    return class_labels


def resample_concat_dict_of_activity_mats_w_subsample(dict_of_activity_dfs, num_resample,local_rng, subsample_range):
    """TO: given a dict of activity matrices where rows = units, cols = frames and scalar N, resample it N times into a list. 
    Each list elem = activity from a diff subj (to allow for varying len datasets)"""
    #pandas dataframe is INCLUSIVE of the end value, so you are including it in the subsample
    resampled_dict_list =[resample_unit_timeseries_df(d.loc[:,subsample_range], num_resample,local_rng) for d in dict_of_activity_dfs.values()]
    resampled_df = pd.concat(resampled_dict_list, axis = 0)
    return resampled_df

def resample_ensemble_stage_activity(class_matrix_store,
                                     n_frames_to_draw:int=500,
                                     ensemble:str = "",
                                     geno:str="",
                                     stages_to_resample:list  = ['Early_IA_Correct', 'Early_RS_Correct', 'Early_IA_Error', 'Early_RS_Error'],
                                     **kwargs):
    '''To iterate over specified stages and return dict containing N resampled frame for each stage. Requires 'resample_into_class_matrix'
    '''
    ensemble_resample_in_phase_dict = {}
    for class_name in stages_to_resample: #store the versions for this bootstrap run
        class_mat = resample_into_class_matrix(class_matrix_store,n_frames_to_draw,ensemble, class_name, geno)
        ensemble_resample_in_phase_dict[class_name] = class_mat
        
    return ensemble_resample_in_phase_dict

def resample_into_class_matrix(class_matrix_store,n_resample, ensemble_name, class_name, geno_day_curr, subsample_range = []):
    local_rng = np.random.default_rng() #create a Generator instance with default_rng
    activity_dict = class_matrix_store[ensemble_name][class_name][geno_day_curr]
    ## add logic for ability to subsample what frame you actually use 
    if len(subsample_range) == 0:
        subsample = False
    else:
        subsample = True
    if subsample:
        class_matrix = resample_concat_dict_of_activity_mats_w_subsample(activity_dict,n_resample,local_rng, subsample_range)
    else:
        class_matrix = resample_combine_dict_of_activity_dfs(activity_dict, n_resample,local_rng)
    return class_matrix

def resample_combine_dict_of_activity_dfs(dict_of_activity_dfs, num_resample,local_rng):
    """TO: given a dict of activity matrices where rows = units, cols = frames and scalar N, resample it N times into a list. 
    Each list elem = activity from a diff subj (to allow for varying len datasets)"""

    resampled_dict_list =[resample_unit_timeseries_df(d, num_resample,local_rng) for d in dict_of_activity_dfs.values()]
    #NO LONGER RETURNS TUPLES 9/26/24/ #above returns list of tuples (resample df, resample IDs)
    # resampled_df = pd.concat([e for e in resampled_dict_list], axis = 0)
    resampled_df = pd.concat(resampled_dict_list, axis = 0)
    # class_idx = [e[1] for e in resampled_dict_list]
    return resampled_df

def resample_unit_timeseries_df(input_timeseries_df, num_resample,local_rng):
    #TO- retain original tseries index, but join to newly resample df
    resample_matrix = resample_matrix_rows_w_replace(input_timeseries_df.values, num_resample, local_rng) 
    resample_unit_df = pd.DataFrame(data = resample_matrix, index = input_timeseries_df.index)
    return resample_unit_df

def resample_matrix_rows_w_replace(input_matrix, num_resample,local_rng):
    """ returns resampled matrix, and indices used to generate resample. feed in pre-created resample """
    array_rows, array_cols = input_matrix.shape #get dims of input_matrix #assume that array_rows = num_units
    num_units = array_rows #assme that the num rows in the tseries = num units you sample from in dataset
    resample_idx = local_rng.choice(array_cols, size = (num_units,num_resample),
                                     replace = True) #output shape: (num_units,num_resample)
    resampled_matrix = np.take_along_axis(input_matrix, resample_idx, axis=1) #axis = 1 means slices  in rows
    #Take values from input mat by matching 1d index vals in data slices.
    return resampled_matrix