## for phase enrichment timeseries analysis
import seaborn as sns
import numpy as np
import pandas as pd
import scipy.stats as stats
import pingouin as pg
import itertools
from matplotlib import pyplot as plt
# from statannotations.Annotator import Annotator
from helper_functions import *
from dataframe_annotation_functions import *

## begin main 

###pseudo taco, get oertlaps 
def get_phases_enrich_str_from_bool_enrich_vecs(enrich_matrix, phase_vecs, na_str):
    #TO- given a matrix where each row contains multiple columns, return a list for each row's enriched pahses
    #phase_dims is str list of columns to extract from input df #na str is what str is returned if phase isn't enriched in
    row_phases_enriched_list = enrich_matrix.apply(lambda x: [bool(p)*phase_vecs[i] if bool(p) else na_str for i,p in enumerate(x[sorted(phase_vecs)])], axis = 1)
    return row_phases_enriched_list.apply(lambda x: " & ".join([elem for elem in x if elem is not na_str]))
def get_sort_unique_overlap_count(overlap_df):
    return overlap_df.stack().groupby(level = 0).unique().astype(float).sort_values(ascending = False) #vertstack each col pass throuhg overlap crosstab, then get uniq values for the overlap count + sort
def crosstab_enrichment_overlap(unit_mean_tseries, phase_dims):
    geno_overlap = []
    for geno in unit_mean_tseries.geno_day.unique(): ## loop throuh ggenos
        unit_enrichment =  unit_mean_tseries[unit_mean_tseries.geno_day == geno].groupby(by = 'unique_ID')[phase_dims].first()
        overlap_list = []
        for count, curr_phase_overlap in enumerate(phase_dims): #iterate over each phase
            all_crosstab = pd.crosstab([unit_enrichment[d] for d in phase_dims], unit_enrichment[curr_phase_overlap]) #crosstab 1.0 overlap of current col of interest, w all other cols
            ct_bool = all_crosstab.reset_index(drop = True).rename({1.0: curr_phase_overlap}, axis = 1)
            ct_bool.index = get_phases_enrich_str_from_bool_enrich_vecs(all_crosstab.reset_index(), phase_vecs = phase_dims, na_str = 'none')
            overlap_list.append(ct_bool.loc[ct_bool[curr_phase_overlap]>0, curr_phase_overlap]) #get nonzero overlaps, for current phase
        overlap_df = pd.concat(overlap_list, join = 'outer', axis = 1)
        overlap_df[geno] = get_sort_unique_overlap_count(overlap_df)
        geno_overlap.append(overlap_df[geno])
    geno_sig_overlap_df = pd.concat(geno_overlap, join = 'outer', axis = 1)
    return geno_sig_overlap_df

########## Plot enrichment grouped timeseries and distributions
def make_tseries_long(input_ts, numeric_col,timebin_col):
    tseries_long =  add_bin_end_col(input_ts.melt(id_vars =  input_ts.columns[~input_ts.columns.isin(numeric_col)], var_name = timebin_col, value_name = 'mean activity'), timebin_col) #melt long
    return tseries_long

def plot_mean_SEM_timeseries_in_phase(ax_input, df_input, **kwargs):
    g = sns.lineplot(data =  df_input,ax = ax_input, **kwargs)
    ax_input.axvline(x=0, color="black", dashes=(2, 1), zorder=0)#add 0 second line
    handles, labels = ax_input.get_legend_handles_labels()#get legend information then remove 
    ax_input.get_legend().remove()
    sns.despine(ax = ax_input)
    return g, handles, labels

def plot_enriched_vs_not_units_in_phase(ax_plot, activation_df, phase_to_plot, enrichment_col, phase_col_name, data_type, **plot_kwargs ):
    df_phase_slice =  activation_df.loc[(activation_df[phase_col_name] == phase_to_plot),:]
    g, handles, labels = plot_mean_SEM_timeseries_in_phase(ax_plot,df_phase_slice, **{'style': enrichment_col, 'y' : 'mean activity', 'x': 'bin_end',**plot_kwargs})
    set_ax_title_xlabel_ylabel(ax_plot, {'title':f"Enriched v. non-enriched units", 'xlabel':f"Time (s)", 'ylabel':f"Mean {data_type}"})
    sns.despine(ax = ax_plot)
    return g, handles, labels

