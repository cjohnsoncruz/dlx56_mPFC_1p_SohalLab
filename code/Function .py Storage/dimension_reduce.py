# dimension_reduce.py- contains scripts and functions for TSNE, PCA and other dimensionality reduction techniques
##TSNE

from sklearn.manifold import TSNE
from sklearn.decomposition import PCA 
def return_TSNE_projection(input_matrix, tsne_params = None):
    ''' Returns TSNE projection of input matrix
    input_matrix = (samples x features) matrix
    tsne_params = dict of TSNE parameters
    returns tsne_array 
    '''
    if tsne_params == None:
        tsne_params = {'n_components': 2, "perplexity": 90, "method":'exact', 'init':'pca'}
    tsne_array = TSNE(metric = 'cosine', **tsne_params).fit_transform(input_matrix)
    return tsne_array

def run_TSNE_on_mean_activity(input_AVs, tsne_params= None):
    """ Requires cell x stage matrix of AVs, and dict of TSNE input params"""
    if tsne_params == None:
        tsne_params = {'n_components': 2, "perplexity": 90, "method":'exact', 'init':'pca'}
    tsne_array = TSNE(metric = 'cosine', **tsne_params).fit_transform(input_AVs)
    tsne_output =input_AVs
    tsne_output = input_AVs.assign(**{f"dim_{n+1}":tsne_array[:,n] for n in range(tsne_params['n_components'])})
    return tsne_output

def return_TSNE_on_stage_AV_w_enrich_labels(input_AVs, enrichment_labels, stage_names:list):
    """ Assigns ensemble class labels to new columns in TSNE df that takes mean stage AVs and projects into TSNE"""
    #return TSNE projected matrix
    sig_suffix = "_ens" #what suffix to use to distinguish the enrichment vectors from the activity vecdtors 
    TSNE_df = run_TSNE_on_mean_activity(input_AVs)
    TSNE_df= TSNE_df.merge(enrichment_labels, how = 'inner', left_index = True, right_index = True, suffixes = ("", sig_suffix))
    #join AV with enrichment enrichment_matrix
    TSNE_df['n_sig'] = TSNE_df[[s + sig_suffix for s in stage_names]].sum(axis = 1)
    TSNE_df['multi_ensemble'] = TSNE_df['n_sig']> 1

    TSNE_df['is_sig'] = TSNE_df['n_sig']> 0
    TSNE_df['ensemble'] = 'none'
    TSNE_df.loc[TSNE_df.n_sig>0, 'ensemble'] = TSNE_df.loc[TSNE_df.n_sig>0, stage_names].idxmax(axis = 1)

    return TSNE_df 

## PCA

