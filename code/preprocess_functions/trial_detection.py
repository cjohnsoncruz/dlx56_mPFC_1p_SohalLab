# trial_detection.py- code for taking 1 x frame behavioral vector and annotating task stages
import numpy as np
from typing import Tuple, Union, Dict, Sequence


##MAIN FUNCTION TO transform label vector into trial number at each frame
def return_trial_num_at_frame(labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray, int]:
    """ Python translation of the MATLAB function return_trial_num_at_frame.
    input: labels: 1D array of per-frame labels.

    Returns:
        trial_num_at_frame: 1D int array of length len(labels). Value j means the frame
            belongs to trial j, with trials numbered starting at 1. Zeros indicate no trial.
        trial_start_index: 1D int array of trial start frame indices, 1-based like MATLAB.
        num_trials: integer count of trials.
    """
    labels = np.asarray(labels)
    assert labels.ndim == 1, "labels must be a 1D array"
    T = labels.size

    # Find trial starts: a start occurs when label switches into 2 or into 9
    starts0 = []  # 0-based start indices for slicing
    for i in range(1, T):
        prev_val = labels[i - 1]
        cur_val = labels[i]
        if ((prev_val != 2 and cur_val == 2) or (prev_val != 9 and cur_val == 9)):
            starts0.append(i)

    num_trials = len(starts0)
    trial_num_at_frame = np.zeros(T, dtype=int)

    if num_trials == 0:
        return trial_num_at_frame, np.array([], dtype=int), 0

    # Assign trial numbers to frame ranges
    for j in range(num_trials - 1):
        s0 = starts0[j]
        s1 = starts0[j + 1]
        trial_num_at_frame[s0:s1] = j + 1  # trials are 1-based

    # Last trial runs to the end
    trial_num_at_frame[starts0[-1]:] = num_trials
    # Convert 0-based starts to 1-based frame indices to match MATLAB output
    trial_start_index = np.asarray(starts0, dtype=int) + 1

    return trial_num_at_frame, trial_start_index, num_trials

    ## MAIN FUNCTION: build index of task stage locations
def build_phase_masks(
    input_labels: Union[Dict[str, Sequence[bool]], Tuple[Sequence[bool], Sequence[bool]]],
    analysis_config
    ) -> Dict[str, np.ndarray]:
    """
    Build boolean masks for the 6 complex phases, writing the results into the
    exact keys provided in analysis_config['task_phase_names'] (case-insensitive matching).
    analysis_config needs:
      - 'task_phase_names': list/tuple of 6 names (any capitalization)
      - 'early_criteria_value': int
    """
    # set parameters
    stage_names = analysis_config.task_phase_names
    earlyN = analysis_config.early_criteria_value
    ##
    in_RS, is_error = get_inRS_isError(input_labels)
    idx = np.arange(len(in_RS), dtype=int)
    T = len(idx)
    #check error inputs
    assert (~in_RS).any() and in_RS.any(), "Need at least one IA and one RS trial"
    assert analysis_config.early_criteria_value >= 1, "early_criteria_value must be >= 1"

    canon = _canonical_keys(stage_names)  # lower -> original key

    ia_pos = np.where(~in_RS)[0]
    rs_pos = np.where(in_RS)[0]
    assert ia_pos.size > 0 and rs_pos.size > 0, "Must contain IA and RS trials"

    first_RS = rs_pos[0]
    last_IA = ia_pos[ia_pos <= first_RS][-1]
    last_RS = rs_pos[-1]

    early_IA_end = ia_pos[min(earlyN, ia_pos.size) - 1]
    early_RS_end = rs_pos[min(earlyN, rs_pos.size) - 1]

    in_early_IA = idx <= early_IA_end
    in_early_RS = in_RS & (idx <= early_RS_end)

    out = {name: np.zeros(T, dtype=bool) for name in stage_names}

    # Early IA error with fallback
    ia_err_early = is_error & (~in_RS) & in_early_IA
    if ia_err_early.any():
        out[canon["early_ia_error"]] = ia_err_early
    else:
        ia_err_idx = np.where(is_error & (~in_RS))[0]
        if ia_err_idx.size > 0:
            pick = ia_err_idx[:min(ia_err_idx.size, earlyN)]
            mask = np.zeros(T, dtype=bool)
            mask[pick] = True
            out[canon["early_ia_error"]] = mask

    # Early IA correct
    out[canon["early_ia_correct"]] = (~is_error) & (~in_RS) & in_early_IA

    # Late IA, not errors
    late_ia_start = last_IA - earlyN + 1
    late_ia_idx = np.arange(late_ia_start, last_IA + 1, dtype=int)
    mask_late_ia = np.zeros(T, dtype=bool)
    mask_late_ia[late_ia_idx] = True
    out[canon["late_ia"]] = mask_late_ia & (~is_error)

    # Early RS error with fallback
    rs_err_early = is_error & in_RS & in_early_RS
    if rs_err_early.any():
        out[canon["early_rs_error"]] = rs_err_early
    else:
        rs_err_idx = np.where(is_error & in_RS)[0]
        if rs_err_idx.size > 0:
            pick = rs_err_idx[:min(rs_err_idx.size, earlyN)]
            mask = np.zeros(T, dtype=bool)
            mask[pick] = True
            out[canon["early_rs_error"]] = mask

    # Early RS correct
    out[canon["early_rs_correct"]] = (~is_error) & in_RS & in_early_RS

    # Late RS, not errors
    late_rs_start = last_RS - earlyN + 1
    late_rs_idx = np.arange(late_rs_start, last_RS + 1, dtype=int)
    assert len(late_rs_idx) == earlyN
    mask_late_rs = np.zeros(T, dtype=bool)
    mask_late_rs[late_rs_idx] = True
    out[canon["late_rs"]] = mask_late_rs & (~is_error)

    # Reference indices
    out["_last_IA_index"] = int(last_IA)
    out["_last_RS_index"] = int(last_RS)
    out["_early_IA_end_index"] = int(early_IA_end)
    out["_early_RS_end_index"] = int(early_RS_end)
    return out

