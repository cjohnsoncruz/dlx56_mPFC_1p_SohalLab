#for post shuffle, info extraction
import pandas as pd
import numpy as np
from datetime import datetime

## ensemble info for all subjects
def get_cell_ensemble_info_per_subject(raster_dataframes, all_subject_shuffles, n_shuf_per_subject):
    """ Loops through all subjects and computes cell ensemble enrichment info """
    all_subject_ensemble_info = []
    for subject_name, raster_df in raster_dataframes.items():
        print(f"Processing subject: {subject_name}")
        cell_col = [c for c in raster_df.columns if 'cell' in c]
        all_shuffle_means = all_subject_shuffles[subject_name]
        subject_ensemble_info = get_cell_stage_enrichment(all_shuffle_means, raster_df, cell_col, n_shuf_per_subject)
        all_subject_ensemble_info.append(subject_ensemble_info)
    all_ensembles = pd.concat(all_subject_ensemble_info).reset_index(drop=True)
    #add metadata
    all_ensembles['neuron_id'] = all_ensembles['subject_name'] + '-' + all_ensembles['cell'].str.replace('cell_','')
    all_ensembles['date_made'] = datetime.now().strftime("%d-%b-%Y")
    all_ensembles['n_shuffles'] = n_shuf_per_subject
    
    return all_ensembles
## main enrichment analysis function
def get_cell_stage_enrichment(all_shuffle_means, raster_df, cell_col, n_shuf_per_subject):
    ## code for enrichment analysis: given N shuffles, find the 95th percentile value for each cell at each task stage
    cell_threshold = all_shuffle_means.groupby('task_stage')[cell_col].agg(lambda x: np.percentile(x, 95)) #empirical?

    #get real raster mean activity data (DESPARSIFY if necessary)
    for col in cell_col:
        if isinstance(raster_df[col], pd.SparseDtype):
            raster_df.loc[:, col] = raster_df[col].sparse.to_dense()
        raster_df.loc[:, col] = raster_df[col].astype(float)
            
    #group real data by trial_section and task_stage
    real_mean_activity = raster_df.groupby(by = ['trial_section', 'task_stage'])[cell_col].mean().loc['post_outcome', (slice(None))].drop(0)

    # FIX: Only keep stages that exist in both threshold and real data
    common_stages = cell_threshold.index.intersection(real_mean_activity.index)
    cell_threshold = cell_threshold.loc[common_stages]
    real_mean_activity = real_mean_activity.loc[common_stages]

    #get % of shuffle values greater than or equal to real cell activity
    counts_per_cell = []
    for stage, group in all_shuffle_means.groupby("task_stage"):
        # print(f"checking {stage}")
        real_values = real_mean_activity.loc[stage, cell_col] #get % of shuffle greater than or equal to real
        comparison = group[cell_col] >= real_values      # broadcast columnwise
        counts = comparison.sum()                         # count True per cell
        counts.name = stage                               # label this row
        counts_per_cell.append(counts)
    shuf_percentile = pd.DataFrame(counts_per_cell)/n_shuf_per_subject

    #get boolean mask of enriched cells
    enriched_cells = (real_mean_activity > cell_threshold)

    # melt dataframes for joining analysis
    shuf_percentile_long = shuf_percentile.reset_index().melt(id_vars = 'index', var_name = 'cell', value_name = r'percent_shuffle >= real').rename(columns = {'index': 'task_stage'})
    cell_enrich_long = enriched_cells.reset_index().melt(id_vars = 'task_stage', var_name = 'cell', value_name = 'enriched') #cells activity > threshold
    cell_activity_long = real_mean_activity.reset_index().melt(id_vars = 'task_stage', var_name = 'cell', value_name = 'mean') #real mean activity of cells
    cell_thresh_long = cell_threshold.reset_index().melt(id_vars = 'task_stage', var_name = 'cell', value_name = 'percentile_95') #95th percentile of shuffles

    #join dataframes
    cell_ensemble_info = pd.merge(pd.merge(cell_thresh_long, cell_activity_long, on=['task_stage','cell']), cell_enrich_long, on=['task_stage','cell'])
    cell_ensemble_info = pd.merge(cell_ensemble_info, shuf_percentile_long, on=['task_stage','cell'])
    #add subject marker 
    cell_ensemble_info['subject_name'] = raster_df['subject_name'].unique()[0]
    return cell_ensemble_info
