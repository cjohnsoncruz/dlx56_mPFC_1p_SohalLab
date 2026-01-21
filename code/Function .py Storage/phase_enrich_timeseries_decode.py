#phase_enrich_timeseries_decode.py
import numpy as np
import pandas as pd 
import itertools
import matplotlib
from matplotlib import pyplot as plt
import seaborn as sns
from helper_functions import *
# from .pseudopop_creation import resample_unit_timeseries_df

# local subfunctions
# fast pack version 
# #pseudopopulation creation methods
def horzcat_all_trials(timeseries_df, tseries_cols, unit_col_name, drop_pre_outcome = None):
    # timeseries_df, dataframe containign long view where eah crow is 1 cell's tseries for a given trial (+ info about phase you're in, etc)
    #  tseries_cols- list of column names that contain the contiguous numeric data
    if drop_pre_outcome:#dropping negative values that come ftrompre-decision
        tseries_cols = [col for col in tseries_cols if "-" not in col] 
    trial_slice_storage = []#create lists for storage of
    for trial in timeseries_df.trial_num.unique():
        trial_slice = timeseries_df.loc[timeseries_df.trial_num == trial].set_index(unit_col_name)
        trial_slice_storage.append(trial_slice.loc[:,tseries_cols]) #needs to be stored in list because you will be transposing themt o be concat horizontally
    combined_slices = pd.concat(trial_slice_storage, axis = 1)
    return combined_slices
# ## helper functions
def get_dataset_names_in_geno(dataset_name_by_geno_day,geno_day):
    datasets_in_geno = dataset_name_by_geno_day.loc[dataset_name_by_geno_day.geno_day == geno_day,'name'].values[0] #get name of datasets in current geno_day setup
    return datasets_in_geno

 ## imported subfunc for cuDF speedup
def get_tseries_of_dataset(timeseries_df, expt_name):
    #get time-series that are occurign in phase of interest
    dataset_df_slice = timeseries_df.loc[timeseries_df.name == expt_name]
    return dataset_df_slice

def get_tseries_in_phase(timeseries_df, phase_name):
    phase_dataset_df_slice = timeseries_df.loc[timeseries_df.task_phase_vec == phase_name]
    return phase_dataset_df_slice

def get_tseries_phase_enrich_cells(tseries_df, unit_ID_col, enrichment_ID_df, dataset_name, e_phase_name):
    enrich_in_phase_unit_IDs = get_dataset_units_enrich_in_phase(enrichment_ID_df, unit_ID_col, dataset_name, e_phase_name) #get unit IDs that are enriched in phase of interest
    enrich_in_phase_dataset_df = tseries_df.loc[tseries_df[unit_ID_col].isin(enrich_in_phase_unit_IDs)]#get unit time-series only if they enriched in phase of interest
    return enrich_in_phase_dataset_df, enrich_in_phase_unit_IDs

def get_dataset_units_enrich_in_phase(enrich_unit_by_name_phase_df, unit_ID_col, dataset, e_phase):
    name_mask = enrich_unit_by_name_phase_df.name == dataset
    phase_mask = enrich_unit_by_name_phase_df.task_phase_vec == e_phase
    enrich_in_phase_unit_IDs =enrich_unit_by_name_phase_df.loc[phase_mask&name_mask, unit_ID_col].values[0]
    return enrich_in_phase_unit_IDs