def plot_max_events_by_geno_in_phase_bar(ax_to_plot, **kwargs):
    g = sns.barplot(ax = ax_to_plot, **kwargs)
    line_handles, line_labels = ax_to_plot.get_legend_handles_labels() #get legend information then remove
    ax_to_plot.get_legend().remove()
    sns.despine(ax_to_plot)
    return g, line_handles, line_labels

def plot_row_enrich_ts_w_label(e_tseries_long,phase_names, col_width,row_width,data_type, geno_color_dict, num_enrich_ROI_geno, units):
## adapted version of the plot_phase_enriched_vs_phase_activity()
    num_rows = len(phase_names)
    n_col_to_add = 2
    fig, axs = plt.subplots(num_rows,(num_rows + n_col_to_add),figsize = ((num_rows +n_col_to_add)*col_width, num_rows*row_width,), layout = 'constrained', width_ratios = [0.15] + np.tile(1,num_rows + n_col_to_add-1).tolist())
    for e_count, row_phase in enumerate(phase_names):
        #put text to label what row this is
        ax_row_label = axs[e_count,0]
        ax_row_label.text(x = 0.3, y = 0.75, s = f"Units sig. active (e-unit) in", wrap = True, fontsize = 10, horizontalalignment='center', verticalalignment='center',) #add sig. star if sig
        ax_row_label.text(x = 0.3, y = 0.5, s = f"{row_phase},", wrap = True, fontsize = 10, horizontalalignment='center', verticalalignment='center',) #add sig. star if sig
        ax_row_label.text(x = 0.3, y = 0.25, s = f"normalized event rate:", wrap = True, fontsize = 10, horizontalalignment='center', verticalalignment='center',) #add sig. star if sig
        ax_row_label.axis('off')
        #plot enrich vs not enriched
        ax_enrich_comp = axs[e_count,1]
        g = plot_enriched_vs_not_units_in_phase(ax_enrich_comp, e_tseries_long, row_phase, 'enriched_in_phase', "task_phase_vec", data_type, **geno_color_dict)[0]## PLOT ENRICHED vs NOT within phase rel plot

        ax_enrich_comp.set_ylim([0, None])
        for act_count, col_phase in enumerate(phase_names):    ## ITERATE THROUGH OTHER PHASES #plot (activity) of cells enriched in phase N, in all phases
            e_in_phase_df = e_tseries_long.loc[(e_tseries_long[row_phase] == 1) & (e_tseries_long.task_phase_vec == col_phase),:] #for the corresponding rows that contain activity for the task phase of itnerest
            axis = axs[e_count,act_count+n_col_to_add]
            g, handles, labels= plot_mean_SEM_timeseries_in_phase(axis, e_in_phase_df, **{'alpha': 0.8, 'y' : 'mean activity', 'x': 'bin_end',**geno_color_dict})
            set_ax_title_xlabel_ylabel(axis, {'title':f"E-unit in {col_phase}", 'yticks': [], 'ylabel': None, 'xlabel':f"Time (s)", 'xlim': [None, 15], 'ylim': ax_enrich_comp.get_ylim()})
            axis.set_yticks([]) # sns.despine(ax = axis)
            if e_count < len(phase_names)-1:
                axis.set_xticks([])
                ax_enrich_comp.set_xticks([])
            _,  _ = add_sig_star_from_timebin_ANOVA(e_in_phase_df, g, axis)# add sig star by timebin
    ## overall figure specifications
    fig.suptitle(f" Avg. phase-enriched {units} {data_type} time-series in all phase. (1-way ANOVA by timebin)")
    fig.legend(handles, [f"{label} (n = {n_val} {units} enriched)" for label, n_val in num_enrich_ROI_geno.items()], loc='upper left', bbox_to_anchor=(0.15, 1.025),ncol=4, title=None, frameon=False) #add N to each of these labels
    return fig

