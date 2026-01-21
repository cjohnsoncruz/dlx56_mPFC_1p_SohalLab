"""
Diagnostic script to identify the cause of feature mismatch in out-of-distribution decoding.
Run this AFTER you have class_matrix_store, out_of_dist_train_sets, out_of_dist_test_sets defined.

Error context: "X has 107 features, but LinearSVC is expecting 123 features as input"
"""
import numpy as np
import pandas as pd
from matrix_resample_utils import fast_pack_data_local, resample_into_class_matrix

def diagnose_feature_mismatch(class_matrix_store, out_of_dist_train_sets, out_of_dist_test_sets, num_resample=100):
    """
    Diagnose why train and test matrices end up with different numbers of features.
    """
    phase_names = list(class_matrix_store.keys())
    issues_found = []

    print("=" * 80)
    print("DIAGNOSTIC: Checking for feature count mismatches in out-of-distribution decoding")
    print("=" * 80)

    # Check a sample enrichment phase and geno_day
    e_phase = phase_names[0]
    geno_days = list(class_matrix_store[e_phase][e_phase].keys())

    for geno_day_curr in geno_days:
        print(f"\n--- Checking geno_day: {geno_day_curr}, enriched in: {e_phase} ---")

        # Build resampled matrices for all phases (same as decoder does)
        ensemble_resample_in_phase_dict = {}
        for class_name in phase_names:
            try:
                class_matrix = resample_into_class_matrix(
                    class_matrix_store, num_resample, e_phase, class_name, geno_day_curr
                )
                ensemble_resample_in_phase_dict[class_name] = class_matrix

                # Check for duplicate indices
                idx = class_matrix.index
                n_unique = len(set(idx))
                n_total = len(idx)
                if n_unique != n_total:
                    print(f"  WARNING: {class_name} has DUPLICATE unit IDs! {n_total} total, {n_unique} unique")
                    issues_found.append(f"Duplicate IDs in {class_name} for {geno_day_curr}")
                else:
                    print(f"  {class_name}: {n_total} units (no duplicates)")
            except Exception as ex:
                print(f"  ERROR building {class_name}: {ex}")

        # Check each train/test pair
        for phase_count, (train_pair, test_pair) in enumerate(zip(out_of_dist_train_sets, out_of_dist_test_sets)):
            class_0_train, class_1_train = train_pair
            class_0_test, class_1_test = test_pair

            print(f"\n  Pair {phase_count}: Train on {train_pair} -> Test on {test_pair}")

            try:
                # Build train matrix
                class_mat_0_train = ensemble_resample_in_phase_dict.get(class_0_train)
                class_mat_1_train = ensemble_resample_in_phase_dict.get(class_1_train)

                if class_mat_0_train is None or class_mat_1_train is None:
                    print(f"    SKIP: Missing class matrix")
                    continue

                concat_matrix_train, concat_labels_train = fast_pack_data_local(
                    class_mat_0_train, class_mat_1_train, 0, 1
                )

                # Build test matrix
                class_mat_0_test = ensemble_resample_in_phase_dict.get(class_0_test)
                class_mat_1_test = ensemble_resample_in_phase_dict.get(class_1_test)

                if class_mat_0_test is None or class_mat_1_test is None:
                    print(f"    SKIP: Missing class matrix")
                    continue

                concat_matrix_test, concat_labels_test = fast_pack_data_local(
                    class_mat_0_test, class_mat_1_test, 0, 1
                )

                # Get unit IDs
                unit_IDs_train = concat_matrix_train.index.values
                unit_IDs_test = concat_matrix_test.index.values

                print(f"    Train matrix: {concat_matrix_train.shape} (units: {len(unit_IDs_train)})")
                print(f"    Test matrix:  {concat_matrix_test.shape} (units: {len(unit_IDs_test)})")

                # Check for duplicates in indices
                train_unique = len(set(unit_IDs_train))
                test_unique = len(set(unit_IDs_test))

                if train_unique != len(unit_IDs_train):
                    print(f"    *** ISSUE: Train has duplicate unit IDs! {len(unit_IDs_train)} total, {train_unique} unique")
                    issues_found.append(f"Train duplicates in pair {phase_count}")

                if test_unique != len(unit_IDs_test):
                    print(f"    *** ISSUE: Test has duplicate unit IDs! {len(unit_IDs_test)} total, {test_unique} unique")
                    issues_found.append(f"Test duplicates in pair {phase_count}")

                # Compute boolean masks (as decoder does)
                unit_IDs_test_set = set(unit_IDs_test)
                unit_IDs_train_set = set(unit_IDs_train)

                train_IDs_in_test_bool = [u in unit_IDs_test_set for u in unit_IDs_train]
                test_IDs_in_train_bool = [u in unit_IDs_train_set for u in unit_IDs_test]

                n_train_in_test = sum(train_IDs_in_test_bool)
                n_test_in_train = sum(test_IDs_in_train_bool)

                print(f"    Train units in test: {n_train_in_test}")
                print(f"    Test units in train: {n_test_in_train}")

                if n_train_in_test != n_test_in_train:
                    print(f"    *** MISMATCH FOUND! This causes the decoding error ***")
                    print(f"        Model trained with {n_train_in_test} features")
                    print(f"        But test data has {n_test_in_train} features")
                    issues_found.append(f"Feature mismatch in pair {phase_count}: {n_train_in_test} vs {n_test_in_train}")

                    # Find the problematic IDs
                    intersection = unit_IDs_train_set & unit_IDs_test_set
                    print(f"        True intersection size: {len(intersection)}")

                    # Check for case sensitivity or whitespace issues
                    train_str = [str(u).strip() for u in unit_IDs_train]
                    test_str = [str(u).strip() for u in unit_IDs_test]
                    if len(set(train_str)) != len(set(unit_IDs_train)):
                        print("        WARNING: String conversion changes train uniqueness!")
                    if len(set(test_str)) != len(set(unit_IDs_test)):
                        print("        WARNING: String conversion changes test uniqueness!")
                else:
                    print(f"    OK: Both have {n_train_in_test} common features")

            except Exception as ex:
                print(f"    ERROR: {ex}")
                import traceback
                traceback.print_exc()

    print("\n" + "=" * 80)
    if issues_found:
        print(f"SUMMARY: Found {len(issues_found)} issues:")
        for issue in issues_found:
            print(f"  - {issue}")
    else:
        print("SUMMARY: No obvious issues found in unit alignment")
    print("=" * 80)

    return issues_found