#SUBFUNCTIONS for build phase masks
def _coerce_labels(input_labels: Union[
    Dict[str, Sequence[bool]], Tuple[Sequence[bool], Sequence[bool]]
    ]) -> Tuple[np.ndarray, np.ndarray]:
    """Accept dict {'in_RS','is_error'} or tuple (in_RS,is_error)."""
    if isinstance(input_labels, dict):
        in_RS = np.asarray(input_labels["in_RS"], dtype=bool)
        is_error = np.asarray(input_labels["is_error"], dtype=bool)
    else:
        in_RS = np.asarray(input_labels[0], dtype=bool)
        is_error = np.asarray(input_labels[1], dtype=bool)
    assert in_RS.shape == is_error.shape and in_RS.ndim == 1
    return in_RS, is_error

##HELPER FUNCTIONS for phase mask building
def get_inRS_isError(input_labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Python translation of the MATLAB function:        function [in_RS, is_error] = get_inRS_isError(input_labels)
    Inputs:
    input_labels : np.ndarray
        Vector of behavioral labels per frame.
    -
    Outputs:
    in_RS : np.ndarray. Boolean array, True if trial i is an RS trial.
    is_error : np.ndarray. Boolean array, True if trial i is an error trial.
    """
    # Call your existing function (must return 1D arrays)
    trial_num_at_frame, _, num_trials = return_trial_num_at_frame(input_labels)

    in_RS = np.zeros(num_trials, dtype=bool)
    is_error = np.zeros(num_trials, dtype=bool)

    for i in range(1, num_trials + 1):
        trial_mask = trial_num_at_frame == i
        trial_vals = input_labels[trial_mask]

        # Equivalent to: sum(unique(...) > 8) > 1
        in_RS[i - 1] = np.sum(np.unique(trial_vals) > 8) > 1

        # Equivalent to: sum(ismember([6, 13], ...)) > 0
        is_error[i - 1] = np.isin(trial_vals, [6, 13]).any()

    return in_RS, is_error

## helper function- get_trial_stage_map
def get_trial_stage_map(stage_dict, stage_names, num_trials):
    stage_in_trial = np.zeros((1, num_trials), dtype=object)
    trial_range = np.arange(num_trials)
    for s in stage_names:
        stage_in_trial[0,stage_dict[s]] = s# use stage bool to fill array with stage name where true

    trial_stage_map = {i+1:value for i,value in enumerate(stage_in_trial.squeeze())} #hashmap for trial's stage
    return trial_stage_map

## helper function- _canonical_keys just in case of string mismatch
def _canonical_keys(stage_names):
    # Map lowercase -> original key from your config
    canon = {name.lower(): name for name in stage_names}
    required = [
        "early_ia_error","early_ia_correct","late_ia",
        "early_rs_error","early_rs_correct","late_rs"
    ]
    missing = [r for r in required if r not in canon]
    if missing:
        raise KeyError(f"analysis_config.task_phase_names missing keys (case-insensitive): {missing}")
    return canon