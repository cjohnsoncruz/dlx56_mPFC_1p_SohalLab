# ensemble_overlap- made 2.28.26
# centralizes ensemble overlap functions
######### IMPORTS
import matplotlib
from matplotlib import pyplot as plt
from matplotlib_venn import venn2
from collections import defaultdict
from scipy.stats import chi2_contingency

import seaborn as sns
import pandas as pd 
import numpy as np
#custom imports
import helper_functions
from ax_modifier_functions import replace_first_underscore_linebreak, set_labels, set_ax_title_xlabel_ylabel

## PLOT FUNCTIONs:

def plot_save_ensemble_overlap_fig(unit_mean_tseries,
                                   ensemble_to_plot,
                                   geno_order,
                                   stage_names,
                                   venn_fig_size, 
                                   label_text_align = {0: 'right', 1: 'center'}, 
                                   hspace = (1.5/1.5)*0.75,
                                   wspace = 0.01,
                                   fig_num = 5,
                                   stage_palette_dict = defaultdict(None),
                                   use_custom_venn_colors= True,
                                   **kwargs):
    
    fig, ax_array = plt.subplots(2,2,figsize =venn_fig_size, 
                                 layout = 'tight', 
                                 gridspec_kw = {'wspace':wspace,'hspace':hspace}) #(1.5/venn_fig_size[1]) is because 0.75 works for 1.5, so below that, increase spacing, and above that, decrease
    ## main venn plot info 
    set_colors = {True: tuple(stage_palette_dict[x] for x in ensemble_to_plot), False: ('r', 'g')}[use_custom_venn_colors]
    venn_objs = plot_ensemble_venn(ax_array, unit_mean_tseries, ensemble_to_plot, geno_order, stage_names,set_colors = set_colors, label_text_align = label_text_align)
    # for v in venn_objs.values():
    #     [v.set_labels[k].set_horizontalalignment(val) for k,val in label_text_align.items()] #equiv to: # labels[0].set_horizontalalignment('right') # labels[1].set_horizontalalignment('center')
    # ##save overlap fig
    fig_name = f"Ensemble cell overlap by geno for {'_'.join(ensemble_to_plot)}"
    helper_functions.save_fig_in_main_fig_dir(fig, fig_name= fig_name, folder_key=fig_num, filetypes_to_save = ['png'])
    return fig, ax_array

def plot_ensemble_venn(ax_array, 
                       input_df,
                         ensemble_to_plot,
                         geno_order,
                           stage_names,
                             set_colors = ("r", "g"),
                              label_text_align:dict = {} ):
    set1, set2 = ensemble_to_plot
    venn_objs = dict()
    ## determine # of cells enriched in stage 1 and stage 2, and only either
    geno_crosstab = get_geno_stage_overlap_crosstab(input_df, ensemble_to_plot,geno_order,stage_names)

    for g, geno in enumerate(geno_order): #iterate over axes
        ax = ax_array.flat[g]
        #query pre-existing geno overlap table 
        geno_subset = geno_crosstab.loc[geno_crosstab.geno_day == geno,:]
        set1_size=geno_subset.n_only_in_set_1.values[0]
        set2_size=geno_subset.n_only_in_set_2.values[0]
        total_overlap = geno_subset.total_overlap.values[0]
        venn_objs[geno] = venn2(ax = ax, subsets = (set1_size,set2_size,total_overlap), set_colors = set_colors,
              set_labels = (replace_first_underscore_linebreak(set1), replace_first_underscore_linebreak(set2)))
        for lbl in venn_objs[geno].set_labels:
            lbl.set_fontsize(6)
        venn_title =  f"{geno}:"
        set_labels(ax, {'title':venn_title,})
    
    #new- 12/16/25- move alignment into plot_ensemble_venn()
    for v in venn_objs.values():
        [v.set_labels[k].set_horizontalalignment(val) for k,val in label_text_align.items()] #equiv to: # labels[0].set_horizontalalignment('right') # labels[1].set_horizontalalignment('center')

    return venn_objs
