#TO- store functions that will be useful for all plotting/processing
import numpy as np
import pandas as pd 
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn as sk
from textwrap import wrap
from scipy import stats
from datetime import datetime
from scipy.spatial.distance import pdist, cdist
import os
import itertools
# from statannotations.Annotator import Annotator
## import other custom modules
import ax_modifier_functions as axmod
import dataframe_annotation_functions as dfanno
# from phase_enrichment_timeseries.phase_enrich_timeseries_decode import get_unique_ID_for_dataset_units
import sns_plotting_config as sns_cfg 
#hyperparameters for decoding
num_resample = 400
n_pseudopop_runs = 300 #number of times you 1) create pseudopop and 2) decode with it
run_permutation_test = False
perm_test_type = 'auto' # 'auto' #optiosn are ['manual', 'auto']
n_perms = 300 #7min/100 perm #29-33 minutes/500 perm
reg_penalty = 'l2'
k_folds = 5 #first iter is 5 fold cv

##HELPER FUNCTION STORAGE
def get_datetag():
    curr_time = datetime.now()
    date_tag = "_".join([curr_time.strftime('%d'),curr_time.strftime('%h'),curr_time.strftime('%Y')])
    return date_tag

def save_plot_record_as_csv_txt(posthoc_df:pd.DataFrame,
                                folder_pref:str, #tag for later recorveyr fo folder information 
                                fig_name:str, 
                                csv_folder_most_recent=None, 
                                csv_folder_current_run=None,
                                csv_suffix:str="_posthoc table_",
                                txt_suffix:str="results_text"):
    '''To save CSV + TXT records from the posthoc testing done for current figure. saves in 1) 'csv folder most recent' which is constantly added to, and 2) csv folder current run, updated each day
    # params: csv_suffix and txt_suffix are appended to their respective filetypes
    return: none 
    '''
    ## get/import params and add to posthoc_df
    date_tag = get_datetag()
    posthoc_df['date_tag'] = date_tag
    posthoc_df['fig_name'] = fig_name
    posthoc_df['fig_num'] = folder_pref
    #save posthoc CSV
    if csv_suffix is not None:
        csv_name = "_".join([folder_pref, fig_name , csv_suffix , f"{date_tag}.csv"])
        save_csv_to_analysis_storage(posthoc_df.assign(fig_name=fig_name), csv_name, csv_folder_most_recent, csv_folder_current_run)
    else: 
        print("No csv suffix provided, not saving csv")
    if txt_suffix is not None:
        text_name = "_".join([folder_pref, fig_name , txt_suffix ,f"{date_tag}.txt"])
        #save as txt
        if csv_folder_current_run is not None:
            write_posthoc_to_txt_clean(posthoc_df, csv_folder_current_run / text_name)
        if csv_folder_most_recent is not None:
            write_posthoc_to_txt_clean(posthoc_df, csv_folder_most_recent / text_name)
    else:
        print("No text suffix provided, not saving text")
    

# temp storage for annotation tag 
    # date_tag = "_".join([datetime.now().strftime('%d'),datetime.now().strftime('%h'),datetime.now().strftime('%Y')])
    # # add date-tag annot
    # fig_obj.get_axes()[-1].annotate(f"made-{date_tag}", (0.98,-0.1), (10, -20), fontsize = 5, xycoords='axes fraction', textcoords='offset points',annotation_clip = False, ha= 'right', va='top')

DEFAULT_DATE_FORMAT = "%d_%h_%Y"

def save_csv_to_analysis_storage(csv_to_save: pd.DataFrame, csv_name: str, csv_folder_latest = None, csv_folder_current_run= None) -> None:
    """
    Save a CSV file to both the latest analysis folder and the current run's analysis folder.
    """
    valid_folders = [f for f in [csv_folder_latest, csv_folder_current_run] if f is not None]
    for folder in valid_folders:
        os.makedirs(folder, exist_ok=True)
        csv_to_save.to_csv(os.path.join(folder, csv_name))
        print(f"Saved {csv_name} to {folder}")


def write_posthoc_to_txt_clean(posthoc_table: pd.DataFrame, output_file: str) -> None:
    """
    Write a posthoc table to a text file, with one comparison per line. New version better aligned with readibility
    """
    with open(output_file, "w") as file:
        for _, row in posthoc_table.iterrows():
            template = [
                f"Comparing {row.numeric_var} of groups in {row.category_compared_within} level: " 
                        f"{row.group_1} {row.group_1_mean:.3f} +/- {row.group_1_sem:.3f}, {row.group_2} {row.group_2_mean:.3f} +/- {row.group_2_sem:.3f}. "
            f"{row.group_1} vs {row.group_2} {row.test_name} test statistic {row.stat_result[0]:.1f}, p = {row.pvalue:.5f}. {row.group_1} n={row.group_1_n[0]}, {row.group_2} n={row.group_2_n[0]}. full pvalue: {row.pvalue:.3E}\n"]

            file.write(template[0])
    print(f"Output saved to {output_file}")


