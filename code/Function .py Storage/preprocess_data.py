# preprocess_data.py
#################### HYPERPARAMETER DEFINITIONS
## set hyperparameter dict for analysis run 
import os
import numpy as np
import pandas as pd

hyper_param_dict = {}
#set fields of hypoerparameters
hyper_param_dict['drop_low_responders'] = False
hyper_param_dict['drop_cells_active_in_1_trial'] = False #%meta param
hyper_param_dict['window_to_bin'] = 5 #n frames to average over
hyper_param_dict['bin_size'] = hyper_param_dict['window_to_bin']/20 #in seconds, resulting binsize
hyper_param_dict['n_sec_to_rotate'] = 0
hyper_param_dict['n_pre_bin_to_drop'] = 2*4 #how many bins (seconds * window size0  of the pre-decision to drop
hyper_param_dict['n_post_end_bin_to_drop'] = 0*4 #how many bins (seconds * window size0  of END the post-decision to drop)
## begin data loading# ## preprocess language
hyper_param_dict['normalize_data'] = True
hyper_param_dict['drop_subj_w_1_stage_trial'] = False
hyper_param_dict['data_type'] = "event_rate"

#################### LOCATION NAMES
#current files- 9/3/24 replaced old 
analysis_data_to_use_folder = '11-Dec-2024_event_fixed_stage_labels'
datasets_location = f"/content/drive/MyDrive/Colab Notebooks/Sohal Lab Datasets/time-series including WT CLNZ dataset/{analysis_data_to_use_folder} Dataset Source/"
# datasets_location = "/content/drive/MyDrive/Colab Notebooks/Sohal Lab Datasets/Time-series activity datasets/"
timeseries_loc = datasets_location
#specify filenames 
analysis_data_to_use = '11-Dec-2024'
enriched_by_stage_path = f'main_datasets_complexTACO- neurons_activity by task phase_{analysis_data_to_use}.xls' #300 shuff, april 24 run
analysis_config_path = []
# enriched_by_stage_path = 'complexTACO- neurons_activity by task phase_15-Apr-2024.xls' #300 shuff, april 24 run
# post_activity_timeseries = datasets_location + 'post_outcome_neurons_trial sig activity_timeseries.csv'
post_activity_timeseries = datasets_location + f'post_outcome_main_datasets_neurons_trial activity timeseries data_{analysis_data_to_use}_timeseries.csv'

trial_tseries_save_name = f'single_trial_post_neuron_timeseries_w_enrichment_{analysis_data_to_use}_.csv'
hyper_param_dict['trial_tseries_save_name'] = trial_tseries_save_name
stage_col = 'task_phase_vec'


############# FUNCTION STORAGE
##MAIN FUNCTION

#TO- store functions that are common for all current preprocessing functions
import custom_module_imports as cmi
def get_all_baseline_timeseries_dfs(datasets_location, file_tag = None, bin_timeseries = None):
    if file_tag == None:
        file_tag = 'baseline'
    if bin_timeseries == None:
        bin_timeseries = True

    files = [f for f in os.listdir(datasets_location)]
    baseline_files = [f for f in files if file_tag in f]
    baseline_dfs_list= [] #store each csv dataset o baseline activity
    for f in baseline_files:
        subj_baseline_df = pd.read_csv(datasets_location + f)
        baseline_dfs_list.append(subj_baseline_df)
    ## join the baseline dfs
    baseline_df = pd.concat(baseline_dfs_list)
    baseline_df = cmi.hf.bin_post_outcome(bin_timeseries, baseline_df, 5)
    #various post-processing
    cmi.hf.annotate_csv(baseline_df, 'name')

    return baseline_df

