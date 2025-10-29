# analysis_config_loader.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from itertools import combinations, product
import yaml

@dataclass
class AnalysisConfig:
    # Directly loaded fields
    trial_section_names: List[str]
    phase_division_types: List[str]
    task_phase_names: List[str]
    simple_phase_names: List[str]
    feature_type_names: List[str]

    phase_is_solo_vector: bool
    shuffle_to_use: str
    num_shuffles: int

    early_division_criteria_types: List[str]
    early_criteria_type: str
    early_criteria_value: int

    trial_section_divisions: List[Any]

    corr_vector_is_triangular: bool

    seconds_before_post_to_keep: int
    time_series_bin_size: float
    corr_time_series_bin_size: float
    percentile: float
    threshold_with_shuffle: bool
    min_baseline_len: int

    final_thresh: float
    final_thresh2: float
    final_thresh3: float
    final_thresh4_abs: float

    drop_low_value_peak_events: bool
    drop_low_act_cell_in_dataset_obj: bool
    low_act_thresh_in_obj_init: float
    cutoff_filter: str
    peak_event_cutoff_percentile: float

    use_dff_not_spikes: bool
    zscore_dff: bool
    zscore_dff_to_baseline: bool
    spike_decay_frac_of_peak_cutoff: float
    end_event_at_drop_frac_of_diff: bool

    # Derived fields
    compare_baseline_names: List[str] = field(init=False)
    all_interphase_comparisons: List[Tuple[str, str]] = field(init=False)
    num_sections: int = field(init=False)
    num_phases: int = field(init=False)
    num_interphase_comparisons: int = field(init=False)
    num_baseline_comparisons: int = field(init=False)

    sec_phase_combos: List[Tuple[int, int]] = field(init=False)
    all_section_phase_pair_names: List[Tuple[str, str]] = field(init=False)
    num_section_phase_pairs: int = field(init=False)

    simple_sec_phase_combos: List[Tuple[int, int]] = field(init=False)
    simple_all_phase_pair_names: List[Tuple[str, str]] = field(init=False)
    num_section_phase_pairs_simple: int = field(init=False)

    def __post_init__(self):
        self.compare_baseline_names = [f"{p}_x_baseline" for p in self.task_phase_names]
        self.all_interphase_comparisons = list(combinations(self.task_phase_names, 2))

        self.num_sections = len(self.trial_section_names)
        self.num_phases = len(self.task_phase_names)
        self.num_interphase_comparisons = len(self.all_interphase_comparisons)
        self.num_baseline_comparisons = len(self.compare_baseline_names)

        self.sec_phase_combos = list(product(range(self.num_sections), range(self.num_phases)))
        self.all_section_phase_pair_names = [
            (self.trial_section_names[i], self.task_phase_names[j]) for i, j in self.sec_phase_combos
        ]
        self.num_section_phase_pairs = len(self.all_section_phase_pair_names)

        simple_len = len(self.simple_phase_names)
        self.simple_sec_phase_combos = list(product(range(self.num_sections), range(simple_len)))
        self.simple_all_phase_pair_names = [
            (self.trial_section_names[i], self.simple_phase_names[j]) for i, j in self.simple_sec_phase_combos
        ]
        self.num_section_phase_pairs_simple = len(self.simple_all_phase_pair_names)

    def get_num_phase_pairs(self, phase_type: str) -> int:
        if phase_type == "simple":
            return self.num_section_phase_pairs_simple
        return self.num_section_phase_pairs

def load_analysis_config(path: str) -> AnalysisConfig:
    with open(path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = yaml.safe_load(f)
    return AnalysisConfig(**data)