def write_posthoc_table_to_txt(posthoc_table: pd.DataFrame, output_file: str) -> None:
    """
    Write a posthoc table to a text file, with one comparison per line.
    """
    with open(output_file, "w") as file:
        for _, row in posthoc_table.iterrows():
            fig_num = row['fig_num']
            comparison      = row["category_compared_within"]
            numeric_var = row["numeric_var"]
            axis_var        = row["x_category_var"]
            g1, g2          = row["group_1"], row["group_2"]
            # group_n may be a length‐1 sequence; guard against both cases
            n1 = row["group_1_n"][0] if hasattr(row["group_1_n"], "__getitem__") else row["group_1_n"]
            n2 = row["group_2_n"][0] if hasattr(row["group_2_n"], "__getitem__") else row["group_2_n"]
            pval            = row["pvalue"]
            test            = row.get("test_name", "")
            stat            = row.get("stat_result", "")
            mean1, sem1     = row["group_1_mean"], row["group_1_sem"]
            mean2, sem2     = row["group_2_mean"], row["group_2_sem"]
            
            file.write(
                f"[Fig num: {fig_num}. "
                f"Posthoc group dimension: {comparison}. "
                f"X axis categorical variable: {axis_var}. "
                f"Y variable: {numeric_var}] "
                f"{g1} {mean1:.3f}+/-{sem1:.3f} vs {g2} {mean2:.3f}+/-{sem2:.3f}. "
                f"{test} Test Stat={stat[0]:.1f}, p={pval:.5f} (Mean +/- SEM). ({g1} n={n1}, {g2} n={n2}) Full pvalue: {pval}\n"
            )
    print(f"Output saved to {output_file}")

################## figure location storage set location for storing folders for Figures
from pathlib import Path
# Save figures under the repository's results/ directory (two levels up from this file)
# helper_functions.py is in code/Function .py Storage/, so parents[2] is the repo root
main_fig_save_loc = Path(__file__).resolve().parents[2] / 'results'

fig_nums = [n+1 for n in range(9)]
fig_save_dir = {n: main_fig_save_loc / f"fig_{n}" for n in fig_nums}
supp_fig_save_dir = {f's_{n}': main_fig_save_loc / f"supp_fig_{n}" for n in fig_nums}

def save_fig_in_main_fig_dir(fig_obj, fig_name, folder_key, filetypes_to_save,**kwargs):
    """ Given a list of strings, dict of folder names, and template to fill, save N figures with N filetypes
    subfolder_dict- dict where key = filetype, value = folder name to save within current folder
    filetypes to save- list of strings whre elemtns = file exntensions (e.g. pdf, svg, png )"""
    #set up default args for saving
    default_args = { 'dpi': 300,'pad_inches':0.025} #'bbox_inches': 'tight',
    save_args = {**default_args, **kwargs}
    ##add datetime tag
    date_tag = "_" + "_".join([
        datetime.now().strftime('%d'),
        datetime.now().strftime('%h'),
        datetime.now().strftime('%Y')])
    # use a clean folder name (no trailing separators); keep leading underscore only for filenames
    date_dir = "_".join([
        datetime.now().strftime('%d'),
        datetime.now().strftime('%h'),
        datetime.now().strftime('%Y')])
    #if key contains s, save in supp folder
    if type(folder_key) == str:
        save_loc = supp_fig_save_dir[folder_key]
    else:
        save_loc = fig_save_dir[folder_key] #dict- key = figure number, value = folder loc
#save actual files
    make_folder(save_loc)
    make_folder(save_loc / date_dir)
    for fig_type in filetypes_to_save:
        fig_obj.savefig((save_loc / date_dir / f"{fig_name}{date_tag}.{fig_type}"), **save_args)


def min_max_normalize(vector: np.ndarray, keep_min: bool = True) -> np.ndarray:
    """
    Min-max normalize a vector, optionally keeping the minimum values unchanged.
    """
    vec_min, vec_max = np.min(vector), np.max(vector)
    if vec_max == vec_min:
        return vector  # Avoid division by zero for constant vectors

    normalized = (vector - vec_min) / (vec_max - vec_min)
    if keep_min:
        normalized[vector == vec_min] = vec_min
    return normalized


def check_if_row_has_nan(input_array):
    return np.any(np.isnan(input_array),axis = 1)

def get_match_index_in_iterable(iterable, val):
    ''' returns index of val in iterable if present'''
    return [idx for idx, x in enumerate(iterable) if x == val]

def make_folder(folder_name):
    if not os.path.exists(folder_name): # Check if the folder exists # If not, create the folder
        os.makedirs(folder_name)
        print(f"The folder '{folder_name}' has been created.")
    else:
        print(f"The folder '{folder_name}' already exists.")

# def get_start_ends_of_sliced_range(length, chunk_size):
#     """ 
#     Divides a range of indices into N chunks, ensuring all chunks except the last are the same size.
#     Args:
#         length (int): The total length of the range.
#         chunk_size (int): The size of chunks.
#        Returns: np.ndarray: An array of (start, stop) tuples representing the chunk ranges.
#     """
#     # Compute the size of each chunk
#     n_chunks = length // chunk_size
#     # Create an array of start indices
#     starts = np.arange(0, length, chunk_size)
#     # Compute inclusive stop indices so each chunk has exactly chunk_size rows
#     stops = starts + chunk_size - 1
#     stops[-1] = length - 1
#     return np.column_stack((starts, stops))

def add_spaces_linebreak_to_stage_ticks(stage_ax_ticks): 
    ''' TO- given a list of ax ticks that consist of task stages with understores, replace the underscores with spaces, then insert a line break char at position 9 (where early IA/RS ends)'''
    labels_w_spaces = [x.get_text().replace("_", " ") for x in stage_ax_ticks]
    labels_wrapped = [x[:8] + "\n" + x[8:] if x not in ["Late IA", "Late RS"] else x for x in labels_w_spaces ]
    return labels_wrapped 