def get_normed_trial_tseries( stage_enriched_csv_path,act_tseries_path, hyper_param_dict):
    #import hyper parameters for analysis 
    window_to_bin= hyper_param_dict['window_to_bin']
    n_sec_to_rotate= hyper_param_dict['n_sec_to_rotate']
    save_name= hyper_param_dict['trial_tseries_save_name']
    norm_data= hyper_param_dict['normalize_data']
    drop_low_responders = hyper_param_dict['drop_low_responders']

    if drop_low_responders == None:
        drop_low_responders = True #if user fails to input bool saying whether to drop_low_responders, default to doing it
    if norm_data == None:
        norm_data = True #if user fails to input bool saying whether to perform min/max normalization on data, default to doing it
    #TO- combine enrichment csv + actiivty timeseries, bin and rotate, then normalize
    ## run main body of analysis 
    cols_to_drop = ['threshold_with_shuffle','peak_dff_threshold_percentile','drop_low_value_peak_events','cutoff_filter','peak_event_cutoff_percentile']
    cell_period_active = read_cell_enrichment_by_stage(stage_enriched_csv_path)
    outcome_post = pd.read_csv(act_tseries_path, header =0,low_memory=False)
    outcome_post =outcome_post.drop([x for x in cols_to_drop if x in outcome_post], axis = 1).dropna(subset = ['task_phase_vec'])
    cmi.hf.annotate_csv(outcome_post, 'name')
    ## begin preprocess- bin and rotate timeseries 
    outcome_post = bin_rotate_timeseries(outcome_post, window_size = window_to_bin, rotate_by = n_sec_to_rotate)
    #get stage info
    numeric_col = get_numeric_cols_timeseries(outcome_post, " to ")
    ## get post enrichment generic func
    trial_tseries_df_raw = remove_low_activity_WT_datasets(preprocess_post_df(outcome_post, get_post_enrichment(cell_period_active)), numeric_col, drop_low_responders) ## logic- drop lowest 2 active datasets
    normed_trial_tseries_df = cmi.hf.run_min_max_norm_on_timeseries(norm_data, trial_tseries_df_raw, ['name', 'unique_ID'], numeric_col, 'max_trial_val') #min_max_norm = True
    normed_trial_tseries_df.to_csv(save_name)
    #get mean of each trial
    normed_trial_tseries_df['mean_rate'] =normed_trial_tseries_df[[c for c in numeric_col if '-' not in c]].mean(axis = 1) #mean rate is post outcome only
    normed_trial_tseries_df['active_in_trial'] =normed_trial_tseries_df['mean_rate']>0
    #OPTIONAL- drop N bins from start and M bins from end of time-series
    normed_trial_tseries_df = drop_end_bins_of_trials(normed_trial_tseries_df,numeric_col,  n_end_timebins_to_drop = hyper_param_dict['n_post_end_bin_to_drop'] )
    normed_trial_tseries_df = drop_start_bins_of_trials(normed_trial_tseries_df,numeric_col,  n_start_timebins_to_drop =hyper_param_dict['n_pre_bin_to_drop'])

    return normed_trial_tseries_df.replace([np.inf, -np.inf], np.nan)

## ain preprocessing
def preprocess_post_df(input_df, enrich_df,stage_enrich_cols = None,  stage_col= None):
    #TO- given an input df csv, an enrichment df, process and clean 
   #set defualt keyargs 
   if stage_col== None:
       stage_col= 'task_phase_vec'
   if stage_enrich_cols == None:
       stage_enrich_cols = sorted(input_df[stage_col].unique())
   key_list = ['name', 'geno', 'geno_day', 'neuron_ID']
   #verify key is uniue
   input_df= drop_duplicate_neuron_ID_col(input_df,'neuron_ID')
   ##merge dataset and add key columns 
   input_df = merge_enrich_df_timeseries_df(input_df.drop('section', axis = 1),
                                            enrich_df.drop('section', axis = 1), key_list)
   clean_post_df=add_enriched_in_curr_phase_col(input_df, stage_col)
   ## add more key cols 
   neuron_ID_col_name = 'neuron_ID'
   clean_post_df['any_enrichment']= clean_post_df[stage_enrich_cols].sum(axis = 1)