def plot_phase_enriched_vs_phase_activity(e_tseries_long,phase_names, col_width,row_width,data_type, geno_color_dict, num_enrich_ROI_geno, units):
    num_rows = len(phase_names)
    fig, axs = plt.subplots(num_rows,(num_rows + 1),figsize = ((num_rows + 1)*col_width, num_rows*row_width,), layout = 'constrained')# height_ratios =np.tile([0.2, 0.075],num_rows//2))
    for e_count, row_phase in enumerate(phase_names):
        g = plot_enriched_vs_not_units_in_phase(axs[e_count,0], e_tseries_long, row_phase, 'enriched_in_phase', "task_phase_vec", data_type, **geno_color_dict)[0]## PLOT ENRICHED vs NOT within phase rel plot
        axs[e_count,0].set_ylim([0, None])
        for act_count, col_phase in enumerate(phase_names):    ## ITERATE THROUGH OTHER PHASES #plot (activity) of cells enriched in phase N, in all phases
            e_in_phase_df = e_tseries_long.loc[(e_tseries_long[row_phase] == 1) & (e_tseries_long.task_phase_vec == col_phase),:] #for the corresponding rows that contain activity for the task phase of itnerest
            axis = axs[e_count,act_count+1]
            g, handles, labels= plot_mean_SEM_timeseries_in_phase(axis, e_in_phase_df, **{'alpha': 0.8, 'y' : 'mean activity', 'x': 'bin_end',**geno_color_dict})
            set_ax_title_xlabel_ylabel(axis, {'title':f"Phase-enrich in {col_phase}",'ylabel': None, 'xlabel':f"Time (s)", 'ylim': axs[e_count,0].get_ylim()})
            _,  _ = add_sig_star_from_timebin_ANOVA(e_in_phase_df, g, axis)# add sig star by timebin
    ## overall figure specifications
    fig.suptitle(f" Avg. phase-enriched {units} {data_type} time-series in all phase. (1-way ANOVA by timebin)")
    fig.legend(handles, [f"{label} (n = {n_val} {units} enriched)" for label, n_val in num_enrich_ROI_geno.items()], loc='upper left', bbox_to_anchor=(0.15, 1.025),ncol=4, title=None, frameon=False) #add N to each of these labels
    return fig

##### TABLE MANIPULATION FUNCTIONS 
def merge_timeseries_with_section_enrich(unit_timeseries_df, sec_enrichment_df, section_name):
    merged_df = add_enriched_in_curr_phase_col(unit_timeseries_df.merge(sec_enrichment_df.loc[sec_enrichment_df.section == section_name,:].drop('section', axis = 1), how = 'inner', on = ['name', 'neuron_ID', 'geno_day', 'geno']), 'task_phase_vec')
    merged_df['any_enrichment'] =merged_df.loc[:,list(merged_df.task_phase_vec.unique())].sum(axis = 1)
    return merged_df

def get_mean_phase_timeseries_with_enrichment(timeseries_df, section_enrichment, section_name):
    groupby_list = ['name', 'neuron_ID','geno_day', 'task_phase_vec']
    cols_to_avg_over = ['trial_num']
    numeric_col = get_numeric_cols_timeseries(timeseries_df, " to ")
    unit_mean_tseries = get_unit_mean_timeseries_by_phase(timeseries_df,cols_to_avg_over, groupby_list,numeric_col)
    phase_names = unit_mean_tseries.task_phase_vec.unique()
    avg_phase_tseries_of_unit = merge_timeseries_with_section_enrich(unit_mean_tseries.drop('section', axis = 1),section_enrichment,  section_name)#table is, mean neuron activation by each N task phases, per dataset
    numeric_col_post_decision =[col for col in [num_col for num_col in avg_phase_tseries_of_unit.columns if " to " in num_col] if "-" not in col ]
    print(numeric_col_post_decision) #get max of each row, within columns above
    avg_phase_tseries_of_unit['max_trial_dff'] = avg_phase_tseries_of_unit[numeric_col_post_decision].max(axis = 1, numeric_only = True)
    return avg_phase_tseries_of_unit, unit_mean_tseries, phase_names