def make_chunked_iterator_of_ranges(start,end, n_batches):
    batch_size = end//n_batches #divide len of vector into N batches
    start_val_range = np.arange(start, end + batch_size, batch_size)
    end_val_range = np.arange(start + batch_size, end + batch_size, batch_size)
    start_end_val_list = [np.arange(x,y) for (x,y) in zip(start_val_range, end_val_range)]
    #avoid last batch being extralong
    start_end_val_list[-1] = np.arange(start_end_val_list[-1][0], end)
    print(f"N_batches: {n_batches}")
    print(f"Batch_size: {batch_size}")
    return start_end_val_list


def get_unique_ID_for_dataset_units(tseries_df, unit_ID_col):
    unique_neuron_ID_per_dataset = tseries_df.groupby(by = ['name'])['neuron_ID'].value_counts().to_frame().drop('neuron_ID', axis = 1).reset_index()
    unique_neuron_ID_per_dataset['unique_ID'] = unique_neuron_ID_per_dataset.name.str.cat(unique_neuron_ID_per_dataset.neuron_ID.astype(str), sep = "-")
    return unique_neuron_ID_per_dataset

## subfunctions for classification
## decoding creation func
def make_class_label_vector(class_matrix, class_val):
    class_labels = np.repeat(class_val, class_matrix.shape[1])
    return class_labels

def get_class_AVs(class_0_matrix, class_1_matrix, class_0, class_1):
    class_0_AV = class_0_matrix.mean(axis = 1).to_frame()
    class_1_AV= class_1_matrix.mean(axis = 1).to_frame()
    merged_AVs =pd.concat([class_0_AV.rename({0: 'class_0'}, axis = 1), class_1_AV.rename({0: 'class_1'}, axis = 1)], axis = 1, join = 'inner').fillna(0).rename({'class_0': class_0,'class_1' : class_1}, axis = 1)
    return merged_AVs

def get_cosine_sim(vector_1, vector_2):
    v1_norm = np.linalg.norm(vector_1) 
    v2_norm =  np.linalg.norm(vector_2)
    if np.logical_or((v1_norm == 0), (v2_norm==0)):
        cos_sim = np.nan
    else:
        cos_sim = np.dot(vector_1, vector_2)/ (v1_norm*v2_norm)
    return cos_sim

def get_cosine_sim_of_class_AVs(class_0_matrix, class_1_matrix, class_0, class_1):
    #to- take the mean of each class used for decoding, and find cosine sim. between the classes
    #because you dn't use the raw activiyt vectors in the output, can just shortcut and take the avs directly
    # old method (convert to AV/df then take valuyes)
    AVs= get_class_AVs(class_0_matrix, class_1_matrix, class_0, class_1)
    AV_1, AV_2 = AVs[class_0].values,AVs[class_1].values #get value numpy array vector
    # new method- convert directly
    # AV_1= class_0_matrix.mean(axis = 1).values
    # AV_2 = class_1_matrix.mean(axis = 1).values #get value numpy array vector
    class_cosine_sim = get_cosine_sim(AV_1, AV_2) #np.dot(AV_1,AV_2)/ (np.linalg.norm(AV_1) * np.linalg.norm(AV_2))    
    return class_cosine_sim

#get pdist function (used in decoding data )
def get_mean_pdist(input_array):
    ''' get the mean of input pdist'''
    return pdist(input_array).mean()
##AV matrix related funcs

def get_df_unit_mean_activity_matrix(unit_mean_tseries, phase_dims, numeric_col, ignore_pre):
    all_geno_matrix,  all_geno_IDs= get_unit_mean_phase_activity_matrix( unit_mean_tseries, False, phase_dims, numeric_col, ignore_pre)
    print(f" Shape of concat. matrix is {all_geno_matrix.shape}, Shape of ID matrix is {all_geno_IDs.shape}")
    mean_AV_matrix = pd.DataFrame(data =np.nanmean(all_geno_matrix, axis = 1), columns = phase_dims, index = all_geno_IDs).merge(unit_mean_tseries.groupby('unique_ID')['geno_day'].first().to_frame(),left_index = True, right_on = 'unique_ID')
    if np.mean(mean_AV_matrix.loc[:, phase_dims].sum(axis = 1) == 0)>0:
        print(f" Removing {np.mean(mean_AV_matrix.loc[:, phase_dims].sum(axis = 1) == 0)} % of AVs with all 0s ")
        mean_AV_matrix = mean_AV_matrix[(mean_AV_matrix.loc[:, phase_dims].sum(axis = 1) > 0)]
        mean_AV_matrix['max_phase'] =mean_AV_matrix[phase_dims].idxmax(axis = 'columns')
        mean_AV_matrix['max_phase_val'] =mean_AV_matrix.apply(lambda x: x[x.max_phase], axis = 1)

    return mean_AV_matrix

def get_units_active_both_phases(activity_thresh, activity_df, phase_1, phase_2):
    high_active_df = activity_df[~((activity_df[phase_1] < activity_thresh)& (activity_df[phase_2] < activity_thresh))]# low_phase_1 =     # low_phase_2 = 
    return high_active_df