#    clean_post_df = add_neuron_ID_col(clean_post_df, name_col= neuron_ID_col_name)
   clean_post_df= add_unique_col(clean_post_df, 'name', neuron_ID_col_name, sep = None)
   return clean_post_df.replace([np.inf, -np.inf], np.nan)

def bin_rotate_timeseries(input_df, window_size = None, rotate_by = None):
    """#TO- combine binning of frame-wise df function + rotating by N seconds function (to set zero period identically across sections). Moves columns right-ward by N seconds. """
    #set defaults
    if window_size == None:
        window_size = 5
    if rotate_by == None:
        rotate_by = 3
    ## begin preprocess- bin and rotate timeseries 
    input_df = cmi.hf.bin_post_outcome(bin_post = True, outcome_post = input_df, win_n = window_size)# num frames to bin on
    num_cols = get_numeric_cols_timeseries(input_df, " to ").to_list()
    ## rotate bins 
    bin_size = window_size/20
    offset = int(rotate_by/bin_size)
    print(f" Moving numeric coluns by {offset} bins")
    if offset > 0:
        input_df = rotate_df_numeric_cols(input_df,  num_cols, offset)

    return input_df
######################################################
## SUBFUNCTIONS ## function tsorage 

def get_df_unit_mean_activity_matrix(unit_mean_tseries, phase_dims, numeric_col, ignore_pre):
    all_geno_matrix,  all_geno_IDs= get_unit_mean_phase_activity_matrix( unit_mean_tseries, False, phase_dims, numeric_col, ignore_pre)
    print(f" Shape of concat. matrix is {all_geno_matrix.shape}, Shape of ID matrix is {all_geno_IDs.shape}")
    mean_AV_matrix = pd.DataFrame(data =np.nanmean(all_geno_matrix, axis = 1), columns = phase_dims, index = all_geno_IDs).merge(unit_mean_tseries.groupby('unique_ID')['geno_day'].first().to_frame(),left_index = True, right_on = 'unique_ID')
    if np.nanmean(mean_AV_matrix.loc[:, phase_dims].sum(axis = 1) == 0)>0:
        print(f" Removing {np.nanmean(mean_AV_matrix.loc[:, phase_dims].sum(axis = 1) == 0)} % of AVs with all 0s ")
        mean_AV_matrix = mean_AV_matrix[(mean_AV_matrix.loc[:, phase_dims].sum(axis = 1) > 0)]
    return mean_AV_matrix

#### preprocessing and normalization steps 
def get_unit_mean_phase_activity_matrix(unit_mean_tseries, use_enrich_unit_only, phase_dims, numeric_col, ignore_pre):
    '''#TO- create matrix that's = concatenated vectors of all neuron mean activationni phase (output matrix = # units x # phases)
    OUTPUT- '''
    matrix_IDs, stack_matrix,nan_df_list = dict(), dict(),[]
    skip_rec = dict()
    ## if going to skip pre-outcome period, change what counts as numeric col
    if ignore_pre:
        numeric_col = [col for col in numeric_col if '-' not in col]
    for dataset in unit_mean_tseries.name.unique():
        matrix_list = []
        dataset_df = unit_mean_tseries[ (unit_mean_tseries.name == dataset)]
        if len(dataset_df.task_phase_vec.unique()) < len(phase_dims):#check that dataset has ALL 6 phases, if not, skip
            skip_rec[dataset] = len(dataset_df.task_phase_vec.unique())
            # continue
        for phase in phase_dims:
            phase_mask = (dataset_df.task_phase_vec == phase)
            matrix = dataset_df.loc[phase_mask, numeric_col].values #get phase entries, producing (dataset_neuron) x (time_bin matrix)
            #check if phase is present, if matrix extracted w phase trials is empty, assume mous elacks it 
            if matrix.shape[0] == 0:
                print('0 mask')
                matrix = np.tile(np.nan, (len(dataset_df.unique_ID.unique()), len(numeric_col)))
            # print(dataset, phase,matrix.shape)
            if np.sum(np.isnan(matrix))>0:
                print(f" # nan values in {dataset} slice in {phase} = {np.sum(np.isnan(matrix))}")
                nan_df_list.append( dataset_df.loc[phase_mask, numeric_col])
            matrix_list.append(matrix)
        stack_matrix[dataset] = np.dstack(matrix_list)
        matrix_IDs[dataset] = dataset_df.loc[phase_mask, 'unique_ID'].values
    all_geno_matrix = np.concatenate([val for val in stack_matrix.values()], axis = 0)
    all_geno_IDs =  np.concatenate([val for val in matrix_IDs .values()], axis = 0) 

    return all_geno_matrix, all_geno_IDs


