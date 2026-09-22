classdef phase_index < index_vector
    %adapted from find_index_erroCorrect_trials_earlyIARS, turnt into a class
    %subclass of index_vector (which is IA,RS dependent) %9/23 by CarlosJohnson-Cruz
    properties
        IA_trials = [];
        RS_trials = []; % #sample labels as properties % IA Correct, RS Correct
        IA_error = []
        RS_error = [];
        IA_correct = [];
        RS_correct = [];
        %complex label properties
        trials_index_vector = [];
        last_IA_trials = [];
        last_RS_trial = [];
        early_RS_errors_exist = []; %store boolean for whether there existed error trials or not in early IA/ RS
        early_IA_errors_exist = [];

        phase_type = []; %will set the type of phase to use
        phase_vec = struct(); %stores old early section info, etc
        frame_by_stage = struct(); %store frames of each stage for reference
    end
    methods
        %% INIT %%
        function index_obj = phase_index(input_labels, phase_schema_to_use) %input is just raw labels
            %input arguments- input_labels == vector of behavior at frame
            % - phase_schema_to_use is string, either "simple" or
            % "complex", added 12/20/23, now to allow for simple or complex
            % phase schema

            %constructor function
            index_obj@index_vector(input_labels); %returns [index_obj.in_RS, index_obj.is_error] built in
            for n = 1:analysis_config.num_phases
                index_obj.phase_vec.(analysis_config.task_phase_names(n)) = [];
            end
            if nargin > 0
                %first add in info about IA Error/Correct, RS Error/Correct
                index_obj = return_simple_phase_index(index_obj);
                %one way to make phase indexes (uses %early.late divisions)
                if phase_schema_to_use == analysis_config.phase_division_types(2) %if this == the complex naming scheme, then add additional phase info
                    index_obj = return_phase_index_count(index_obj); %perform phase index count on input labels
                elseif phase_schema_to_use== "keep_late_error"
                    index_obj = return_phase_index_count(index_obj); %perform phase index count on input labels
                    %then, overwrite late sections with newly determined
                     index_obj.phase_vec.(analysis_config.task_phase_names(3)) = late_IA_trial_logical & ~IsError_bool_vec;

                end
                index_obj.phase_type = phase_schema_to_use;
            end
        end
        %% major functions

        %% simple phase label
        function index_obj = return_simple_phase_index(index_obj)
            %TO- divide only into IA Error, IA Correct, RS Correct, RS %Error
            %% get information on binary feature vectors for IA and RS trials, + IA error + RS error
            inRS = index_obj.in_RS;
            IsError = index_obj.is_error;
            index_obj.trials_index_vector = 1:length(inRS);
            index_obj.IA_trials = index_obj.trials_index_vector(~inRS);
            index_obj.RS_trials = index_obj.trials_index_vector(inRS);
            %IA Error, RS Error
            index_obj.IA_error = index_obj.trials_index_vector(IsError&~inRS); %find list of Ia error trials, this is a numeric range
            index_obj.RS_error = index_obj.trials_index_vector(IsError&inRS);
            % IA Correct, RS Correct
            index_obj.IA_correct = index_obj.trials_index_vector(~IsError&~inRS); %find list of Ia Correct trials, this is a numeric range
            index_obj.RS_correct = index_obj.trials_index_vector(~IsError&inRS);
            %match value names to current phase names            %iterate through simple phases name
            simple_IA_error_loc = contains(analysis_config.simple_phase_names,'IA',IgnoreCase=true) & contains(analysis_config.simple_phase_names,'error',IgnoreCase=true);
            simple_IA_correct_loc = contains(analysis_config.simple_phase_names,'IA',IgnoreCase=true) & ~contains(analysis_config.simple_phase_names,'error',IgnoreCase=true);
            simple_RS_error_loc = contains(analysis_config.simple_phase_names,'RS',IgnoreCase=true) & contains(analysis_config.simple_phase_names,'error',IgnoreCase=true);
            simple_RS_correct_loc = contains(analysis_config.simple_phase_names,'RS',IgnoreCase=true) & ~contains(analysis_config.simple_phase_names,'error',IgnoreCase=true);
            
            index_obj.phase_vec.(analysis_config.simple_phase_names(simple_IA_error_loc))=        index_obj.IA_error;
            index_obj.phase_vec.(analysis_config.simple_phase_names(simple_IA_correct_loc))=        index_obj.IA_correct;
            index_obj.phase_vec.(analysis_config.simple_phase_names(simple_RS_error_loc))=        index_obj.RS_error;
            index_obj.phase_vec.(analysis_config.simple_phase_names(simple_RS_correct_loc))=        index_obj.RS_correct;

        end

        %% return phase index (early/Late IA/RS breakdown)
        %TO: find the index of error/correct trials for IA and RS, for early and %late (not broken into corr/incorr)
        function index_obj = return_phase_index_count(index_obj)
            % first N/ 5 / last 5 trials
            % and if the mouse doesn't make any errors during the first 5 trials then use the first 1 or 2 errors in that task phase
            % even if they are outside this first 5 window
            %% declare structures
            inRS_bool_vec = index_obj.in_RS;
            IsError_bool_vec = index_obj.is_error;
            %% get information on binary feature vectors for IA and RS trials, + IA error + RS error
            %imported from simple phase function
            %% get information on early and late start and end points for IA
            early_IA_end= struct(); 
            early_RS_end = struct();

            [early_IA_end.index, early_RS_end.index ] = deal(analysis_config.early_criteria_value); %deal assigns same value to both
            early_IA_end.trial = index_obj.IA_trials(early_IA_end.index);
            early_RS_end.trial = index_obj.RS_trials(early_RS_end.index);

            trial_is_in_early_IA = index_obj.trials_index_vector<=early_IA_end.trial; %boolean
            trial_is_in_early_RS = inRS_bool_vec & (index_obj.trials_index_vector<=early_RS_end.trial); %trial is NOT in IA, and IS before early RS END

            index_obj.last_IA_trials = find(inRS_bool_vec,1, 'first')-1; %find 1st element in IS RS bool, then go 1 index previous to get last IA trual # 
            index_obj.last_RS_trial = find(inRS_bool_vec,1,'last');
            %% parse trials into early IA error
            
            trial_is_error_notRS_inEarlyIA = IsError_bool_vec&~inRS_bool_vec&trial_is_in_early_IA; %find if > 0 trials  are 1) error trial, 2) not in RS, 3) in early IA 
            trial_isError_notRS = IsError_bool_vec&~inRS_bool_vec; %trials that 1) = error, 2) NOT in RS
            index_obj.early_IA_errors_exist= sum(trial_is_error_notRS_inEarlyIA ) > 0;

            %if NO IA errors exist at all- set blank as default to not need % another else statement
            index_obj.phase_vec.(analysis_config.task_phase_names(1)) = []; %no IA errors exist at all

            if index_obj.early_IA_errors_exist %if >0 trial == is Error, is IA, and is Early
                index_obj.phase_vec.(analysis_config.task_phase_names(1)) = trial_is_error_notRS_inEarlyIA ;% EARLY IA ERROR

            elseif sum(trial_isError_notRS) >0 %if any just IA ERROR trials exist at ALL & if no trials are ERROR and IA and IN EARLY, then
                n_IA_errors_to_use = min([sum(trial_isError_notRS), analysis_config.early_criteria_value]); %determine if analysis_config.early_criteria_value, or the # of errors present is longer
                
                %create IA error logical vector for indexing
                IA_errors_indices_to_use = index_obj.IA_error(1:n_IA_errors_to_use); % list of error trials trials to use/set as true in the boolean
                IA_early_error_bool = false(1, length(inRS_bool_vec));
                IA_early_error_bool(IA_errors_indices_to_use) = logical(true); %set the specific error indices to useto == true
                index_obj.phase_vec.(analysis_config.task_phase_names(1)) = IA_early_error_bool;
            end
            %% parse trials into early IA correct 
            
            trial_is_notError_notRS_inEarlyIA = ~IsError_bool_vec&~inRS_bool_vec&trial_is_in_early_IA; %EARLY IA CORRECT ==  NOT error, NOT inRS and IS before ealry IA ends
            index_obj.phase_vec.(analysis_config.task_phase_names(2)) = trial_is_notError_notRS_inEarlyIA;
            %% create late_N object
            late_N_index_obj = struct(); %used for storing values 
            %% parse trials into Late IA
            %get trial # that is ~5 triasl before the last IA trial
            late_IA_start = index_obj.last_IA_trials-analysis_config.early_criteria_value+ 1; %add the +1, to make the range contain 5 trials, not 6 
            last_N_index_obj.IA_trials = late_IA_start:index_obj.last_IA_trials; % range of the actual trial values that == late IAe.g. 10,11,13,14
            
            %create a boolean for using as logical indexing later
            late_IA_trial_logical =false(1, length(inRS_bool_vec));
            late_IA_trial_logical(last_N_index_obj.IA_trials) = logical(true);
            %take the logical index and store it %LATE ia = intersection of NOT RS and POST earlyIA
            index_obj.phase_vec.(analysis_config.task_phase_names(3)) = late_IA_trial_logical & ~IsError_bool_vec;

            %% parse trials into early RS error
            trial_isError_isRS_inEarlyRS = IsError_bool_vec & inRS_bool_vec & trial_is_in_early_RS;
            trial_isError_isRS = IsError_bool_vec&inRS_bool_vec;
            %check bools
            index_obj.early_RS_errors_exist = sum(trial_isError_isRS_inEarlyRS ) > 0;
            index_obj.phase_vec.(analysis_config.task_phase_names(4))= []; %no RS errors exist, set blank as default to not need
            % another else statement

            if index_obj.early_RS_errors_exist  %else if >1 trial == is Error, is RS, and is Early
                index_obj.phase_vec.(analysis_config.task_phase_names(4))= trial_isError_isRS_inEarlyRS; %EARLY RS ERROR

            elseif sum(trial_isError_isRS )> 0 %if RS errors exist at all, if no trial == is error, is RS and is Early

                n_trials_to_use = min([sum(trial_isError_isRS), analysis_config.early_criteria_value]);
                RS_errors_indices_to_use = index_obj.RS_error(1:n_trials_to_use ); % list of error trials indices to use/set as true in the boolean
                RS_early_error_trials_logical = false(1, length(inRS_bool_vec));
                RS_early_error_trials_logical(RS_errors_indices_to_use ) = logical(true); %set the specific error indices to useto == true
                index_obj.phase_vec.(analysis_config.task_phase_names(4))= RS_early_error_trials_logical;
            end
            %% parse trials into early RS correct 
                %make bool vector
            trial_notError_isRS_isEarlyRS = ~IsError_bool_vec&inRS_bool_vec&trial_is_in_early_RS;
                %use bool vector
            index_obj.phase_vec.(analysis_config.task_phase_names(5))=trial_notError_isRS_isEarlyRS ; % EARLY RS CORRECT
            
            %% parse late RS trials %LATE RS = intersection of is RS and POST ea
           
            late_RS_start = index_obj.last_RS_trial-analysis_config.early_criteria_value+ 1; %add the +1, otherwise the range of late IA will include (analysis_config.analysis_config.early_criteria_value+ 1) than
            last_N_index_obj.RS_trials = late_RS_start :index_obj.last_RS_trial; % range of the actual trial values that == late IAe.g. 10,11,13,14
            assert(length(last_N_index_obj.RS_trials) == analysis_config.early_criteria_value, "error- mismatch between len of last N RS trials and early criteria value chosen ")
            %create a boolean for using as logical indexing later
            late_RS_boolean =false(1, length(inRS_bool_vec));
            late_RS_boolean(last_N_index_obj.RS_trials) = true;
            %take the logical index and store it
            index_obj.phase_vec.(analysis_config.task_phase_names(6)) =late_RS_boolean& ~IsError_bool_vec;  %inRS&[index_obj.trials_index_vector>[length(inRS) - early_RS_end.index]]; %LATE RS
        end
        %%
        %% %FUNCTION STORAGE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        %% return all strings for labels
        function [task_phase_trial_vec, IA_RS_trial_vec, corr_error_trial_vec]= return_trial_feature_vecs(divisions_index)
            %% To- return 3 string vectors where element i = corresponding feature value for vector
            %notate correct/incorrect as string by trial
            corr_error_trial_vec  = return_correct_error_string_vector(divisions_index);
            %note IA/RS rule genreral statment
            IA_RS_trial_vec =return_IA_RS_string_vector(divisions_index); %notate IA/RS as string by trial element
            %note task Phase
            if analysis_config.phase_is_solo_vector%do not need to fill in mid periods if using single vector analysis
                task_phase_trial_vec = return_task_phase_name_vector(divisions_index);
            else %else if using multiple trial comparisons, need to retain information on mid rule tials (that aren't in individual task phases pre-defined)
                task_phase_trial_vec = return_task_phase_name_vector_gaps_filled(divisions_index);
            end
        end

        %% return string vector methods

        function correct_error_trial_vec  = return_correct_error_string_vector(index_obj)
            correct_error_trial_vec = repmat("Error", length(index_obj.is_error),1); %correct_error_trialwise_vector(IsError) = "Error";
            correct_error_trial_vec(~index_obj.is_error) = "Correct";
        end

        function IA_RS_trialwise_vector =return_IA_RS_string_vector(index_obj)
            %TO- given a scalar # of trials, and a logical vector where entry T = 1
            %when trial T is a RS trial, return a string vector where each trial is %labeled IA or RS
            IA_RS_trialwise_vector = strings(length(index_obj.in_RS),1);
            IA_RS_trialwise_vector (index_obj.in_RS) = "RS";
            IA_RS_trialwise_vector (~index_obj.in_RS) = "IA";
        end

        function task_phase_trial_vec = return_task_phase_name_vector(index_obj)
            %To- return a string array vector where ent yi = the task phase currently in effect at trial i for early/late cutup
            num_trials = length(index_obj.in_RS); %sample number just to test
            task_phase_trial_vec = strings(num_trials,1);%first-make trial type vec of empty strings
            switch index_obj.phase_type
                case "simple" %4 version phase addition
                    for t = 1:length(analysis_config.simple_phase_names)
                        section_logical_trials = index_obj.phase_vec.(analysis_config.simple_phase_names(t))';
                        % index into empty vector for each type of trial,
                        task_phase_trial_vec(section_logical_trials)= analysis_config.simple_phase_names(t);
                        % where their processed condition logical vector replaces the strings at that position
                    end
                case "complex" %6 version phase addition
                    for t = 1:analysis_config.num_phases
                        section_logical_trials = index_obj.phase_vec.(analysis_config.task_phase_names(t))';
                        % index into empty vector for each type of trial,
                        task_phase_trial_vec(section_logical_trials)= analysis_config.task_phase_names(t);
                        % where their processed condition logical vector replaces the strings at that position
                    end
            end
        end

        function mid_fill_task_phase_vec = return_task_phase_name_vector_gaps_filled(index_obj)
            %TO- return a vector with phases marked, and GAPS filled in
            %with statements indicating mid
            % if entry is still empty, fill in with Rule name- correct stat
            task_phase_trial_vec = return_task_phase_name_vector(index_obj);
            corr_error_trial_vec = return_correct_error_string_vector(divisions_index);
            %note IA/RS rule genreral statment
            IA_RS_trial_vec =return_IA_RS_string_vector(divisions_index); %notate IA/RS as string by trial element
            %note task Phase
            mid_period_bool = task_phase_trial_vec==""; %is 1 when you aren't in earlyIA,etc
            mid_fill_task_phase_vec(mid_period_bool) = append(IA_RS_trial_vec(mid_period_bool), "_mid_", corr_error_trial_vec(mid_period_bool));
        end
        %% create label matrix from individual vectors
        function[feature_label_matrix] = make_feature_matrix_for_comparisons(divisions_index)
            % TO- create a MATRIX with features for each
            [task_phase_vec, IA_RS_vec, corr_err_vec]= return_trial_feature_vecs(divisions_index);
            if analysis_config.phase_is_solo_vector %given 2023 analysis creates 1 single vec per period, %just take cosine sim of vectors directly
                %if your'e doing solo vector analysis,%then downsample all of these vectors
                [unique_phases, phase_first_index, ~]= unique(task_phase_vec);
                phase_first_index= phase_first_index(~(unique_phases == ""));
                [task_phase_vec, IA_RS_vec, corr_err_vec]= deal(task_phase_vec(phase_first_index), IA_RS_vec(phase_first_index), corr_err_vec(phase_first_index) );
            else %do nothing, continue
            end
            % transpose % then append to create matrix of trial type names
            feature_label_matrix = struct(); %each field of this is a 2d matrix with the features stored
            %to allow for changing label names, use fuzzy logic
            error_field_name = analysis_config.feature_type_names(contains(analysis_config.feature_type_names , "err"));
            rule_field_name = analysis_config.feature_type_names(contains(analysis_config.feature_type_names , "IA"));
            phase_field_name = analysis_config.feature_type_names(contains(analysis_config.feature_type_names , "phase"));
            %create feature matrix entries % append function supports implicit expansion of arrays. combine strings from col vec and row vec to form a 2D string array.
            feature_label_matrix.(error_field_name) = append(corr_err_vec, "-", corr_err_vec');
            feature_label_matrix.(rule_field_name) = append(IA_RS_vec, "-", IA_RS_vec');
            feature_label_matrix.(phase_field_name) = append(task_phase_vec, "-", task_phase_vec');
        end% end function % old outputs: corr_err_trial_label_matrix ,IA_RS_trial_label_matrix,task_phase_trial_label_matrix
    end %end methods

end
%
% enumeration
% end
