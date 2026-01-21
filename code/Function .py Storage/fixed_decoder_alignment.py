"""
Fixed alignment logic for out-of-distribution decoding.

The original code has a bug when there are duplicate unit IDs - the boolean mask
approach produces different counts for train vs test.

ORIGINAL PROBLEMATIC CODE:
    train_IDs_in_test_bool = [u in unit_IDs_test for u in unit_IDs_train]
    test_IDs_in_train_bool = [u in unit_IDs_train for u in unit_IDs_test]
    concat_matrix_test = concat_matrix_test[:, test_IDs_in_train_bool]
    concat_matrix_train = concat_matrix_train[:, train_IDs_in_test_bool]

This fails when: sum(train_IDs_in_test_bool) != sum(test_IDs_in_train_bool)
Which happens when there are duplicate unit IDs in either matrix.

FIX: Use proper set intersection and reindex both DataFrames to common units.
"""

def align_train_test_matrices(concat_matrix_train, concat_matrix_test):
    """
    Properly align train and test matrices to have the same units (features).

    Args:
        concat_matrix_train: DataFrame with index = unit IDs, columns = frames
        concat_matrix_test: DataFrame with index = unit IDs, columns = frames

    Returns:
        train_aligned: numpy array (n_frames_train, n_common_units)
        test_aligned: numpy array (n_frames_test, n_common_units)
        common_units: list of unit IDs that are in both matrices
    """
    # Get unique unit IDs as sets for efficient intersection
    unit_IDs_train = set(concat_matrix_train.index)
    unit_IDs_test = set(concat_matrix_test.index)

    # Compute true intersection
    common_units = sorted(unit_IDs_train & unit_IDs_test)  # sorted for reproducibility

    if len(common_units) == 0:
        raise ValueError("No common units between train and test sets!")

    # Handle potential duplicate indices by using .loc with unique index
    # If there are duplicates, we need to aggregate or take first occurrence
    train_has_dups = concat_matrix_train.index.duplicated().any()
    test_has_dups = concat_matrix_test.index.duplicated().any()

    if train_has_dups:
        # Aggregate duplicates by taking mean (or you could use first)
        concat_matrix_train = concat_matrix_train.groupby(level=0).mean()

    if test_has_dups:
        concat_matrix_test = concat_matrix_test.groupby(level=0).mean()

    # Reindex both to common units (this ensures same order and same units)
    train_reindexed = concat_matrix_train.loc[common_units]
    test_reindexed = concat_matrix_test.loc[common_units]

    # Transpose and convert to numpy (shape: frames x units)
    train_aligned = train_reindexed.T.values
    test_aligned = test_reindexed.T.values

    # Verify alignment
    assert train_aligned.shape[1] == test_aligned.shape[1], \
        f"Alignment failed: train has {train_aligned.shape[1]} features, test has {test_aligned.shape[1]}"

    return train_aligned, test_aligned, common_units


# REPLACEMENT CODE for run_N_decoder_out_of_distribution
# Replace the problematic section (lines ~40-47 of the original function) with:
"""
# OLD CODE (remove this):
unit_IDs_test = concat_matrix_test.index.values
unit_IDs_train = concat_matrix_train.index.values
train_IDs_in_test_bool = [u in unit_IDs_test for u in unit_IDs_train]
test_IDs_in_train_bool = [u in unit_IDs_train for u in unit_IDs_test]
concat_matrix_test = concat_matrix_test.T.values
concat_matrix_train = concat_matrix_train.T.values
concat_matrix_test = concat_matrix_test[:, test_IDs_in_train_bool]
concat_matrix_train = concat_matrix_train[:, train_IDs_in_test_bool]

# NEW CODE (use this instead):
concat_matrix_train, concat_matrix_test, common_units = align_train_test_matrices(
    concat_matrix_train, concat_matrix_test
)
"""

# FULL CORRECTED FUNCTION:
import itertools
import numpy as np
import pandas as pd
from sklearn import svm, model_selection
from datetime import datetime