## ###############################################################
## utility FUNCTION STORAGE:

def make_premade_comparison_pvalue_df(group_list:list, pvalue_list:list):
    ''' To, given a known pvalue for a comparison, bundle and overwrite values '''
    ## zip values together into dict
    comparison_pval_df = pd.DataFrame([dict(group_1= e[0], group_2 = e[1], pvalue=p) for e,p in zip(group_list, pvalue_list)])
    return comparison_pval_df

def update_posthoc_pvalues(posthoc_df:pd.DataFrame, comparison_pvalues:pd.DataFrame):
    #shift index to multiindex of (group1, group2) to streamline accessing
    post = posthoc_df.set_index(["group_1","group_2"])
    cmp  = comparison_pvalues.set_index(["group_1","group_2"])["pvalue"]
    post["pvalue"].update(cmp)
    #overwrite with updated values
    updated_posthoc = posthoc_df
    updated_posthoc["pvalue"] = post["pvalue"].values
    return updated_posthoc

def compute_ensemble_overlap_chi2(unit_mean_tseries, all_ensemble_pairs, geno_order, stage_names):
    """Compute overlap crosstabs and chi-squared tests for each ensemble pair."""
    overlap_tab = []

    for ensemble_to_plot in all_ensemble_pairs:
        overlap = get_geno_stage_overlap_crosstab(unit_mean_tseries, ensemble_to_plot, geno_order,stage_names)
        overlap['contingency'] = overlap.apply(lambda x: 
                                               np.array(
                                                   [[(x.n_total-x.n_only_in_set_1-x.n_only_in_set_2-x.total_overlap), x.n_only_in_set_1],
                                                     [x.n_only_in_set_2, x.total_overlap]]
                                                     ),axis = 1)
        #contingency table: [total - only_1 - only_2 - both_1_2], only_1], [only_2, both_1_2] # resChi2ContingencyResult-    An object containing attributes:
        # statistic-float- The test statistic. # pvalue-float The p-value of the test. # dof-int: The degrees of freedom. NaN if method is not None. # expected_freq-ndarray, same shape as observed
        overlap[['statistic', 'pvalue', 'dof', 'expected_frequency']] = overlap.apply(lambda x: chi2_contingency(x.contingency), axis=1, result_type='expand').values
        overlap_tab.append(overlap)

    return pd.concat(overlap_tab) 

def get_geno_stage_overlap_crosstab(input_df, 
                                    ensemble_to_plot,
                                    geno_order,
                                    stage_names, 
                                    unit_ID_col = 'neuron_ID'):
    ''' To- given a set of genotypes to iterate over, anda  dataframe with boolean (ON or OFF) in stage of interests, find the crosstabulation''' 
    set1, set2 = ensemble_to_plot        ## determine # of cells enriched in stage 1 and stage 2, and only either
    output_list = []
    for g, geno in enumerate(geno_order):
        geno_enrich_matrix = input_df.loc[input_df.geno_day==geno, :].groupby(unit_ID_col)[stage_names].first()
        overlap_vec = (geno_enrich_matrix[set1]==1) & (geno_enrich_matrix[set2] ==1)
        total_overlap =  overlap_vec.sum()
        set1_only_size = geno_enrich_matrix[set1].sum().astype(int) - total_overlap
        set2_only_size = geno_enrich_matrix[set2].sum().astype(int) - total_overlap
        output = dict(geno_day = geno,
                      set_1_name = set1,
                      set_2_name = set2, 
                      total_overlap = total_overlap, 
                      n_total = overlap_vec.size,
                      fraction_total_overlap = total_overlap/overlap_vec.size,
                      percent_total_overlap=100* (total_overlap/overlap_vec.size),
                      n_only_in_set_1 = set1_only_size,
                      n_only_in_set_2=set2_only_size, )
        output_list.append(output)
    geno_crosstab= pd.DataFrame.from_records(output_list)
    return geno_crosstab