## TRIMMING FUNCTIONS 
def drop_end_bins_of_trials(trial_tseries,numeric_col,  n_end_timebins_to_drop = None):
    ''' TO- drop N timebins from the end of trial-level timeseries  '''
    #default args: 
    if n_end_timebins_to_drop == None:
        n_end_timebins_to_drop = 0
    post_cols_to_drop = {True: numeric_col[-n_end_timebins_to_drop:], False: []}[n_end_timebins_to_drop > 0] # post_cols_to_drop = numeric_col[-hyper_param_dict['n_post_end_bin_to_drop']:]
    print(f"Dropping {n_end_timebins_to_drop} bins from end: {post_cols_to_drop}")
    return trial_tseries.drop(post_cols_to_drop, axis = 1)

def drop_start_bins_of_trials(trial_tseries,numeric_col,  n_start_timebins_to_drop = None):
    ''' TO- drop N timebins from the start of trial-level timeseries  '''
    #default args: 
    if n_start_timebins_to_drop == None:
        n_start_timebins_to_drop = 0
    pre_cols_to_drop = {True:numeric_col[0:n_start_timebins_to_drop], False: []}[ n_start_timebins_to_drop > 0]
    print(f"Dropping {n_start_timebins_to_drop} bins from start: {pre_cols_to_drop}")
    return trial_tseries.drop(pre_cols_to_drop, axis = 1)


def get_subject_stage_info_df(trial_tseries):
    #TO- create output DF with information about the # of enrihced units by stage, number of trials per stage, etc
    # get subj level dfs 
    trial_list_by_dataset = cmi.hf.get_trial_num_in_phase_by_dataset(trial_tseries)
    e_unique_ID_subj = cmi.hf.get_ID_enriched_units_by_phase(trial_tseries, 'unique_ID', 'enriched_in_phase')
    n_units_by_subject =  trial_tseries.groupby(by = ['geno_day', 'name'])['unique_ID'].nunique().reset_index().rename({'unique_ID': 'num_units'}, axis = 1)
    #merge all subj level dfs
    subject_stage_info_df = e_unique_ID_subj.merge(n_units_by_subject, on = ['geno_day', 'name'], how = 'left').merge(
        trial_list_by_dataset, on = ['geno_day', 'name', 'task_phase_vec'], how = 'left')
    subject_stage_info_df['over_5'] = subject_stage_info_df.apply(lambda x: [y > 5 for y in x['trial_num']], axis = 1)
    return subject_stage_info_df


def get_unit_mean_timeseries_by_phase(time_series_df,cols_to_avg_over = None, groupby_list = None, numeric_col_wide = None):
    ##default args 
    if cols_to_avg_over== None:
        cols_to_avg_over = ['trial_num']
    if groupby_list== None: 
        groupby_list = ['name', 'neuron_ID','geno_day', 'task_phase_vec']
    ##main logic
    id_cols = time_series_df.columns[~time_series_df.columns.isin(numeric_col_wide)]
    temp_id_cols = [col for col in id_cols.tolist() if col not in groupby_list] #tewmp ID cols are for just maintaining information about activation
    groupby_func_agg = {**{col: 'mean' for col in numeric_col_wide}, **{id_col: 'first' for id_col in temp_id_cols if id_col not in cols_to_avg_over}}
    cell_avg_stage_tseries =time_series_df.groupby(by =groupby_list).agg(groupby_func_agg).reset_index()

    cell_avg_stage_tseries['max_val']= cell_avg_stage_tseries.loc[:,[c for c in cell_avg_stage_tseries.columns if "to" in c]].max(axis = 1)
    cell_avg_stage_tseries['max_val_tbin']= cell_avg_stage_tseries.loc[:,[c for c in cell_avg_stage_tseries.columns if "to" in c]].idxmax(axis = 1)
    cell_avg_stage_tseries['mean_rate'] = cell_avg_stage_tseries[[c for c in numeric_col_wide if '-' not in c]].mean(axis = 1) #mean rate is post outcome only
    return cell_avg_stage_tseries