##filetype saving figure functions 
### NEW_ make custom subfolders with figure type (e.g. svg, pdf) in there
def make_figtype_subfolders(folder_name):
    """Create subfolders for each figure type under the given base folder.
    Accepts str or Path for folder_name. Returns a dict mapping filetype to Path.
    """
    base = Path(folder_name)
    subfolder_paths = {
        'svg': base / 'svg_plots',
        'pdf': base / 'pdf_plots',
        'png': base / 'png_plots',
    }
    for subfolder in subfolder_paths.values():
        make_folder(subfolder)
    return subfolder_paths

def save_fig_as_filetype_list(fig_obj, fig_name_template, subfolder_dict, filetypes_to_save):
    """ Given a list of strings, dict of folder names, and template to fill, save N figures with N filetypes
    subfolder_dict- dict where key = filetype, value = folder name to save within current folder
    filetypes to save- list of strings whre elemtns = file exntensions (e.g. pdf, svg, png )"""
    date_tag = "_".join([datetime.now().strftime('%d'),datetime.now().strftime('%h'),datetime.now().strftime('%Y')])

    for fig_type in filetypes_to_save:
        folder = Path(subfolder_dict[fig_type])
        outfile = folder / f"{fig_name_template}.{fig_type}"
        fig_obj.savefig(outfile)

def replace_df_index_underscore(input_df):
    return input_df.rename(index = {p:p.replace("_", " ") for p in input_df.index})

def full_annotate_2_phase_table(df_2_phases): 
    # TO- given a table containing two phase columns, return all types of phase breakdowns (e.g. IA/RS, error/correct, pre/post)
    #add section names function 
    df_2_phases = dfanno.add_section_names_and_pair(df_2_phases)
     #add rule cols
    phase_rule_col_names = ["phase1_rule","phase2_rule"]
    df_2_phases = dfanno.add_rule_col_per_phase_pair(df_2_phases, ['Phase1', 'Phase2'], phase_rule_col_names)
    #error/correct by phase
    df_2_phases['Phase1_correct_error'] = dfanno.add_error_correct_col(df_2_phases['Phase1'])
    df_2_phases['Phase2_correct_error'] = dfanno.add_error_correct_col(df_2_phases['Phase2'])
    #error pair insertion
    df_2_phases['correct_compared'] =df_2_phases.apply(lambda row: "-".join(set(sorted([row['Phase1_correct_error'], row['Phase2_correct_error']]))), axis = 1)
    single_section_str = ~df_2_phases['correct_compared'].str.contains("-")
    df_2_phases.loc[single_section_str, 'correct_compared'] = df_2_phases.loc[single_section_str, 'correct_compared'].str.cat(
        df_2_phases.loc[single_section_str, 'correct_compared'], '-')
    
    ## rule pair insertion
    df_2_phases = dfanno.add_rule_pair_col(df_2_phases, phase_rule_col_names)
    #correct for baseline string annotation flips
    df_2_phases.loc[df_2_phases['Rule_pair'].str.contains('aseline'),'Rule_pair'] = 'baseline'
    ## add section comparisons
    df_2_phases['cross_phase_compared'] = df_2_phases.sections_compared.str.contains("-")
    df_2_phases['ITI-trial'] = df_2_phases['cross_phase_compared'] & df_2_phases.sections_compared.str.contains("ITI")
    df_2_phases['trial-trial'] = df_2_phases['cross_phase_compared'] & (~df_2_phases.sections_compared.str.contains("ITI")
                                                                         & ~df_2_phases.sections_compared.str.contains("aseline"))
    df_2_phases['contains_IA'] = df_2_phases['Rule_pair'].str.contains("IA")
    return df_2_phases

def get_scipy_chi2_output(chi2_output_obj):
    #TO- given a chi2 output of the test, return a dict with the appropriate features #https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2_contingency.html#
    return {'statistic': [chi2_output_obj[0]], 'pval':[chi2_output_obj[1]], 'dof': [chi2_output_obj[2]], 'expected': [chi2_output_obj[3]]}
#for wrapping strings 
from textwrap import wrap
def get_wrapped_str(input_str, **kwargs):
    return '\n'.join(wrap(input_str, **kwargs))
    
## helper function for setting kwargs for a PCA scatterplot
def get_PCA_scatter_kwarg_dict(palette = None, input_alpha = None, distinct_face_alpha = None):
    #set PCA KWARG and return dict
    if palette == None:
        palette = ['mediumblue', 'red']
    if input_alpha == None:
        input_alpha = 0.4
    if distinct_face_alpha == None:
        distinct_face_alpha = False
    #package all of it into dicts
    if distinct_face_alpha:
        PCA_kwargs = {'palette': [matplotlib.colors.to_rgba(c,alpha =input_alpha) for c in palette],'linewidth' : 0.1,'edgecolor': 'black'}
    else:
        PCA_kwargs = {'palette': palette, 'alpha': input_alpha, 'edgecolors':None}
    return PCA_kwargs

##helper function for making PCA from dataset
def get_PCA_obj_and_transform_matrix(input_matrix, n_comp= None):
    """ input_matrix (M rows, N columns): M samples, N features. """
    if n_comp == None:
        n_comp = 3
    PCA_obj= sk.decomposition.PCA(n_components=n_comp, svd_solver = 'covariance_eigh', whiten = True)
    PCA_matrix = PCA_obj.fit_transform(input_matrix) #changed 12/8 to not using dataframe
    return PCA_obj, PCA_matrix