## enrichment annotation functions
def get_num_early_IA_enrich_unit_by_subj_long(phase_enrichment_by_subj):
    long_enrichment = phase_enrichment_by_subj.melt(id_vars = ['name', 'geno_day'])
    long_early_IA_enrich_df =  long_enrichment[long_enrichment.variable.str.contains('Early_IA')]
    long_early_IA_enrich_df['section'] = long_early_IA_enrich_df.variable.str.split("_", n = 1).str.get(0)
    long_early_IA_enrich_df['error_correct']= long_early_IA_enrich_df.variable.str.split("_").str.get(-1).map({'Correct': "# correct enriched units", 'Error': '# error enriched units'})
    long_early_IA_enrich_df = long_early_IA_enrich_df.groupby(['name', 'geno_day', 'section', 'error_correct'])['value'].first().unstack('error_correct').reset_index()
    return long_early_IA_enrich_df


def get_unit_count_by_subject(sample_groups, units):
    unit_count_by_subject = sample_groups.groupby(by = ['geno_day', 'name'])['treatment'].count().reset_index().rename({'treatment': f"{units} count"}, axis = 1)
    return unit_count_by_subject
def get_subject_count(sample_groups):
    subject_count = sample_groups.groupby(by = "name")['geno_day'].first().value_counts().to_frame().reset_index().rename({'index': "Genotype-treatment", 'geno_day': "# Subjects:"}, axis = 1)
    return subject_count
def get_unit_count_by_subject_and_subject_count(sample_groups, units):
    unit_count_by_subject = get_unit_count_by_subject(sample_groups, units)
    subject_count = get_subject_count(sample_groups)
    return unit_count_by_subject, subject_count
def get_mean_activation_csv(excel_file):
    mean_activation_df = pd.read_excel('neurons_mean dataset activity_18-Jan-2024.xls')
    annotate_csv(mean_activation_df, 'name_col')
    return mean_activation_df



def get_section_enrichment_df(input_df, section_names, id_cols):
    section_columns = {}
    section_enrichment = {}
    for counter, sec in enumerate(section_names):
        section_columns[sec] = input_df.columns[input_df.columns.str.contains(sec)].tolist()
        section_enrichment[sec] = input_df[section_columns[sec] + id_cols]
        section_enrichment[sec]['section'] = sec
        section_enrichment[sec].columns = section_enrichment[sec].columns.str.removeprefix(sec + "_")
    section_enrichment = pd.concat(section_enrichment).reset_index().drop(['level_0', 'level_1'], axis = 1)
    return section_enrichment, section_columns

def get_mean_enrichment_by_phase(df_with_enrichment, ID_cols, phase_cols):
    return df_with_enrichment.groupby(by = ID_cols).agg({phase: "mean" for phase in phase_cols }).reset_index().melt(id_vars = ID_cols)

def reorganize_numeric_cols_if_has_neg(input_df, numeric_sep):
    local_numeric_col =  get_numeric_cols_timeseries(input_df, numeric_sep)
    local_neg_cols = local_numeric_col.str.startswith("-")
    local_pos_cols = ~local_neg_cols
    reorg_numeric = local_numeric_col[local_neg_cols].tolist() + local_numeric_col[local_pos_cols].tolist()
    local_numeric_col =reorg_numeric
    id_cols = input_df.columns[~input_df.columns.str.contains(numeric_sep)].tolist()
    reorg_df = input_df[local_numeric_col + id_cols]
    return reorg_df

####
### post-hoc comparison functions for timeseries
def run_welch_ANOVA_on_geno_by_timebin(timeseries_df, timebin_col, dependent_var_col, geno_col):
    timebin_list = timeseries_df[timebin_col].unique()
    timebin_anova_result_list = []

    for curr_timepoint in timebin_list:
        test_timepoint = timeseries_df[timeseries_df[timebin_col]== curr_timepoint]
        timebin_anova = pg.welch_anova(data = test_timepoint, dv = dependent_var_col, between = geno_col).drop('Source', axis = 1)
        timebin_anova['timebin'] = curr_timepoint
        timebin_anova_result_list.append(timebin_anova)

    time_series_geno_anova = pd.concat(timebin_anova_result_list)# timebin_anova
    time_series_geno_anova['sig'] = time_series_geno_anova['p-unc'] < 0.05
    time_series_geno_anova
    return time_series_geno_anova

