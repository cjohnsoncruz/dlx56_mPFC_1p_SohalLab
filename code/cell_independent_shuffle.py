### Cell-Independent Circular Shuffle Analysis (MATLAB-style)

def circular_shuffle_mean_activity_cell_independent(raster_df, cell_col, category_value, 
                                                 label_col='task_stage', n_shuffles=1000, 
                                                 random_seed=None):
    """
    Cell-independent circular shuffle analysis (MATLAB-style).
    Each cell gets its own independent set of circular shifts.
    
    Parameters
    ----------
    raster_df : pd.DataFrame
        DataFrame with frame-level data
    cell_col : str
        Column name of the cell to analyze
    category_value : str
        The category/task_stage to analyze
    label_col : str, default='task_stage'
        Column containing categorical labels
    n_shuffles : int, default=1000
        Number of shuffles to perform
    random_seed : int, optional
        Random seed for reproducibility
        
    Returns
    -------
    dict
        Same format as circular_shuffle_mean_activity()
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Convert to numpy arrays
    if hasattr(raster_df[cell_col], 'sparse'):
        activity = raster_df[cell_col].sparse.to_dense().values.astype(np.float64)
    else:
        activity = raster_df[cell_col].values.astype(np.float64)
    
    labels = raster_df[label_col].values
    n_frames = len(labels)
    
    # Compute observed mean
    observed_mask = (labels == category_value)
    observed_mean = activity[observed_mask].mean()
    n_frames_observed = observed_mask.sum()
    
    # Generate random shifts (n_shuffles x 1)
    shifts = np.random.randint(1, n_frames, size=(1, n_shuffles))
    
    # Pre-allocate results
    shuffled_means = np.empty(n_shuffles, dtype=np.float64)
    
    # Process each shuffle with its own shift
    for i in range(n_shuffles):
        # Apply circular shift to labels
        shifted_labels = np.roll(labels, shifts[0, i])
        shifted_mask = (shifted_labels == category_value)
        shuffled_means[i] = activity[shifted_mask].mean()
    
    # Calculate p-value (one-tailed)
    p_value = (shuffled_means >= observed_mean).mean()
    
    return {
        'observed_mean': observed_mean,
        'shuffled_means': shuffled_means,
        'p_value': p_value,
        'n_frames_in_category': n_frames_observed,
        'shuffle_distribution_mean': shuffled_means.mean(),
        'shuffle_distribution_std': shuffled_means.std()
    }


def batch_circular_shuffle_analysis_cell_independent(raster_df, cell_cols, categories, 
                                                   label_col='task_stage', n_shuffles=1000,
                                                   parallel=True, n_jobs=-1):
    """
    Batch process multiple cells with cell-independent shuffles.
    
    Parameters
    ----------
    raster_df : pd.DataFrame
        Input data
    cell_cols : list
        List of cell columns to process
    categories : list
        List of categories to test
    label_col : str, default='task_stage'
        Column containing labels
    n_shuffles : int, default=1000
        Number of shuffles per test
    parallel : bool, default=True
        Use parallel processing
    n_jobs : int, default=-1
        Number of parallel jobs (-1 = all cores)
        
    Returns
    -------
    pd.DataFrame
        Results with one row per cell-category combination
    """
    from tqdm.notebook import tqdm
    
    # Generate all combinations to test
    tasks = [(cell, cat) for cell in cell_cols for cat in categories]
    results = []
    
    def process_one(cell, category):
        result = circular_shuffle_mean_activity_cell_independent(
            raster_df=raster_df,
            cell_col=cell,
            category_value=category,
            label_col=label_col,
            n_shuffles=n_shuffles
        )
        return {
            'cell': cell,
            'category': category,
            'p_value': result['p_value'],
            'observed_mean': result['observed_mean'],
            'shuffle_mean': result['shuffle_distribution_mean'],
            'shuffle_std': result['shuffle_distribution_std'],
            'n_frames': result['n_frames_in_category']
        }
    
    if parallel:
        try:
            from joblib import Parallel, delayed
            
            print(f"Processing {len(tasks)} cell-category combinations in parallel...")
            results = Parallel(n_jobs=n_jobs)(
                delayed(process_one)(cell, cat) 
                for cell, cat in tqdm(tasks, desc="Shuffling")
            )
        except ImportError:
            print("joblib not found, falling back to sequential processing")
            parallel = False
    
    if not parallel:
        results = [process_one(cell, cat) for cell, cat in tqdm(tasks, desc="Shuffling")]
    
    return pd.DataFrame(results)