def get_geno_comparisons_stratefied_by_phase(phase, unique_genos, combos_to_skip):
    phase_pair_dict_phase = [combo for combo in itertools.product([phase],unique_genos )]
    phase_geno_comparison_pairs = [list(combo) for combo in itertools.combinations(phase_pair_dict_phase,2) if sorted([combo[1][1], combo[0][1]]) not in combos_to_skip ]
    return phase_geno_comparison_pairs

#############
## PLOT FUNCTIONS
##get boolean for what period each title is in

def get_bool_category_vecs(stage_list):
    is_late = [ 'late' in stage.lower() for stage in stage_list]
    is_RS = [ 'rs' in stage.lower() for stage in stage_list]
    is_error = [ 'error' in stage.lower() for stage in stage_list]
    bool_category_vec = {'late': is_late, 'RS': is_RS, 'error': is_error}
    return bool_category_vec

def get_early_rule_str_list(is_dict):
    early_and_rule = [" ".join([e,r]) for e,r in zip(['Early' if not(s) else 'Late' for s in is_dict['late']], ['IA' if not(s) else 'RS' for s in is_dict['RS']])]
    return early_and_rule
def get_correct_error_str_list(is_dict):
    correct_and_error = ['Correct' if not(s) else 'Error' for s in is_dict['error']]
    return correct_and_error

# given known location of x ticks, and known content, find mean position of each content
def get_unique_stage_mean_xtick_loc(tick_loc, stage_list):
    uniq_stage_mean_loc = list()
    for unique_stage in set(stage_list):
        stage_match = [e == unique_stage for e in stage_list]
        uniq_stage_mean_loc.append(np.mean(tick_loc[stage_match]))
    return uniq_stage_mean_loc
    
def get_ax_linedata_and_y_offset(g):
    line_y = np.concatenate([line.get_ydata() for line in g.get_lines()])
    max_height_y =line_y[line_y<1].max()
    #define ylims and offsets
    ylims = g.get_ylim()
    height_offset_text = ylims[1]*0.995# height_offset_text = max_height_y + max_height_y*0.25
    height_offset_line = ylims[1]*0.96# height_offset_line = height_offset- jitter_offset
    jitter_offset = 0.00775
    return height_offset_text, height_offset_line, jitter_offset

def plot_heatmap_w_kwargs(data, ax, kwarg_dict, label_dict):
    sns.heatmap(data =data, ax = ax, **kwarg_dict)
    axmod.set_ax_title_xlabel_ylabel(ax, label_dict)
    return ax

def replace_df_index_underscore(input_df):
    return input_df.rename(index = {p:p.replace("_", " ") for p in input_df.index})

## DATA STRUCTURE SPECIFIC FUNCS
def flatten_2_row_mosaic(mosaic_2d):
    return [e for e in mosaic_2d[0]]+ [e for e in mosaic_2d[1]]

def add_dict_field_to_dicts(dict_list, new_field_name):
    #TO- given iterable  of dict objects, update each one with 'new_field_name', containign a fresh dict
    for elem in dict_list:
        elem.update({new_field_name: dict()})

def remove_unwanted_entries(elem_list, elem_to_keep, placeholder_str):
    new_list = [e if e in elem_to_keep else placeholder_str for e in elem_list]
    return new_list
## time-bin extraction functions
def get_bin_end_str(timebin_list, bin_flag = None):
    if bin_flag == None:
        bin_flag = " to "
    bin_end = [e.split(bin_flag)[1].split("s")[0] for e in timebin_list] #.str.removesuffix("s").astype(float)
    return bin_end

def get_numeric_col_bin_end_float(timebin_list):
    bin_ends_str = get_bin_end_str(timebin_list)
    bin_ends_float = [float(e) for e in bin_ends_str]
    return bin_ends_float

def rename_df_numeric_col_w_bin_end_float(input_df, numeric_col):
    bin_ends_float = get_numeric_col_bin_end_float(numeric_col)
    #zip together numeric_col and new ends
    rename_dict = {old:new for old, new in zip(numeric_col, bin_ends_float)}
    input_df = input_df.rename(rename_dict, axis = 1)
    return input_df

#### Preprocessing functions

## function to annotate csv from the experiment name 
def annotate_csv(df, field_name):
    verbose_geno_day_names = {'HET1': 'Het VEH', 'HET2': 'Het CLNZ', 'HET3': 'Het postCLNZ', 'WT1': 'WT VEH', 'WT2': 'WT CLNZ'}
    #field name is the name of the column containing the name information 
    treat_conditions = [(df[field_name].str.contains("RS1")), (df[field_name].str.contains("RS2")), (df[field_name].str.contains("RS3"))]
    treat_values = [1,2,3]
    df['day'] = np.select(treat_conditions, treat_values)
    df['geno'] = np.select(
        [df[field_name].str.contains('WT'),df[field_name].str.contains('HET')],
         ['WT', 'HET'],
         default = 'unknown')
    # aggregate day and geno
    raw_geno_day = df['geno'] + df['day'].astype(str)
    df['geno_day'] = raw_geno_day.replace(verbose_geno_day_names)
    #correct df to nan from zero, as groupby ignores nan

#function to save files in previously created figure storage folder within the google drive
def save_file_to_drive(fig_name, file_format,storage_file_path):
    """storage path is predefined. figure name and file format are string inputs """
    plt.savefig(os.path.join(storage_file_path,fig_name), format = file_format,dpi=300, bbox_inches='tight')