def get_dict_of_geno_day_combo_by_timebin(sig_geno_anova_df,curr_timeseries, combos_to_skip):
    bin_geno_ts_combo_list = {}
    for curr_time_bin in sig_geno_anova_df.timebin.unique():
        curr_time_bin = [curr_time_bin]
        bin_geno_pair = [combo for combo in itertools.product(curr_time_bin, curr_timeseries.geno_day.unique())]
        impt_geno_comparisons = [combo for combo in itertools.combinations( bin_geno_pair,2) if sorted([combo[0][1], combo[0][1]]) not in combos_to_skip ]
        bin_geno_ts_combo_list[curr_time_bin[0]] = impt_geno_comparisons
    return bin_geno_ts_combo_list

def return_timebin_MC_df(sig_geno_anova_by_timebins, sig_timebin_df, timebin_comparison_dict):
    pg_output_list = []
    for curr_time_bin in sig_geno_anova_by_timebins.timebin.unique():
        mask_in_timebin = sig_timebin_df.bin_end == curr_time_bin
        for geno_comp in timebin_comparison_dict[curr_time_bin]:
            geno_1_mask = sig_timebin_df.geno_day == geno_comp[0][1]
            geno_2_mask = sig_timebin_df.geno_day == geno_comp[1][1]
            array_1 = sig_timebin_df.loc[mask_in_timebin & geno_1_mask,'mean activity'].values
            array_2 = sig_timebin_df.loc[mask_in_timebin & geno_2_mask,'mean activity'].values
            pg_output = pg.mwu(array_1, array_2)
            pg_output['compared'] = " v ".join([geno_comp[0][1],geno_comp[1][1]])
            pg_output['timebin'] = curr_time_bin
            pg_output['pval_adjust_bh'] = stats.false_discovery_control(pg_output['p-val'], method = 'bh')
            pg_output_list.append(pg_output.drop(['RBC','CLES'], axis = 1))
    if pg_output_list:
        mw_posthoc_on_sig_bins_df = pd.concat(pg_output_list)
    else:
        mw_posthoc_on_sig_bins_df = pd.DataFrame(columns = ['compared','timebin', 'pval_adjust_bh'])
    return mw_posthoc_on_sig_bins_df


## plot significance annotation functions
#star marker
def add_sig_star_bar_to_timebin(ax_for_star, sig_geno_anova_result_df, height_offset_text, height_offset_line):
    for bin_counter, bin in enumerate(sig_geno_anova_result_df.timebin.unique()):
        pvals_text = "=".join(['p', str(sig_geno_anova_result_df.loc[sig_geno_anova_result_df.timebin== bin,'p-unc'].round(3)[0])])
        ax_for_star.text(x = bin, y = height_offset_text , s = "*", fontsize = 14, horizontalalignment='center', verticalalignment='top',) #add sig. star if sig
        ax_for_star.hlines(y = height_offset_line, xmin = bin- .49, xmax =bin + 0.49, lw = 2) #add line over timebin if sig
#anova + star marker
def add_sig_star_from_timebin_ANOVA(curr_timeseries, g, curr_axis):
    # add sig star by timebin
        time_series_geno_anova= run_welch_ANOVA_on_geno_by_timebin(curr_timeseries, 'bin_end', 'mean activity',  'geno_day')
        sig_geno_anova_timebins = time_series_geno_anova[time_series_geno_anova.sig]
        height_offset_text, height_offset_line, jitter_offset=  get_ax_linedata_and_y_offset(g)#get line data
        add_sig_star_bar_to_timebin(curr_axis,sig_geno_anova_timebins, height_offset_text, height_offset_line)
        return time_series_geno_anova,  sig_geno_anova_timebins
#generic marker