## rotating names based on input

def rotate_df_numeric_cols(input_df, num_col, offset):
    #rotate array of columns and reset 
    shift_numeric_col = np.roll(num_col, -offset)
    input_df=input_df.rename(columns = {o:n for o,n in zip(num_col,shift_numeric_col )}).drop(shift_numeric_col[-offset:], axis = 'columns')   
    return input_df

# drop_low_activity_WT_data funcs
def remove_low_activity_WT_datasets(trial_tseries_df_raw, numeric_col, drop_datasets):
    wt_mean_act = get_WT_mean_activity_df(trial_tseries_df_raw, numeric_col,) # wt_mean_act = trial_tseries_df_raw[trial_tseries_df_raw.geno_day == "WT VEH"].groupby('name')[numeric_col].mean().mean(axis = 1).reset_index().rename({0: 'mean activity'}, axis = 1)
    print(wt_mean_act)
    drop_type = 'bottom_2' # if input is string, drops lowest 2. if input is numeric, drops values < threhsold
    if drop_datasets:
        low_responders = get_low_activity_WT_names(wt_mean_act, cutoff = drop_type) # low_responders = wt_mean_post_activity['name'].iloc[-2:]
        print(f" dropping low responders {low_responders}, below threshold {drop_type}")
        trial_tseries_df_raw = trial_tseries_df_raw[~trial_tseries_df_raw.name.isin(low_responders)]
    return trial_tseries_df_raw     

def get_WT_mean_activity_df(trial_df, numeric_col, geno_name = None, mean_act_col_name = None):
    #set defaults 
    if geno_name == None:
        geno_name = 'WT VEH'
    if mean_act_col_name == None:
        mean_act_col_name = 'mean activity'
        #main logic
    wt_mean_act =trial_df.loc[trial_df.geno_day == geno_name,:].groupby('name')[numeric_col].mean().mean(axis = 1).reset_index().rename(
        {0: mean_act_col_name}, axis = 1)
    return wt_mean_act

def get_low_activity_WT_names(activity_df,activity_col = None, cutoff = None, num_to_drop = None):
    ## set defaults  # if input is string, drops lowest 2. if input is numeric, drops values < threhsold
    if activity_col == None:
        activity_col = 'mean activity'
    if cutoff is None:
        cutoff = 0.01 #activity cutoff
        ## run main logic 
    sorted_df = activity_df.sort_values(by = activity_col, ascending = False)
    if type(cutoff) == int:
        low_activity_mask = sorted_df.loc[:,activity_col] < cutoff
    else: 
        print(f"Dropping lowest 2 act datasets")
        low_activity_mask = sorted_df.index[-2:]
    low_activity_names =  sorted_df.loc[low_activity_mask, 'name'].unique()
    if num_to_drop is not None:
        low_activity_names = sorted_df['name'].iloc[-num_to_drop:]
    return low_activity_names

def drop_duplicate_neuron_ID_col(input_df, neuron_ID_substring):
    neuron_ID_cols =[f for f in input_df.columns if neuron_ID_substring in f]
    if len(neuron_ID_cols) >1:
        #drop last neuron ID col
        input_df = input_df.drop(neuron_ID_cols[1:], axis = 1)
        input_df.rename({neuron_ID_cols[0]: 'neuron_ID'}, axis = 1, inplace = True)
        print(f"dropped duplicate neuron ID col")
    return input_df