def get_unit_max_event_rate_of_all_trials(timeseries_df, group_by_list, numeric_col, name_unitID_list, max_val_col_name):
    #TO- get the max event rate recorded for a neuron, across all trials. standard inputs:
        # group_by_list: list  ['name', 'neuron_ID', 'task_phase_vec', 'trial_num'] # numeric_col: usual list of cols with tseries data in them
        # name_unitID_list: list with dataset name + unit name, eg. ['name', 'neuron_ID'] # max_val_col_name: name of column to store the max trial value in, e.g.  "max_trial_val"
    max_event_rate_df= timeseries_df.groupby(by = group_by_list)[numeric_col].max().max(axis = 1).reset_index().rename({0: max_val_col_name}, axis = 1)# canonical line:  timeseries_df.groupby(by = ['name', 'neuron_ID', 'task_phase_vec', 'trial_num'])[numeric_col].max().max(axis = 1).reset_index().rename({0: "max_trial_val"}, axis = 1)
    max_event_rate_df = max_event_rate_df.groupby(by = name_unitID_list)[max_val_col_name].max().reset_index() #OG line: max_event_rate_df.groupby(by = ['name', 'neuron_ID'])['max_trial_val'].max().reset_index()
    return max_event_rate_df

def add_unique_ID_col_to_trial_series_df(trial_tseries_df, numeric_col, dataset_name_col, id_col):
    trial_tseries_df = trial_tseries_df.merge(get_unique_ID_for_dataset_units(trial_tseries_df, id_col), 
                                              on = [dataset_name_col, id_col], how = 'left')
    trial_tseries_df.loc[:,numeric_col] = trial_tseries_df.loc[:, numeric_col].astype(float)
    return trial_tseries_df

def run_min_max_norm_on_timeseries(run_norm, timeseries_df, name_unitID_list, numeric_col,max_val_col_name):
    #get max event rate by unit
    if run_norm:
        groupby_list = name_unitID_list + ['task_phase_vec', 'trial_num']
        max_e_rate = get_unit_max_event_rate_of_all_trials(timeseries_df, groupby_list, numeric_col, name_unitID_list, max_val_col_name)
        if max_val_col_name not in timeseries_df.columns:    #merge timeseries with max event rate by unit record
            nonzero_max_vals = max_e_rate.loc[(max_e_rate[max_val_col_name] > 0),:]
            normed_ts_df = timeseries_df.merge(nonzero_max_vals, how = 'left', on = name_unitID_list) 
        else:
            normed_ts_df = timeseries_df
        # print(f"columns of merge are {normed_ts_df.columns}")
        section_mask = (~normed_ts_df[max_val_col_name].isnull()) & (normed_ts_df[max_val_col_name] > 0) #delete rows if their max val == or nan
        normed_ts_df = normed_ts_df.loc[section_mask,:]
        #normalize by max event rate
        normed_ts_df.loc[:, numeric_col] = normed_ts_df.loc[:, numeric_col].values/normed_ts_df.loc[:, max_val_col_name].values[:,np.newaxis] #find way to avoid NaN values
        #drop rows with no max trial val
    else: #else don't norm
        normed_ts_df = timeseries_df 
    return normed_ts_df

#### Enrichment Specifc
def get_rows_enriched_and_of_phase(ts_long,phase_vec_col, phase_enrich_col, phase_name):
    return ts_long.loc[(ts_long[phase_enrich_col] == 1) &(ts_long[phase_vec_col] == phase_name),:]    #  mean_ts_long.loc[(mean_ts_long[row_phase] == 1) &(mean_ts_long['task_phase_vec'] == row_phase),:]

def get_phase_enrichment_CSV(data_type_to_get, input_file):
#TO- fetch CSV for activation what you're doing and return unit name
    if data_type == 'activity': #based on activity or correlations, make units and import
        units = 'single cell'
        has_metadata = True
        input_file
        cell_period_active = pd.read_excel(input_file) #pd.read_excel('complexTACO- neurons_activity by task phase_18-Jan-2024.xls')
        cell_period_active[cell_period_active == -99] = np.nan    #for tables created after 02dec 2023, -99 is nan value
    elif data_type == 'cluster activity':
        has_metadata = True
        units = 'cell-pair clusters'
        cell_period_active = pd.read_excel(input_file)# pd.read_excel('complexTACO- cluster_activity by task phase_26-Jan-2024.xls')
        cell_period_active[cell_period_active == -99] = np.nan    #for tables created after 02dec 2023, -99 is nan value
    else:
        has_metadata = False
        cell_period_active = pd.read_excel(input_file) #pd.read_excel('complexTACO_cell_pair_coactivity_by task phase_26-Jan-2024.xlsx')
        units = 'cell pairs'
        cell_period_active[cell_period_active == -99] = np.nan    #for tables created after 02dec 2023, -99 is nan value
    cell_period_active =cell_period_active.rename(columns = {col: col.replace("outcome_", "") for col in cell_period_active.columns})
    if has_metadata:
        metadata = cell_period_active.iloc[0,-3:].to_frame().T#.rename(columns = ['run_end_time', 'num_shuffles', 'percentile_of_shuff'])
        print(metadata)
        cell_period_active.drop(labels = cell_period_active.columns[-3:], axis = 1, inplace = True)
        # id_col = cell_period_active.pop('neuron_ID') # cell_period_active.insert(13, 'neuron_ID', id_col)
    cell_period_active[cell_period_active.columns[:19]] = cell_period_active[cell_period_active.columns[:19]].astype(float)
    annotate_csv(cell_period_active, 'name')
    return cell_period_active, units