def add_sig_hline_to_bin(ax_for_star, sig_geno_anova_df, h_offset_line):
    for bin_count, bin in enumerate(sig_geno_anova_df.timebin.unique()):
        ax_for_star.hlines(y = h_offset_line, xmin = bin- .49, xmax =bin + 0.49, lw = 2) #add line over timebin if sig

def add_sig_mark_to_timebin(ax_for_star, mark, sig_geno_anova_df, h_offset_text, h_offset_line):
    for bin_count, bin in enumerate(sig_geno_anova_df.timebin.unique()):
        ax_for_star.text(x = bin, y = h_offset_text , s = mark, fontsize = 14, horizontalalignment='center', verticalalignment='top',) #add sig. star if sig
#generic marker + anova
def add_sig_mark_from_timebin_ANOVA(input_tseries, mark, g, curr_axis):
    # add sig star by timebin
        t_series_geno_anova= run_welch_ANOVA_on_geno_by_timebin(input_tseries, 'bin_end', 'mean activity',  'geno_day')
        sig_geno_anova_bins = t_series_geno_anova[t_series_geno_anova.sig]
        height_offset_text, height_offset_line, jitter=  get_ax_linedata_and_y_offset(g)#get line data
        add_sig_mark_to_timebin(curr_axis,mark, sig_geno_anova_bins, height_offset_text, height_offset_line)
        return t_series_geno_anova, sig_geno_anova_bins

## comparisons specific functions
## general structure of nanotator, 
# """
# order = ['Sun', 'Thur', 'Fri', 'Sat']
# ax = sns.boxplot(data=df, x=x, y=y, order=order)
# pairs=[("Thur", "Fri"), ("Thur", "Sat"), ("Fri", "Sun")]
# annotator = Annotator(ax, pairs, data=df, x=x, y=y, order=order)
# annotator.configure(test='Mann-Whitney', text_format='star', loc='outside')
# annotator.apply_and_annotate() """
# ##
## ANOVA specific functions
def run_ANOVA_on_phase_and_geno(df_for_anova, dep_var, factors):
    #plot table of ANOVA
    phase_ANOVA = pg.anova(data = df_for_anova, dv = dep_var, between = factors).set_index('Source').rename({factors[0]: 'phase', 'phase_of_max * geno_day': "phase x geno_day"})
    phase_ANOVA.index.rename("Factor", inplace = True)
    phase_ANOVA_table_trunc = phase_ANOVA.drop(labels = ['MS', 'SS', 'DF'], axis = 1).drop('Residual', axis = 0)
    return phase_ANOVA_table_trunc

def return_ANOVA_and_table_for_plot(df_for_anova, dep_var, factors):
    phase_ANOVA_table_trunc = run_ANOVA_on_phase_and_geno(df_for_anova, dep_var, factors)
    table_data = []
    for i, row in phase_ANOVA_table_trunc.iterrows():
        table_data.append([f"{row['F']:.2f}", f"{row['p-unc']:.2e}", f"{row['np2']:.3f}"])
    return phase_ANOVA_table_trunc, table_data

### phase activaiton correlations 
def get_corr_bootstrap_df(bstrap_storage):
    bstrap_df = pd.DataFrame.from_records(bstrap_storage).reset_index().rename({'index':'geno_day'}, axis = 1).melt(id_vars = 'geno_day', var_name = 'comparison_type', value_name = 'bootstrap_r_vals')
    #get percentiles of bootstrap samples
    bstrap_df['5th'] = bstrap_df['bootstrap_r_vals'].apply(lambda x: np.percentile(x, 5))
    bstrap_df['95th'] = bstrap_df['bootstrap_r_vals'].apply(lambda x: np.percentile(x, 95))
    bstrap_df['mean_bootstrap'] = bstrap_df['bootstrap_r_vals'].apply(np.mean)
    bstrap_df['n_bootstrap'] = bstrap_df['bootstrap_r_vals'].apply(len)
    bstrap_df['range_90_ci'] =  bstrap_df.apply(lambda x: [round(x['5th'],4),round(x['95th'],4)], axis = 1)
    return bstrap_df