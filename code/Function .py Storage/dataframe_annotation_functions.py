import numpy as np
import matplotlib
from matplotlib import pyplot as plt
import pandas as pd
import os
import helper_functions as hf

##functin to take a melted dataframe and 
def annotate_errors(input_df):
    ''' inplace error column adding, Must be performed on melted long form df''' 
    error_mask = input_df['variable'].str.contains('Error')
    input_df['Trial Type'] = 'Correct'
    input_df.loc[error_mask, 'Trial Type'] = 'Error'

#extracts the experiment name to just have a subject ID
def add_subject_col(input_df, col_name):
    input_df['subject']=input_df[col_name].str[0:5]

    ##AV specific functions
def add_phase_behavior_cols(input_df):
    input_df['Trial Phase'] =input_df['variable'].str[0:2]
    input_df['Trial Behavior'] = [entry.split(entry[0:2])[1] for entry in input_df['variable']] #first pass, splits the variable name off the 1st 2 characters, then takes the 2nd entry of the split list
    input_df['Trial Behavior'] = input_df.apply(lambda x: x['Trial Behavior'].split(x['Trial Type'])[0], axis = 1)
    input_df['behavior'] = input_df['Trial Phase'] + input_df['Trial Behavior']
    #extracts the experiment name to just have a subject ID
def add_subject_col(input_df, col_name):
    input_df['subject']=input_df[col_name].str[0:5]

def add_rules_compared_to_df(melted_ensemble_av, new_field_name):
    broad_trial_values = ["IA-IA", "IA-RS", "RS-RS", "IA-Baseline", "RS-Baseline"]
    IA_IA_comparisons = ['Early IA Error vs Early IA Correct', 'Early IA Error vs Late IA','Early IA Correct vs Late IA'] #3 in IA comparisons
    IA_RS_comparisons = ['Early IA Error vs Early RS Error',
                        'Early IA Error vs Early RS Correct',
                        'Early IA Error vs Late RS',
                        'Early IA Correct vs Early RS Error',
                        'Early IA Correct vs Early RS Correct',
                        'Early IA Correct vs Late RS',
                        'Late IA vs Early RS Error',
                        'Late IA vs Early RS Correct', 
                        'Late IA vs Late RS',] # 9 IA-RS comparions
    RS_RS_comparisons = ['Early RS Error vs Early RS Correct', 'Early RS Error vs Late RS','Early RS Correct vs Late RS'] #3 in RS comparions
    IA_baseline = ['Early IA Error vs baseline', 'Early IA Correct vs baseline','Late IA vs baseline' ]
    RS_baseline=['Early RS Error vs baseline','Early RS Correct vs baseline','Late RS vs baseline']
    broad_trial_conditions = [melted_ensemble_av.variable.isin(IA_IA_comparisons),
                            melted_ensemble_av.variable.isin(IA_RS_comparisons), 
                            melted_ensemble_av.variable.isin(RS_RS_comparisons),
                            melted_ensemble_av.variable.isin(IA_baseline),
                            melted_ensemble_av.variable.isin(RS_baseline)]
    melted_ensemble_av[new_field_name] = np.select(broad_trial_conditions, broad_trial_values)


def return_variables_sorted_by_lowest_in_WT(melted_av, variable_name):
    comparison_avg_by_geno = melted_av.groupby(by = [variable_name, "geno_day"])['value'].mean().to_frame().reset_index()
    comparisons_sorted_by_lowest_in_WT_df = comparison_avg_by_geno.loc[comparison_avg_by_geno.geno_day == "WT Veh",:].sort_values(by = "value")
    comparisons_sorted_by_lowest_in_WT_array = comparisons_sorted_by_lowest_in_WT_df[variable_name].values
    return comparisons_sorted_by_lowest_in_WT_array

def import_annotate_sim_dataset(csv_name, name_field):
    # name_field = "name" #default setting
    sim_dataset = pd.read_csv(csv_name)
    hf.annotate_csv(sim_dataset, name_field)
    add_subject_col(sim_dataset, name_field)
    return sim_dataset

def melt_sim_dataset(sim_dataset):
    melted_sim_dataset =sim_dataset.melt(id_vars = ['section', 'name', 'geno', 'day', 'geno_day', 'subject', 'early_criteria_value'])
    melted_sim_dataset['variable'] =melted_sim_dataset.variable.str.replace("_", " ")
    #melted_sim_dataset.dropna(axis = 0, inplace = True)
    return melted_sim_dataset