### getting trial IDs
def get_phase_enriched_units(df_with_enrichment, phase_to_get):
    # df_with_enrichment = df with columns == the name of the phases, signalling enrichment
    # phase_to_get= string that's one of the N phases of interest, for filtering
    enriched_rows = df_with_enrichment[phase_to_get] > 0    #do I just get rows?
    return df_with_enrichment[enriched_rows]

def get_ID_enriched_units_by_phase(df_with_enrichment, ID_col, bool_col_tseries_enriched):
    #bool_col_tsewries_enriched is a boolean col of df_with_enrichment that says if cell N in trial X from phase P is enriched in phase P
    df_only_enrich_in_curr_phase_tseries = df_with_enrichment[df_with_enrichment[bool_col_tseries_enriched]] #index into tseries df with bool col
    enrich_unit_ID_by_name_df = df_only_enrich_in_curr_phase_tseries.groupby(['name', 'geno_day','task_phase_vec'])[ID_col].unique().reset_index()
    enrich_unit_ID_by_name_df['num_enriched_units'] = enrich_unit_ID_by_name_df[ID_col].apply(lambda x: len(x))
    return enrich_unit_ID_by_name_df

def get_trial_num_in_phase_by_dataset(tseries_df):
    trial_list_by_dataset = tseries_df.groupby(['name', 'geno_day','task_phase_vec'])['trial_num'].unique().reset_index()
    trial_list_by_dataset['count_of_trials'] =trial_list_by_dataset.trial_num.apply(lambda x: len(x))
    return trial_list_by_dataset

def get_list_trial_num_in_class(df_class_trials_by_name, class_name, dataset_name):
    #returns vector of trials of interest
    class_rows = df_class_trials_by_name.task_phase_vec ==class_name
    dataset_rows = df_class_trials_by_name.name == dataset_name
    class_trials = df_class_trials_by_name.loc[dataset_rows& class_rows, 'trial_num'].values[0].tolist()
    return class_trials

def get_trial_IDs_and_total_num(dict_of_trials):
    trial_IDs = np.unique(dict_of_trials)
    num_trials= len(trial_IDs)
    return trial_IDs, num_trials

def get_num_trials_by_type_in_subject(timeseries_df, task_phase_col):
    trial_type_by_subj = timeseries_df.groupby(['name', 'geno_day', 'trial_num'])[task_phase_col].first().reset_index()
    trial_type_by_subj = trial_type_by_subj.groupby(['name', 'geno_day'])[task_phase_col].value_counts().to_frame().rename({task_phase_col: "count"}, axis = 1).reset_index()
    trial_type_by_subj = trial_type_by_subj.pivot_table(index = ['name', 'geno_day'], values = 'count', columns = "task_phase_vec").reset_index()
    return trial_type_by_subj

def get_num_enriched_units_by_phase_by_subj(cell_period_active, unit_ID_col):
    phase_enrichment_by_subj = cell_period_active.drop([unit_ID_col, 'day'], axis = 1).groupby(by = ['name', 'geno_day']).sum().reset_index()
    return phase_enrichment_by_subj

def add_bin_end_col(input_df, timebin_string_col):
    input_df['bin_end'] = input_df[timebin_string_col].str.split(" to ",expand = True)[1].str.removesuffix("s").astype(float)
    return input_df

def get_bin_end_str(timebin_list):
    bin_end = [e.split(" to ")[1].split("s")[0] for e in timebin_list] #.str.removesuffix("s").astype(float)
    return bin_end

def get_numeric_col_bin_end_float(timebin_list):
    bin_ends_str = get_bin_end_str(timebin_list)
    bin_ends_float = [float(e) for e in bin_ends_str]
    return bin_ends_float

## PLOT SPECIFIC 
def get_best_fit_line(x_data, y_data):
    x_data_as_matrix = np.vstack([x_data, np.ones(len(x_data))]).T
    print(x_data_as_matrix.shape)
    m, b = np.linalg.lstsq(x_data_as_matrix, y_data)[0] #create least suqares lin alg. fit (take the least squares solution output which is elem 0)
    x_vals = np.linspace(np.min(x_data),np.max(x_data),100)
    y_vals = (m*x_vals) + b
    line_data = (x_vals, y_vals)
    return line_data

def num2str_sigfig(value,num_sig_fig):
    #TO- given a numeric input, and a specified # of sig figs, truncate value
    str_output = f"{float(f'{value:.{num_sig_fig}g}'):g}"
    return str_output

##TIMESERIES BINNING FUNCTIONS (IMPORTED)

## MAIN BINNING FUNCTION