def read_cell_enrichment_by_stage(cell_enrichment_by_stage_path):
    #TO- import the cell enrichment, then annotate litely 
    cell_period_active = pd.read_excel(cell_enrichment_by_stage_path)
    cell_period_active[cell_period_active == -99] = np.nan    #for tables created after 02dec 2023, -99 is nan value
    cell_period_active[cell_period_active.columns[:19]] = cell_period_active[cell_period_active.columns[:19]].astype(float)
    cell_period_active =cell_period_active.rename(columns = {col: col.replace("outcome_", "") for col in cell_period_active.columns})
    metadata = cell_period_active.iloc[0,-3:].to_frame().T#.rename(columns = ['run_end_time', 'num_shuffles', 'percentile_of_shuff'])
    print(metadata)
    cell_period_active.drop(labels = cell_period_active.columns[-3:], axis = 1, inplace = True)
    cmi.hf.annotate_csv(cell_period_active, 'name')
    #check how many neuron ID cols there are
    #if > 1 col has neuron ID in there, drop
    cell_period_active= drop_duplicate_neuron_ID_col(cell_period_active,'neuron_ID')
    return cell_period_active

def get_post_enrichment(cell_period_active):
    section_names = ['pre', 'post', 'ITI']
    id_cols_section = ['name', 'geno_day', 'geno', 'neuron_ID']
    section_enrichment, _ = get_section_enrichment_df(cell_period_active, section_names, id_cols_section)
    post_sec_enrichment = section_enrichment.loc[section_enrichment.section == 'post',:]
    return post_sec_enrichment
    
def get_numeric_cols_timeseries(input_df, numeric_sep):
    local_numeric_col = input_df.columns[input_df.columns.str.contains(numeric_sep)]
    return local_numeric_col

def add_neuron_ID_col(input_df, name_col):
    for name_curr in input_df[name_col].unique():
        subset = input_df[name_col] == name_curr
        input_df.loc[subset, 'neuron_ID'] = subset.cumsum()
    return input_df
#get post-decision information

def add_enriched_in_curr_phase_col(enrichment_merged_act_df, phase_name_col):
    for counter, phase in enumerate(enrichment_merged_act_df[phase_name_col].unique()):
        mask = (enrichment_merged_act_df[phase_name_col]== phase)
        enrichment_merged_act_df.loc[mask, 'enriched_in_phase'] = enrichment_merged_act_df[phase] == 1
    return enrichment_merged_act_df 

def get_section_enrichment_df(input_df, section_names = None, id_cols = None):
    if section_names == None:
        section_names = ['pre', 'post', 'ITI']
    if id_cols== None:    
        id_cols = ['name', 'geno_day', 'geno', 'neuron_ID']
    section_columns = {}
    section_list = []
    for counter, sec in enumerate(section_names):
        section_columns[sec] = input_df.columns[input_df.columns.str.contains(sec)].tolist()
        temp_df = input_df.loc[:, section_columns[sec] + id_cols]
        temp_df.loc[:, 'section'] = sec
        temp_df.columns = temp_df.columns.str.removeprefix(sec + "_")
        section_list.append(temp_df)
        all_section_enrichment = pd.concat(section_list).reset_index().drop('index', axis = 1)
    return all_section_enrichment, section_columns
## 
def merge_enrich_df_timeseries_df(input_df, enrich_df, key_list = None):
    if key_list == None: 
        key_list = ['name', 'geno', 'geno_day', 'neuron_ID']
    merged_df = input_df.merge(enrich_df,how = 'left', on = key_list)
    return merged_df

def add_unique_col(subj_level_df, subj_name_col, neuron_ID_col, sep = None):
    #TO- create new column in a subject level DF, consisteing of concatenated 'neuron ID" and recoridng name cols
    if sep == None:
        sep = '-'
    subj_level_df['unique_ID'] = subj_level_df[subj_name_col].str.cat(subj_level_df[neuron_ID_col].astype(str), sep = sep)
    return subj_level_df