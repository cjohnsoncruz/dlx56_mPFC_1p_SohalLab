##stat_tests.py
#TO- store the custom stat tests devised for post-hoc testing and plotting on dataset viz. 
#started 12/8/24 by CJC
from scipy import stats
from helper_functions import * 
import math 
from scipy.stats import norm

#### PERMUTATION TEST 
#new- nonparametric common language effect size test

#scale robust cohen d
def return_winsorized_data(data:np.array,bounds = [20,80]):
    """TO- given 1D numpy array, return winsorized data. Add flag to cohen d cal""" 
    percentile_lim =  [np.percentile(data, bounds[0]), np.percentile(data, bounds[1])]
    data_winsor = data.copy()
    data_winsor[data_winsor < percentile_lim[0]] = percentile_lim[0]
    data_winsor[data_winsor > percentile_lim[1]] = percentile_lim[1]
    return data_winsor

def run_permutation_test_on_diff_of_vector_means(data_group_1_values, data_group_2_values, n_resamples = 10000):
    if n_resamples == None:
        n_resamples = 10000
    res = stats.permutation_test((data_group_1_values, data_group_2_values), get_diff_of_vector_means, n_resamples =n_resamples, vectorized = True, alternative = 'two-sided')
    result_dict = {'statistic': res.statistic, 'pvalue': res.pvalue}
    output = list(result_dict.values())
    return output

##### FOR BOOTSTRAP DATA, CHECK SEPARATION OF DISTRIBUTIONS
def get_pvalue_from_CI(estimate, ci_lims,ci_type = '95'):
    """TO- given CI limits, find pvalue. Based off Altman & Bland 2011:  https://doi.org/10.1136/bmj.d2304"""
    ci_lims = np.array(ci_lims)
    ci_range = ci_lims.max() - ci_lims.min()    
    #  1 calculate the standard error given normality assumption: SE = (u − l)/(2×1.96)
    z = {'95': 1.96, '99': 2.58}[ci_type] 
    se = ci_range/(2*z)
    # 2 calculate the margin of error: MOE = 1.96SE
    estimate_zscore = estimate/se 
    # 3 calculate the p-value: p = exponent(-0.717*estimate_zscore - 0.416*estimate_zscore**2)
    pval = math.exp(-0.717*estimate_zscore - 0.416*estimate_zscore**2)
    return pval

def get_cohen_d_CI(cohen_d, n_array, ci_type = '95'):
    """TO- given cohen d, and ci type, find CI limitsusing Hedge and Olkin formula"""
    z = {'95': 1.96, '99': 2.58}[ci_type] 
    summed_n = np.sum(n_array)
    product_n = np.prod(n_array)
    hedge_olkin_sigma = np.sqrt((summed_n/product_n)+((cohen_d**2)/(2*summed_n)))
    ci_range = z*hedge_olkin_sigma
    ci_lims = [cohen_d-ci_range, cohen_d+ci_range]
    return ci_lims

    # permutation test null distribution of Cohen's d values
def permutation_cohen_d_null(g1_values, g2_values, n_permutations=1000, seed=None):
    """Compute null distribution of Cohen's d by permutation test.
    Permutes group labels to generate null distribution of effect sizes."""
    g1 = np.asarray(g1_values)
    g2 = np.asarray(g2_values)
    n1 = g1.size; n2 = g2.size
    combined = np.concatenate((g1, g2))
    # vectorized permutation via random sorting
    rng = np.random.default_rng(seed)
    rand = rng.random((n_permutations, n1 + n2))
    perm_idx = np.argsort(rand, axis=1)
    perm_vals = combined[perm_idx]
    m1 = np.nanmean(perm_vals[:, :n1], axis=1)
    m2 = np.nanmean(perm_vals[:, n1:], axis=1)
    # recompute pooled SD per permutation
    sd1 = np.nanstd(perm_vals[:, :n1], axis=1)
    sd2 = np.nanstd(perm_vals[:, n1:], axis=1)
    pooled_sd_perm = sd1 #np.sqrt((sd1**2 + sd2**2) / 2)
    null_dist = np.abs((m1 - m2) / pooled_sd_perm) #because this is null distribution, assume equal variance 
    return null_dist

def test_group_mean_cohen_d(
    g1_values,
    g2_values,
    sdev_factor = 1,
    cohen_d_target= 1.65,
    use_robust_cohen_d = False,
    use_robust_cohen_d_coefficient = False):
    """TO- find the mean and sdev of each group, and find if the separation in means is > sum (standard devs). Takes 2 numpy arrays/lists for input values """
    if use_robust_cohen_d: #winsorize data
        g1_values = return_winsorized_data(g1_values)
        g2_values = return_winsorized_data(g2_values)
    #given array input, get sdev and mean of values
    g1 = {'std':np.nanstd(g1_values), 'mean':np.nanmean(g1_values)}
    g2 = {'std':np.nanstd(g2_values), 'mean':np.nanmean(g2_values)}
    # get abs value of group diff, and 
    pooled_sd = np.sqrt((g1['std']**2 + g2['std']**2)/2)
    # sum_of_stdevs = g1['std']*sdev_factor+g2['std']*sdev_factor
    group_mean_diff = np.abs(g1['mean']-g2['mean'])
    # #get pseudo pvalue by taking U3- which is 
    cohen_d = group_mean_diff/pooled_sd
    if use_robust_cohen_d_coefficient:
        cohen_d = cohen_d * .642 #based on robust coefficient from: Algina et al 2005
    U3 = norm.cdf(cohen_d)
    pseudo_pvalue = 1- U3
    #METHOD 2: permutation test
    null_dist = permutation_cohen_d_null(g1_values, g2_values, n_permutations=10000, seed=None)
    count_extreme = np.sum(null_dist >= cohen_d)
    permutation_test_pvalue = (count_extreme + 1) / (null_dist.size + 1) #smooth pvalue to avoid zero pvalues

    #METHOD 2: find pvalue from cohen d target,suing cohen's u3
    # Cohen’s d can be converted to Cohen’s U3 using the following formula    # U3=Φ(d) where Φ is the cumulative distribution function of the standard normal distribution
    # #get and return dict
    result_dict = {'pooled_sd' :pooled_sd, 'group_mean_diff': group_mean_diff, 
                'group_1_mean': g1['mean'], 'group_1_std':g1['std'],
                'group_2_mean':g2['mean'], 'group_2_std':g2['std'],
                'cohen_d':cohen_d, 'pseudo_pvalue' : pseudo_pvalue, 
                'permutation_test_pvalue': permutation_test_pvalue}
    return result_dict


