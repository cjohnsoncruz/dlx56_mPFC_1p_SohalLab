%%TO-
%store constant static properties used by multiple datasets
%%
classdef analysis_config

    properties(Constant)
        %names for various divisions
        trial_section_names = ["pre_outcome","post_outcome","ITI"];
        phase_division_types = ["simple", "complex"]; %if simple, you're only using 4 phases, if complex, you use 6

        task_phase_names = ["Early_IA_Error", "Early_IA_Correct", "Late_IA", "Early_RS_Error", "Early_RS_Correct", "Late_RS"];
        simple_phase_names = ["IA_Error", "IA_Correct", "RS_Error", "RS_Correct"]; %for 4 phase overlap
        % task_phase_names_w_conflict = ["Early_IA_Error", "Early_IA_Correct", "Late_IA", "Early_RS_Error_conflict","Early_RS_Error_nonconflict", "Early_RS_Correct", "Late_RS"];
        compare_baseline_names = strcat(analysis_config.task_phase_names, "_x_baseline");

        all_interphase_comparisons = nchoosek(analysis_config.task_phase_names, 2); %ignores self comparisons
        feature_type_names = ["correct_error", "IA_RS", "task_phase"]; %used to name feature matrix labels
        %lengths of various divisions
        num_sections = 3;%length(analysis_config.trial_section_names);
        num_phases = length(analysis_config.task_phase_names);
        % num_phases_conflict = length(analysis_config.task_phase_names_w_conflict);
        num_interphase_comparisons = length(analysis_config.all_interphase_comparisons);
        num_baseline_comparisons = length(analysis_config.compare_baseline_names);
        %this is called multiple times as shorthand for loops- should nest
        %this
        % options that can be set
        phase_is_solo_vector = true; %set to true if we are using a single, concatenated matrix to find activity > chance for each task period
        shuffle_to_use = "circle";
        num_shuffles = 1000;
        early_division_criteria_types = ["count", "first_2"];
        early_criteria_type = analysis_config.early_division_criteria_types(1) ; %use if you want to use the raw number of trials to define early or late IA
        early_criteria_value = 5;
        trial_section_divisions = [] ; %incorporate start/end of each trial
        
        %set label values that = start and stop of trial section names
        corr_vector_is_triangular = true;

        %parameters for processing steps
        seconds_before_post_to_keep = 5; %how many seconds before the post-decision should you keep?
        time_series_bin_size = 0.25; %this is in seconds (set to 1 to make it easily divisible given the sections are trimmed in increments of 1)
        corr_time_series_bin_size = 0.5; %to allow for more flexibility,decrease sparisty, extend the time series bin window for corrs
        percentile = 95; %think about how to set percentile- individually?
        threshold_with_shuffle = true;%set whether binarizing will occur
        min_baseline_len = 60*20*10

        %spike modulation parameters
        final_thresh= 2.5; %baseline is 3 % = multiple of variance of dF/F measured in least noisy 50% of frames, to call it an event
        final_thresh2= 12.5; %baseline is 15, = multiple of
        final_thresh3= 20; %baseline is 150
        final_thresh4_abs = 0.01;
        spike_decay_frac_of_peak_cutoff = 0.85;
        end_event_at_drop_frac_of_diff = true; %if you should judge a peak by it's increase from the min val loc in the spike, not the 0 val

        drop_low_value_peak_events = false;
        drop_low_act_cell_in_dataset_obj = false;
        low_act_thresh_in_obj_init = 0.005;
        cutoff_filter = 'bimodality'; %what kind of criteria for trimming excess events with
        peak_event_cutoff_percentile = 1; %what percentile fo events to drop below
        %troubleshooting for changing how you create section-phase pair        %names
        %should you make this determination calculated each time?
        %find where these variables are used, outisde of these calculations
        sec_phase_combos = [repmat(1:length(analysis_config.trial_section_names), 1, length(analysis_config.task_phase_names)); repelem(1:length(analysis_config.task_phase_names), length(analysis_config.trial_section_names))];
        all_section_phase_pair_names = [analysis_config.trial_section_names(analysis_config.sec_phase_combos(1,: ))', analysis_config.task_phase_names(analysis_config.sec_phase_combos(2,: ))' ];
        num_section_phase_pairs = length(analysis_config.all_section_phase_pair_names); %depends on what specific type of omcparisons you're doing
        simple_sec_phase_combos = [repmat(1:length(analysis_config.trial_section_names), 1, length(analysis_config.simple_phase_names)); repelem(1:length(analysis_config.simple_phase_names), length(analysis_config.trial_section_names))];
        simple_all_phase_pair_names = [analysis_config.trial_section_names(analysis_config.simple_sec_phase_combos(1,: ))', analysis_config.simple_phase_names(analysis_config.simple_sec_phase_combos(2,: ))' ];
        num_section_phase_pairs_simple =length(analysis_config.simple_all_phase_pair_names); %depends on what specific type of omcparisons you're doing
        
        % REVISION NEW OPTIONS: added march 2026
        use_dff_not_spikes = false;
        zscore_dff = false;
        zscore_dff_to_baseline = false;
        shuffle_rand_permute = true;
    end
    %%
    %% methods
    methods(Static)
        function [section_name, phase_name] = get_section_phase_pair_names(p, phase_type)
            %inputs- p is the # of the specific combo you want, and phase
            %type says if you're using a simple (4 phase) or complex (6 %phase) algo
            switch phase_type %check for what kind of analysis you're doing- simple phases or %complex phases
                case analysis_config.phase_division_types(1)
                    %WIP- define the names for simples
                    section_name = analysis_config.simple_all_phase_pair_names(p,1);
                    phase_name = analysis_config.simple_all_phase_pair_names(p,2);

                case analysis_config.phase_division_types(2)

                    section_name = analysis_config.all_section_phase_pair_names(p,1);
                    phase_name = analysis_config.all_section_phase_pair_names(p,2);
                otherwise
                    fprintf("ERROR-- forgot to specify phase type for returning the right section_phase pairs")
            end
        end

        %%
        function num_phase_pairs_curr = get_num_phase_pairs(phase_type)
            %to- tell you how many phase pairs exist in the regime you're operatingh in
            %(simple versus complex phase pairs)
            switch phase_type %check for what kind of analysis you're doing- simple phases or %complex phases
                case analysis_config.phase_division_types(1)
                    num_phase_pairs_curr = analysis_config.num_section_phase_pairs_simple;
                case analysis_config.phase_division_types(2)
                    num_phase_pairs_curr = analysis_config.num_section_phase_pairs;
                otherwise
                    num_phase_pairs_curr = [];
                    fprintf("ERROR-- forgot to specify phase type for returning the right nnum of section_phase pairs")
            end
        end
        % % need smiple, 1 line way to preallocate loop based on phase type in
        % % flexible manner
        % function section_phase_array = return_array_of_section_phase_pairs(phase_type)
        %     %to- return string array where each row is a specific section-phase string
        %     %array, and each col is either the section, or phase of that particular
        %     %combination. allows for pre-specified phase type
        % end
    end %end methods
    %%
end