def run_N_decoder_out_of_distribution_fixed(
    class_matrix_store,
    out_of_dist_train_sets,
    out_of_dist_test_sets,
    num_resample: int,
    test_size=None,
    k_folds=None,
    n_pseudopop_run_range=None,
    reg_penalty='l2'  # Added as parameter since it was undefined in original
):
    """
    Fixed version of out-of-distribution decoder with proper unit alignment.
    """
    from matrix_resample_utils import resample_into_class_matrix, fast_pack_data_local

    all_run_record_store = []

    if test_size is None:
        test_size = 0.5
    if k_folds is None:
        k_folds = 2

    phase_names = class_matrix_store.keys()

    for n_run in n_pseudopop_run_range:
        for e_phase in phase_names:
            for geno_day_curr in class_matrix_store['Late_RS']['Late_RS'].keys():
                ensemble_resample_in_phase_dict = {}
                for class_name in phase_names:
                    class_matrix = resample_into_class_matrix(
                        class_matrix_store, num_resample, e_phase, class_name, geno_day_curr
                    )
                    ensemble_resample_in_phase_dict[class_name] = class_matrix

                for phase_count, phase_pair in enumerate(out_of_dist_train_sets):
                    class_0_train, class_1_train = phase_pair[0], phase_pair[1]

                    # Build training set
                    class_mat_0_train = ensemble_resample_in_phase_dict[class_0_train]
                    class_mat_1_train = ensemble_resample_in_phase_dict[class_1_train]
                    concat_matrix_train, concat_labels_train = fast_pack_data_local(
                        class_mat_0_train, class_mat_1_train, 0, 1
                    )

                    # Build test set
                    test_pair = out_of_dist_test_sets[phase_count]
                    class_0_test, class_1_test = test_pair[0], test_pair[1]
                    class_mat_0_test = ensemble_resample_in_phase_dict[class_0_test]
                    class_mat_1_test = ensemble_resample_in_phase_dict[class_1_test]
                    concat_matrix_test, concat_labels_test = fast_pack_data_local(
                        class_mat_0_test, class_mat_1_test, 0, 1
                    )

                    # ============ FIXED ALIGNMENT LOGIC ============
                    # Use proper set intersection and reindexing
                    concat_matrix_train, concat_matrix_test, common_units = align_train_test_matrices(
                        concat_matrix_train, concat_matrix_test
                    )
                    # ================================================

                    cv = model_selection.StratifiedShuffleSplit(
                        n_splits=k_folds, test_size=test_size
                    )

                    split_records = []
                    for split_count, (train, test) in enumerate(
                        cv.split(np.zeros(len(concat_labels_train)), concat_labels_train)
                    ):
                        target_info = {
                            "pseudopop_run_num": n_run,
                            "enriched_group": e_phase,
                            'geno_day': geno_day_curr,
                            'class_0_train': class_0_train,
                            'class_1_train': class_1_train,
                            'class_0_test': class_0_test,
                            'class_1_test': class_1_test,
                            'regularization': reg_penalty,
                            'date_run': datetime.now(),
                            'n_common_units': len(common_units)  # Added for debugging
                        }

                        model = svm.LinearSVC(
                            C=1, max_iter=1000, penalty=reg_penalty, dual=False, verbose=0
                        )
                        trained_model = model.fit(
                            concat_matrix_train[train, :], concat_labels_train[train]
                        )

                        # Prediction on test data
                        test_data = concat_matrix_test
                        test_labels = concat_labels_test
                        prediction_vec = trained_model.predict(test_data)
                        score_real = np.mean(prediction_vec == test_labels)

                        true_pos = np.mean(
                            [np.array([prediction_vec == 1]) & np.array([test_labels == 1])]
                        )
                        true_neg = np.mean(
                            [np.array([prediction_vec == 0]) & np.array([test_labels == 0])]
                        )
                        false_pos = np.mean(
                            [np.array([prediction_vec == 1]) & np.array([test_labels == 0])]
                        )
                        false_neg = np.mean(
                            [np.array([prediction_vec == 0]) & np.array([test_labels == 1])]
                        )

                        # Compute cosine similarities
                        mean_vectors = {
                            'c0_train': concat_matrix_train[concat_labels_train == 0].mean(axis=0),
                            'c1_train': concat_matrix_train[concat_labels_train == 1].mean(axis=0),
                            'c0_test': concat_matrix_test[concat_labels_test == 0].mean(axis=0),
                            'c1_test': concat_matrix_test[concat_labels_test == 1].mean(axis=0),
                        }
                        cosine_sims = {}
                        for (k1, v1), (k2, v2) in itertools.combinations(mean_vectors.items(), 2):
                            cos_sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                            cosine_sims[f'cosine_{k1}_v_{k2}'] = cos_sim

                        curr_split_info = {
                            'accuracy': score_real,
                            'num_features_used': trained_model.n_features_in_,
                            'num_nonzero_coef': np.sum(np.abs(trained_model.coef_) > 0),
                            'true_pos': true_pos,
                            'true_neg': true_neg,
                            'false_pos': false_pos,
                            'false_neg': false_neg,
                            **cosine_sims
                        }
                        split_records.append(curr_split_info)

                    # Average across splits
                    split_summary = pd.DataFrame.from_records(split_records)
                    split_metrics = split_summary.mean(numeric_only=True)
                    split_labels = pd.Series(target_info)
                    split_summary = pd.concat([split_metrics, split_labels], ignore_index=False)
                    split_summary['train_size'] = 1 - test_size
                    split_summary['k_folds'] = k_folds
                    all_run_record_store.append(split_summary)

    all_run_output = pd.DataFrame.from_records(all_run_record_store)
    return all_run_output