def test_group_mean_separation(g1_values,g2_values, sdev_factor = None):
    """TO- find the mean and sdev of each group, and find if the separation in means is > sum (standard devs). Takes 2 numpy arrays/lists for input values """
    if sdev_factor == None:
        sdev_factor = 1 #coefficient for tuning how much you want the separation to be 
    #given array input, get sdev and mean of values
    g1 = {'std':np.nanstd(g1_values), 'mean':np.nanmean(g1_values)}
    g2 = {'std':np.nanstd(g2_values), 'mean':np.nanmean(g2_values)}
    # get abs value of group diff, and 
    sum_of_stdevs = g1['std']*sdev_factor+g2['std']*sdev_factor
    group_mean_diff = np.abs(g1['mean']-g2['mean'])
    # #get pseudo pvalue
    use_pseudo_pvalue = False
    if use_pseudo_pvalue:
        pseudo_pvalue = 1-stats.norm.cdf(group_mean_diff/sum_of_stdevs)
    else:
        pseudo_pvalue = 1 - (group_mean_diff >sum_of_stdevs)*0.999
    # #get and return dict
    result_dict = {'sum_of_stdevs' :sum_of_stdevs, 'group_mean_diff': group_mean_diff, 
                'group_1_mean': g1['mean'], 'group_1_std':g1['std'], 'group_2_mean':g2['mean'], 'group_2_std':g2['std'],
                'mean_diff_more_than_sdevs':group_mean_diff >sum_of_stdevs, 'pseudo_pvalue' : pseudo_pvalue }
    return result_dict


#### BOOTSTRAP TEST ON DIFFERENCE OF MEANS
def get_bootstrap_diff_of_means(data_group_1_values, data_group_2_values, n_bootstrap = 1000):
    #TO- given 2 numpy array vectors, resample n_bootstrap times for each, and return the difference of means
    # bootstrap with replacement for each data group#
    local_rng = np.random.default_rng() #create a Generator instance with default_rng 
    #loop over all values
    result_list = []
    # n_bootstrap = 1000
    for b in np.arange(n_bootstrap):
        resample_1 = local_rng.choice(data_group_1_values,size = len(data_group_1_values))
        resample_2 = local_rng.choice(data_group_2_values,size = len(data_group_2_values))
        diff = resample_1.mean() - resample_2.mean() # print(diff) # print(resample_1, resample_2)
        result_dict = {"resample_run": b , "difference_of_means": diff , "group_1_mean":  resample_1.mean(), "group_2_mean": resample_2.mean()}
        result_list.append(result_dict)

    boot_df = pd.DataFrame.from_records(result_list)
    return boot_df# scipy.stats.bootstrap((data_group_1_values, data_group_2_values), get_cosine_sim)

### MISC FUNCTIONS
def get_diff_of_vector_means(x, y, axis):
    return np.nanmean(x, axis=axis) - np.nanmean(y, axis=axis)

#### DISTRIBUTION OVERLAP CHECK 
def get_overlap_pvalue(distrib_a,distrib_b, ci_a_lims, ci_b_lims, pval_type = None):
    """WIP- just returns flat 0.005 if overlap exists"""
    #get overlap information
    if pval_type == None:
        #then just set it to return a flat value
        pval_type = 'flat'
    no_overlap_exists = find_if_distrib_overlap(distrib_a,distrib_b, ci_a_lims, ci_b_lims)
    ## set pval- WIP
    pval = []
    if pval_type == 'flat':
        if no_overlap_exists:
            pval = 0.005
        else:
            pval = 1
    if pval_type == 'distrib_distance':
        if no_overlap_exists:
            pval = 0.005
        else:
            pval = 1
    return pval

def find_if_distrib_overlap(distrib_a,distrib_b, ci_a_lims, ci_b_lims, overlap_type = None):
    """ TO, given 2 values for distribution a and b, where values are start and stop of range of interest, find if overlap exists.
    ci_a_lims, ci_b_lims are indexes. default check is if 2 distributions OVERLAP. alt mode- check if 2 distrib DONT" OVERLAP. 
    Overlap_types =['overlap_true', 'overlap_false', None] (default = None)"""
    if overlap_type == None:
        overlap_type = 'overlap_true'

    a_range_start, a_range_end = distrib_a[ci_a_lims[0],], distrib_a[ci_a_lims[1],]
    b_range_start, b_range_end = distrib_b[ci_b_lims[0],], distrib_b[ci_b_lims[1],]
    ##check overlap
    a_start_before_b_end = (a_range_start <= b_range_end)
    b_start_before_a_end = (b_range_start <= a_range_end)
    if overlap_type == 'overlap_true':
        overlap_check = a_start_before_b_end & b_start_before_a_end
    if overlap_type == 'overlap_false': #check if a NOT in b range, and b NOT in a range
        overlap_check = not(overlap_check)
    ## WIP- add bool to flip comparison?
    return overlap_check



##posthoc testing functions