def check_raw_data_for_duplicates(trial_tseries_df, unit_ID_col='unique_ID', subject_col='name'):
    """
    Check the raw trial timeseries data for duplicate unit IDs that could cause issues.
    """
    print("\n" + "=" * 80)
    print("DIAGNOSTIC: Checking raw data for duplicate unit IDs")
    print("=" * 80)

    # Check for duplicate unit IDs within the same subject and task phase
    for phase in trial_tseries_df['task_phase_vec'].unique():
        phase_df = trial_tseries_df[trial_tseries_df['task_phase_vec'] == phase]

        for subj in phase_df[subject_col].unique():
            subj_df = phase_df[phase_df[subject_col] == subj]
            unit_ids = subj_df[unit_ID_col].values

            # Within a single trial, should each unit appear once?
            for trial in subj_df['trial_num'].unique():
                trial_df = subj_df[subj_df['trial_num'] == trial]
                trial_units = trial_df[unit_ID_col].values

                if len(trial_units) != len(set(trial_units)):
                    print(f"DUPLICATE within trial: {subj}, {phase}, trial {trial}")
                    print(f"  Total: {len(trial_units)}, Unique: {len(set(trial_units))}")
                    # Find the duplicates
                    from collections import Counter
                    counts = Counter(trial_units)
                    dups = {k: v for k, v in counts.items() if v > 1}
                    print(f"  Duplicated IDs: {dups}")


# Example usage (run in notebook after defining class_matrix_store):
# from diagnose_decode_mismatch import diagnose_feature_mismatch, check_raw_data_for_duplicates
# issues = diagnose_feature_mismatch(class_matrix_store, out_of_dist_train_sets, out_of_dist_test_sets)
# check_raw_data_for_duplicates(trial_tseries_df_norm)