def bin_post_outcome(bin_post, outcome_post, win_n):
    if bin_post: #bin- take frame cols, pivot, then drop index, and groupby every N rows of the index (formerly columns), then take mean, and pivot back
        fr_col, non_frame_col =get_frame_nonframe_cols_of_tseries(outcome_post, 'f')
        pos_frames,neg_frames = get_pos_neg_frame_cols(fr_col, '-') #pos_frames =fr_col[~fr_col.str.contains('-')].tolist() # neg_frames =fr_col[fr_col.str.contains('-')].tolist()
        pre_bin_names, post_bin_names = find_n_bins_pre_post_get_new_bin_mapper(neg_frames, pos_frames, win_n)
        frame_long = outcome_post[neg_frames + pos_frames].T.reset_index().drop('index', axis = 1) #take the frame cols only from post-decision, pivot then reset index # bin_to_frame = frame_long.groupby(frame_long.index//win_n)['index'].agg(['unique', 'nunique']).rename({'unique': 'bin_frames'}, axis = 1).rename(pre_bin_names | post_bin_names)#get what indices are contained in the current binning scheme for reference
        binned_frames = frame_long.groupby(frame_long.index//win_n).mean().T.rename(pre_bin_names | post_bin_names, axis = 1)
        outcome_post= outcome_post[non_frame_col].merge( drop_partial_bin(binned_frames, ( len(neg_frames) + len(pos_frames)), win_n), left_index = True, right_index = True) ## rejoin outcome post with newly binned dataset + drop last bin if window smaller than should be
    return outcome_post

## functions called
def get_frame_nonframe_cols_of_tseries(tseries_df, frame_flag):
    #TO- given a timeseries df (e.g. post-outcome, find all cols with string_flag in them, and create 2 lists of frame/non frame cols)
    fr_col = get_frame_cols( tseries_df, frame_flag)    #fr_col = outcome_post.columns[outcome_post.columns.str.contains('f')]
    non_fr_col = [col for col in tseries_df.columns if col not in fr_col]
    return fr_col, non_fr_col

def find_n_bins_pre_post_get_new_bin_mapper(neg_frames, pos_frames, win_n):
    #TO- given known # of frames of negative (= pre-decision frames) and positive(post decision frames), get # bins for each givne window size, and return dict mapping these bins to original frame names
    num_pre_bins, num_post_bins= get_n_bin_of_pre_post(neg_frames, pos_frames, win_n) #get num frames from pre/post #get size bins after windowing
    pre_bin_names, post_bin_names = get_pre_post_bin_name_mappers(num_pre_bins, num_post_bins, win_n)#map new bin range to actual second value
    return pre_bin_names, post_bin_names 
## subfunctions called to compose above functions 

## functions for getting # frames in pre/post outcome
def get_frame_cols(input_df, frame_flag):
    return input_df.columns[input_df.columns.str.contains(frame_flag)]

def get_pos_neg_frame_cols(frame_cols, frame_flag):
    #TO_ output pos/post-outcome frames, then neg/pre-outcome frames (based on boolean (if, if not having flag_frame in col name))
    pos_frames =frame_cols[~frame_cols.str.contains(frame_flag)]
    neg_frames =frame_cols[frame_cols.str.contains(frame_flag)]
    print(f'binning data- post. # post-outcome frames: {len(pos_frames)} #pre-outcome frames: {len(neg_frames)}')
    return  pos_frames.tolist(), neg_frames.tolist()

def get_col_w_str(input_df, string_to_find): #generic search function
    return input_df.columns[input_df.columns.str.contains(string_to_find)]

## functions for getting bin names based on # frames
def get_n_bin_of_pre_post(neg_frames, pos_frames, win_n):
    #TO- given a window size (in # of frames), get the number of pre-outcome frames included in the dataset (== neg frames), and post-outcome frames (==pos frames)
    #get num frames from pre/post #get size bins after windowing# frac_s =  #fraction of a second the new bin is
    num_pre_bins = int( len(neg_frames)//win_n)
    num_post_bins = int(len(pos_frames)//win_n)
    return num_pre_bins, num_post_bins

def get_pre_post_bin_name_mappers(num_pre_bins, num_post_bins, win_n):
    ##to- given a range of bin values (assuming each is range of +1 int), step up + #map new bin range to actual second value
    pre_bin_names =  get_neg_bin_name_mapper(num_pre_bins, frac_s= win_n/20) 
    post_bin_names = get_pos_bin_name_mapper( np.arange(num_pre_bins, num_pre_bins + num_post_bins), frac_s= win_n/20)
    return pre_bin_names, post_bin_names

def get_pos_bin_name_mapper(pos_bin_range, frac_s):
    ##to- given a range of bin values (assuming each is range of +1 int), step up # frac_s =  #fraction of a second the new bin is
    pos_bin_names = {bin: str(frac_s*(e)) + 's to ' +  str(frac_s*(e+1)) + 's' for e,bin in enumerate(pos_bin_range)}
    return pos_bin_names

def get_neg_bin_name_mapper(num_pre_bins, frac_s):
    ##to- given a range of bin values (assuming each is range of +1 int), step up # frac_s =  #fraction of a second the new bin is
    pre_bin_names = {bin:'-'+str(frac_s*(e+1)) + 's to -' + str(frac_s*(e)) + 's' for e,bin in enumerate(np.flip( np.arange(0, num_pre_bins)))}
    return pre_bin_names

## bin general funcs
def drop_partial_bin(input_df, n_input_frames, win_n):
    ##to- given a window size (in # of frames), find if last bin is uneven sized (i.e. < win_n frames included in last bin), and if so, drop
    rem_frames = ( n_input_frames % win_n)
    print(f"rem_frames: {rem_frames}")
    if rem_frames > 0:
        print(f"Merge penultimate/last bin with only {rem_frames} frame in it, then dropping last bin")
        input_df.iloc[:,-2] = input_df.iloc[:,-2:].mean(axis = 1)
        input_df = input_df.iloc[:,:-1]
    return input_df