#### MAIN MATRIX STORE OF DATASET
def make_dataset_matrix_store_only(phase_names, single_trial_tseries_w_enrich,unit_ID_col,
                                   enrich_unit_ID_by_name_df, numeric_col, trial_list_by_dataset,
                                   dataset_name_by_geno_day,phase_enrichment_by_subj):
    """TO- create a dict where key1 = stage the pseudopop is enriched in, key 2 = stage to look for activity of, and key 3- genotype of current datset"""
    ppop_data,stage_geno_tseries = dict(), dict()
    iter_ct = 0
    for e_phase in phase_names: #loop through enrichment filter (get cells ENRICHED in phase N )
        ppop_data[e_phase],stage_geno_tseries[e_phase] = {},{} # geno_dataset_t_matrix[e_phase], t_count_used[e_phase], pseudopop_data[e_phase], phase_tseries_by_geno[e_phase] = dict(), dict(),dict(), dict() #fill keys of the phase field with names
        print("Get enrich in ",e_phase, "act. in ", phase_names)
        for act_phase in phase_names: #loop through phase ACTIVITY filter (get activity of cells in phase M)
            datasets_w_phase_act = trial_list_by_dataset.loc[trial_list_by_dataset.task_phase_vec == act_phase].name.unique() #only get datasets w. trials in phase of interest
            ppop_data[e_phase][act_phase],stage_geno_tseries[e_phase][act_phase]= {},{} # geno_dataset_t_matrix[e_phase], t_count_used[e_phase], pseudopop_data[e_phase], phase_tseries_by_geno[e_phase] = dict(), dict(),dict(), dict() #fill keys of the phase field with names # geno_dataset_t_matrix[e_phase][act_phase], phase_tseries_by_geno[e_phase][act_phase], pseudopop_data[e_phase][act_phase], t_count_used[e_phase][act_phase] = dict(), dict(), dict(),dict() #fill keys of the phase field with names
            for geno_day in dataset_name_by_geno_day.geno_day.unique():#after iter over all datasets, now, join all genos within a phase specific field of the joined geno matrix
                # geno_day_curr = trial_list_by_dataset.loc[trial_list_by_dataset.name == dataset, 'geno_day'].unique()[0]
                #option 2- use subfunc
                #option 1- chain function calls
                datasets_in_geno = get_dataset_names_in_geno(dataset_name_by_geno_day,geno_day)
                geno_dataset_w_act = [name for name in datasets_in_geno if name in datasets_w_phase_act] #get datasets w. trials in phase of interest & active
                current_ppop_draw = dict()
                for dataset in geno_dataset_w_act: #only get datasets w. trials in phase of interest
                    iter_ct = iter_ct+1

                    if phase_enrichment_by_subj.set_index('name').loc[dataset, e_phase] > 0:
                        phase_dataset_df = get_tseries_in_phase(get_tseries_of_dataset(single_trial_tseries_w_enrich,dataset), act_phase)#get rows of cell level time-series belonging to act_phase
                        e_in_phase_data_df,e_in_stage_ID =get_tseries_phase_enrich_cells(phase_dataset_df, unit_ID_col,
                                                                                         enrich_unit_ID_by_name_df, dataset, e_phase)
                        current_ppop_draw[dataset] =  horzcat_all_trials(e_in_phase_data_df,numeric_col,'unique_ID')  #horzcat the individual trial Tseries for each of the units foudn to be enriched preivously, joining on their index
                        # create pseudopopulation #resample as numpy matrix, then join to index to retain unique IDs            #vstack is possible because you retain the same number of trials
                    #else if the current dataset does NOT have any cells enriched in e_phase, continue to next dataset
    ## store the results in a dict, and access as needed for future runs
                ppop_data[e_phase][act_phase][geno_day] =current_ppop_draw
                # pseudopop_data[e_phase][act_phase][geno_day] = pd.concat([val for key,val in phase_tseries_by_geno[e_phase][act_phase].items() if key in geno_dataset_w_act])
    return ppop_data

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

def resample_concat_dict_of_activity_mats_w_subsample(dict_of_activity_dfs, num_resample,local_rng, subsample_range):
    """TO: given a dict of activity matrices where rows = units, cols = frames and scalar N, resample it N times into a list. 
    Each list elem = activity from a diff subj (to allow for varying len datasets)"""
    #pandas dataframe is INCLUSIVE of the end value, so you are including it in the subsample
    resampled_dict_list =[resample_unit_timeseries_df(d.loc[:,subsample_range], num_resample,local_rng) for d in dict_of_activity_dfs.values()]
    resampled_df = pd.concat(resampled_dict_list, axis = 0)
    return resampled_df

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


## summary plot function 
def plot_unit_enrich_by_phase_summary(fig_size, trial_type_by_subj,phase_enrichment_by_subj,geno_order, phase_names, numeric_col):
    unit_count_fig, axs = plt.subplots(2,2, figsize = fig_size, layout = 'constrained')
    axs = axs.flat
    # plot # recorded trials by phase
    sns.heatmap(ax = axs[0], data= trial_type_by_subj.set_index('name').drop('geno_day', axis = 1).T, annot = True)
    axs[0].set_title('# of recorded trials in each phase, by dataset');
    #plot timebin recorded of a phase, by dataset
    sns.heatmap(ax = axs[1], data= trial_type_by_subj.set_index('name').drop('geno_day', axis = 1).T*len(numeric_col),linewidth = 0.1, annot = True, fmt = '.0f')
    axs[1].set_title('# of recorded timebins in phase, by dataset');
    # plot # cells enriched in phase, by phase
    sns.heatmap(ax = axs[2], data=phase_enrichment_by_subj.set_index('name').drop('geno_day', axis = 1).T, linewidth = 0.1, annot = True, fmt = '.0f')
    axs[2].set_title('# of cells enriched in phase, by dataset');
    #total enrichment by geno_day
    sns.heatmap(ax = axs[3], data=phase_enrichment_by_subj.groupby('geno_day').sum().loc[geno_order,phase_names].T,linewidth = 0.1, annot = True, fmt = '.0f')
    axs[3].set_title('Total # units in pseudopop enriched in phase, by geno_day');
    #figre metadata
    unit_count_fig.subplots_adjust(top = 0.9);
    unit_count_fig.suptitle(f"Summary of Total # of trials and # of usable timebins for each dataset, by task phase");
    return unit_count_fig, axs


