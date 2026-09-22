classdef vector_analysis_methods
    %for- storing functions to be used for comparing vectors across
    %ruleshifting defined task phase. Can be used for correlation vectors or activity vectors
    %% properties section
    properties
    end
    %% static methods
    methods(Static)
        %% MAIN METHODS- RETURN CORR VECTOR ACTIVE OVER CHANCE
        function [sig_corr_vec_table]= return_sig_corr_vec_by_phase_object(dataset_object, phase_type)
            %%TO- return a dataset's correlation vectors, binarized against chance, in a table
            fprintf(strcat(" Creating binary corr vector for dataset: ", dataset_object.name, "\n"))
            %%  define early IA correct, early IA error, early RS correct, early RS error with trial number and index
            phase_index_obj = phase_index(dataset_object.labels, phase_type); %extract criteria from options, creates new phase object
            all_phase_pair_rasters = all_section_phase_pair_rasters(dataset_object.raster,dataset_object.labels, phase_index_obj); %create object where sec_phase_storage contains each version of this
            %% create shuffles
            [shuffles_array, ~] = make_shuffle_methods.create_n_circ_shuffles(analysis_config.num_shuffles, dataset_object.raster); %10 seconds - 10 shuffles/40 shuffles, 40 seconds
            %% FIND CORRELATION MATRIX DURING task phase- consists of concatenated trial matrices then threshold phase vector
            metric_to_use = "corr";
            task_period_threshold =vector_analysis_methods.find_shuff_measure_thresh_by_period(metric_to_use, shuffles_array, dataset_object.labels, phase_index_obj); %create combined threshold object
            %for sections, thresholds will sometimes be nan
            thresholded_vectors = threshold_phase_vectors(all_phase_pair_rasters, metric_to_use, task_period_threshold); %phase pair specific method for thresholding versus supplied percentile
            %% convert concated task phases to table
            sig_corr_vec_table= vectorize_raster_methods.convert_section_phase_vecs_to_table_and_join(thresholded_vectors);
            %% BASELINE-  extract baseline correlation matrix vectors
            baseline_data = baseline_class(dataset_object.raster, dataset_object.labels); %return the properties of the dataset object to make baseline class object
            if baseline_data.is_usable % take baseline period of shuffles and % threshold baseline AVs by the shuffle percentiles
                if analysis_config.phase_is_solo_vector %why do I do this instead of AV style corrs? 5/16/23. Because you are evaluating the correlation between cells across the concat. task period (multiple trials combined, then cell-cell corr found)
                    shuff_baseline_corr_thresh = baseline_access_methods.get_shuffle_baseline_corr_vec_percentile(shuffles_array, dataset_object.labels);
                    sig_corr_vec_table  = [sig_corr_vec_table, table(baseline_data.correlation_vec > shuff_baseline_corr_thresh)]; %take Nth %ile of activity of concated baselines, no need to individualize %for the AVs
                end %end of thresholding
            else
                sig_corr_vec_table = table_methods.add_nan_col(sig_corr_vec_table,-99);
            end
            sig_corr_vec_table = renamevars(sig_corr_vec_table, "Var1", "baseline");
            sig_corr_vec_table.name = repmat(string(dataset_object.name), size(sig_corr_vec_table,1),1);
            sig_corr_vec_table.geno_day = repmat(string(dataset_object.geno_day), size(sig_corr_vec_table,1),1);
            sig_corr_vec_table.geno = repmat(string(dataset_object.geno), size(sig_corr_vec_table,1),1);
        end %% end function
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % MAIN METHODS- RETURN ACTIVITY VECTOR ACTIVE ABOVE CHANCE
        function sig_AV_table_join = return_activity_vector_sig_active_by_task_phase(dataset_object)
            % using dataset class for increased legibility, written 09/2023 by Carlos Johnson-Cruz
            % TO- return a table where each column = a task period, each row = a cell, %and each entry = 1 or 0 if that cell was sig. active > chance during that %task period
            % INPUTS- daataset object, phase_type 
            fprintf(strcat(" Creating binary activity vector for dataset: ", dataset_object.name, "\n"))
            % NEW- WIP drop events if below peak value
            if analysis_config.drop_low_value_peak_events 
            [new_spikes,kept_spiketimes,kept_cellIDs ] = drop_spike_if_has_low_peak_dff(dataset_object.raster, dataset_object.C(dataset_object.good_cells,:),analysis_config.peak_event_cutoff_percentile );
            else
                new_spikes = dataset_object.raster;
            end
             % NEW_ switch between dff vs spikes
           if analysis_config.use_dff_not_spikes
                if analysis_config.zscore_dff
                new_spikes = zscore(dataset_object.C, 0, 2);
                else 
                    new_spikes = dataset_object.C;
                end
            end
            % detect if baseline period exists
            baseline_data = baseline_class(new_spikes, dataset_object.labels); %return the properties of the dataset object to make baseline class object
            %  %define early IA correct, early IA error, early RS correct, early RS error with trial number and index
            phase_type = analysis_config.phase_division_types(2);
            phase_index_obj = phase_index(dataset_object.labels,  phase_type ); %extract criteria from options, creates new phase object
            all_phase_pair_rasters = all_section_phase_pair_rasters(new_spikes, dataset_object.labels, phase_index_obj); %create object where sec_phase_storage contains each version of this
            % new- 12/1/24- define what frames are used for what
            frame_by_stage = all_section_phase_pair_rasters(1:size(new_spikes,2), dataset_object.labels, phase_index_obj); %create object where sec_phase_storage contains each version of this
            % derived              % create shuffles- 1s per shuffle
            %% shuff 
            
            [shuffles_array, ~] = make_shuffle_methods.create_n_circ_shuffles(analysis_config.num_shuffles, new_spikes); %10 seconds - 10 shuffles/40 shuffles, 40 seconds
            
            % find, for each task period, what the shuffled version of activity would be, and threshold real data vs the percentile of that shuffle matrix
            metric_to_use = "activity"; %what metric to measure for the current cocnat pahse of the raster
            task_period_threshold =vector_analysis_methods.find_shuff_measure_thresh_by_period(metric_to_use, shuffles_array, dataset_object.labels, phase_index_obj); %create combined threshold object
            % NEW- 12/12/24- shuffle indices instead of frames, speedup time
            % iterate through sections            % iterate throuhg stages
            % num_phase_pairs_curr = analysis_config.get_num_phase_pairs(phase_type);
            % find-task period corrs loop over shuffles and split
            % all_shuff_vecs = struct(); phase_shuffle_metric = struct();
            % loop over shuffles
            % n_shuf = 200;
            % % 100 shuffles- ~100s to get all metrics
            %     % each shuffle contributes 1 vector to the array of shuffle activity or corr vectors
            %     tic
            %     for p = 1:num_phase_pairs_curr                 % for p = 1:analysis_config.num_section_phase_pairs
            %         p;
            %         [curr_section, curr_phase] = analysis_config.get_section_phase_pair_names(p, phase_type);
            %         shuffle mean act by stage
            %         all_phase_pair_rasters.sec_phase_storage.(curr_section).(curr_phase).raster;
            %         frames_of_interest = frame_by_stage.sec_phase_storage.(curr_section).(curr_phase).raster; %get the frames you care about for the current breakdown
            %         phase_shuffle_metric.(curr_section).(curr_phase) = prctile(shuffle_frames_and_get_frame_activity(dataset_object.raster, frames_of_interest, n_shuf), analysis_config.percentile,2); %is currently the AV that's returned
            %     end
            %     toc
            % 
            %     % finish combination logic                 %make sure this has longer than it is wide, to verify that the concat     %is correct
            %     if all(isnan(combined_period_vec), 'all') | isempty(combined_period_vec) %if section doesnt exits, don't create threshold
            %         phase_shuffle_metric.(curr_section).(curr_phase) = NaN;
            %     else %because corr vectors are now vectors, flattened, you can just take the mean across the axis where the z shuffles are stored
            %         assert(size(combined_period_vec,2) == analysis_config.num_shuffles, "error- combined vector num cols doesn't equal num shuffles")
            %         phase_shuffle_metric.(curr_section).(curr_phase) =prctile(combined_period_vec, analysis_config.percentile, 2);
            %     end
            
            % old way of thresholding vectors
            thresholded_vectors = threshold_phase_vectors(all_phase_pair_rasters, metric_to_use, task_period_threshold); %phase pair specific method for thresholding versus supplied percentile
            % convert concated task phases to table
            sig_AV_table_join = vectorize_raster_methods.convert_section_phase_vecs_to_table_and_join(thresholded_vectors);
            % extract baseline activity vectors
            if baseline_data.is_usable % take baseline period of shuffles
                shuff_baseline_percentiles = baseline_access_methods.get_shuffle_baseline_percentile(shuffles_array, dataset_object.labels);
                sig_AV_table_join = [sig_AV_table_join, table(baseline_data.mean_activity > shuff_baseline_percentiles)]; %take Nth %ile of activity of concated baselines, no need to individualize %for the AVs
            else
                sig_AV_table_join = table_methods.add_nan_col(sig_AV_table_join,-99);
            end
            sig_AV_table_join = renamevars(sig_AV_table_join, "Var1", "baseline");
            % add name col, % add geno_day col  % add geno col
            sig_AV_table_join.name = repmat(string(dataset_object.name), size(dataset_object.raster,1),1);
            sig_AV_table_join.geno_day = repmat(string(dataset_object.geno_day), size(dataset_object.raster,1),1);
            sig_AV_table_join.geno = repmat(string(dataset_object.geno), size(dataset_object.raster,1),1);
            sig_AV_table_join.neuron_ID = [1:size(dataset_object.raster,1)]';
            sig_AV_table_join.peak_dff_threshold_percentile = repelem(analysis_config.peak_event_cutoff_percentile,size(dataset_object.raster,1),1); %detail on the percentile cutoff used for excluding raster events
        end
        
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        %% MAIN METHODS- RETURN TABLE OF COSINE SIMILARITY OF ACTIVITY VECTORS, ACROSS TASK PHASES
        function [AV_with_labels_table, avs ]= find_sig_activity_cos_sim_intraphase(dataset_object, phase_type)
            %% TO: Given dataset object input, export table and struct detailing the cosine similarity between task phases
            %set phase type
            %% PREPROCESS
            sig_AV_table= return_ROI_sig_active_by_task_phase_using_dataset_class(dataset_object); %have table with mean activity vectors for each condition, binarized thresholded v shuffle
            baseline_data = baseline_class(dataset_object.raster, dataset_object.labels); %return the properties of the dataset object to make baseline class object
            divisions_index = phase_index(dataset_object.labels); %extract criteria from options, creates new phase object
            %% extract activity vecs from sig_AV_table
            avs = sig_AV_table; %figure how to rework this's use later on
            baseline_av = sig_AV_table.baseline;
            varNames = string(sig_AV_table.Properties.VariableNames); varNames = varNames(1:18); %gets rid of non variable cols
            %% % extract activity vectors for each
            vec_divide_phases = struct();
            num_phase_pairs_curr = analysis_config.get_num_phase_pairs(phase_type);
            for p = 1:num_phase_pairs_curr                 % for p = 1:analysis_config.num_section_phase_pairs
                [curr_section, curr_phase] = analysis_config.get_section_phase_pair_names(p,phase_type);
                vec_divide_phases.(curr_section).(curr_phase) = avs(:,varNames(p));
            end
            %% find cosine similarity between each section
            [AV_table_cos_sim_struct]= vector_analysis_methods.find_vector_interphase_cosine_sim(vec_divide_phases);
            %% Create linear table for all trial-trial similarities
            AV_table_full=  table_methods.unpack_sectioned_struct_to_table(AV_table_cos_sim_struct, dataset_object.name);
            if baseline_data.is_usable
                [baseline_table,~] =  vector_analysis_methods.find_period_vec_sim_to_baseline(vec_divide_phases,baseline_av);
                AV_table_full = join(AV_table_full, baseline_table, 'Keys', 'section'); % join unrolled tabular array with baseline array
            else %else add NaN for the baseline values just for storag epurposes
                for b = 1:length(analysis_config.compare_baseline_names) %loop over baseline comparisons
                    AV_table_full.(analysis_config.compare_baseline_names(b)) = NaN(size(AV_table_full,1),1);
                end
            end
            %% create linear matrix of ALL AV similarities
            [feature_label_matrix] = make_feature_matrix_for_comparisons(divisions_index); %method on phase index class, outputs struct with F fields, each field = matrix for feature labels
            linear_feature_labels = vector_analysis_methods.make_feature_label_matrix_linear(feature_label_matrix); %
            linear_feature_labels = vector_analysis_methods.pad_linear_feature_for_baseline(linear_feature_labels);
            linear_feature_table = struct2table(linear_feature_labels);
            % stack existing AV_table (converting from wide to long format)
            table_var_names = string(AV_table_full.Properties.VariableNames);
            section_name_cols = contains(table_var_names, ["section", "name"], 'IgnoreCase',true);
            numeric_cols = table_var_names(~section_name_cols);
            AV_with_labels_table = stack(AV_table_full, numeric_cols,'NewDataVariableName','cosine_sim', 'IndexVariableName','Phases_Compared');
            % add N columns containing feature vectors
            AV_with_labels_table = horzcat(AV_with_labels_table, repmat(linear_feature_table,3,1));
            %% SAVING OUTPUTS
            save(strcat(dataset_object.name,save_config.AV_phase_sim_analysis_struct_output_name_for_dataset), "AV_with_labels_table", 'avs', 'vec_divide_phases'); %also save what trials you used for what period
            AV_table_name = strcat(dataset_object.name,save_config.AV_phase_sim_analysis_csv_name_for_dataset);
            writetable(AV_with_labels_table, AV_table_name);
        end % end function

        %% begin sub functions
        function [phase_shuffle_metric] = find_shuff_measure_thresh_by_period(metric_to_use, shuffles_array, input_labels, phase_index_obj)
            %%TO- given input shuffle cell array, and labels, find the specific metric %%(either correlation array, or activity vecs array)
            %metric_to_use = string that's either "corr" or "activity", specifying what %metric to use to create the threshold matrix
            %% declare phase type
            phase_type = phase_index_obj.phase_type;
            num_phase_pairs_curr = analysis_config.get_num_phase_pairs(phase_type);

            %% find-task period corrs loop over shuffles and split
            all_shuff_vecs = struct(); phase_shuffle_metric = struct();
            %% loop over shuffles
            for z = 1:analysis_config.num_shuffles %loop over all shuffles
                sec_phase_pair_rasters = all_section_phase_pair_rasters(full(shuffles_array{z}),input_labels, phase_index_obj); %create object where sec_phase_storage contains each version of this
                %each shuffle contributes 1 vector to the array of shuffle activity or corr vectors
                curr_shuff_vecs = get_all_phase_vecs_general(sec_phase_pair_rasters, metric_to_use); %takes section-phase pair raster obejct + string input to generate the specified vector type
                for p = 1:num_phase_pairs_curr                 % for p = 1:analysis_config.num_section_phase_pairs
                    [curr_section, curr_phase] = analysis_config.get_section_phase_pair_names(p, phase_type);
                    all_shuff_vecs.(curr_section).(curr_phase){z} = curr_shuff_vecs.(curr_section).(curr_phase); %is currently the AV that's returned
                end  %end loop over trial section/task phase pairs
            end %end loop over shuffle
            %% Find cell-cell pair threshold- %take percentiles across 3rd dimension
            % THis shoudl occur after FINAL shuffle concludes. Find cell-cell pair threshold- %take percentiles across 3rd dimension
            num_phase_pairs_curr = analysis_config.get_num_phase_pairs(phase_type);
            for p = 1:num_phase_pairs_curr                 % for p = 1:analysis_config.num_section_phase_pairs
                [curr_section, curr_phase] = analysis_config.get_section_phase_pair_names(p, phase_type);
                combined_period_vec = cell2mat(all_shuff_vecs.(curr_section).(curr_phase));     %combine all the cell array entries
                %finish combination logic
                %make sure this has longer than it is wide, to verify that the concat     %is correct
                if all(isnan(combined_period_vec), 'all') | isempty(combined_period_vec) %if section doesnt exits, don't create threshold
                    [task_period_shuffle_metric_low.(curr_section).(curr_phase) , phase_shuffle_metric.(curr_section).(curr_phase)] = deal(NaN);
                else %because corr vectors are now vectors, flattened, you can just take the mean across the axis where the z shuffles are stored
                    %                     assert(size(combined_period_vec,1) > size(combined_period_vec,2), "Error: Cell2mat of period vector produced vec with dim 2 size > dim 1 size")
                    assert(size(combined_period_vec,2) == analysis_config.num_shuffles, "error- combined vector num cols doesn't equal num shuffles")
                    % P = prctile(A,p,dim) operates along the dimension dim. prctile(A,p,2) operates on the elements in each row.
                    phase_shuffle_metric.(curr_section).(curr_phase) =prctile(combined_period_vec, analysis_config.percentile, 2);
                    task_period_shuffle_metric_low.(curr_section).(curr_phase) = prctile(combined_period_vec, (100-analysis_config.percentile), 2);
                end
            end
        end %end function
        %%%%%%%%%%%
        %% compare trial phase types to baseline
        function [base_compare_table,base_compare_cos_sim] = find_period_vec_sim_to_baseline(vec_input_struct,baseline_av)
            base_compare_cos_sim = struct(); base_compare_table = struct();
            sections = analysis_config.trial_section_names;
            phases = analysis_config.task_phase_names;
            compare_baseline_names = analysis_config.compare_baseline_names; %import name from analysis config properties
            for s = 1:3%loop over all trial periods
                for n = 1:6 %loop over all task sections and make the comparison
                    phase_AVs = vec_input_struct.(sections(s)).(phases(n));
                    if all(isnan(phase_AVs{:,:}))
                        base_compare_table.(sections(s)).(compare_baseline_names(n)) =  NaN; %set equal to Nan if any vector doesn't exist, make sure this is a baseline comparison
                    else
                        if analysis_config.phase_is_solo_vector %then just take cosine sim of solo vectors
                            %baseline av is left alone because it's already
                            %a vector output from the table slice
                            %previously made
                            base_compare_table.(sections(s)).(compare_baseline_names(n)) = cosinesim(phase_AVs{:,:}, baseline_av);
                        else %else do it the old way
                            temp_matrix = create_cosineSimMatrix_2inputs(full(baseline_av.(sections(s)))', phase_AVs', 1); %remember to permute the inputs!
                            base_compare_cos_sim.(sections(s)).(compare_baseline_names(n)) = temp_matrix; %this holds the cosine sim. value of ALL comparisons of (task period trials) to baseline pseudo activity vectors
                            %to avoid inflation- remove the identity when taking the mean, and %take only upper triangle
                            base_compare_table.(sections(s)).(compare_baseline_names(n)) = mean(base_compare_cos_sim.(sections(s)).(compare_baseline_names(n)), 'all');
                        end %end is solo vector check
                    end %end if is nan check
                end %end loop over task phases
                base_compare_table.(sections(s)) = struct2table(base_compare_table.(sections(s)));
                base_compare_table.(sections(s)).section = string(sections(s));  %need to make this into a string otherwise the vert cat of talbve  doesn't work well due to it being char
            end %end loop over trial sections
            base_compare_table = [base_compare_table.(sections(1)); base_compare_table.(sections(2)); base_compare_table.(sections(3))];
        end %end function
        %% function- create cosine similarity matrix between trial phase types, excluding baseline
        function [Vec_cosine_sims_struct]=  find_vector_interphase_cosine_sim(vecs_sectioned)
            vec_cos_sim_matrix_record = struct(); %contains the cosine similarity matrices between each trial section
            Vec_cosine_sims_struct = struct(); %this will be how you store the AV data to turn it into a linear table
            comparison_names = analysis_config.all_interphase_comparisons;
            %% begin loop
            for s = 1:analysis_config.num_sections %iterate over sections
                curr_section = analysis_config.trial_section_names(s); %return current section
                for p = 1:analysis_config.num_interphase_comparisons  %contains all unique comparisons
                    combined_name(p) = strcat(comparison_names(p,1),"_x_", comparison_names(p,2));
                    AVset_1 =  vecs_sectioned.(curr_section).(comparison_names(p,1)); %first group of AV indexed by column 1
                    AVset_2 = vecs_sectioned.(curr_section).(comparison_names(p,2)); %first group of AV indexed by column 2
                    %handle if one vector doesn't exist

                    if all(isnan(AVset_1{:,:}))| all(isnan(AVset_2{:,:}))
                        Vec_cosine_sims_struct.(curr_section).(combined_name(p)) = NaN; %set equal to Nan if any vector doesn't exist
                    else
                        if analysis_config.phase_is_solo_vector %given 2023 analysis creates 1 single vec per period, %just take cosine sim of vectors directly
                            Vec_cosine_sims_struct.(curr_section).(combined_name(p)) = cosinesim(AVset_1{:,:}, AVset_2{:,:});
                        else
                            AV_set_temp_matrix = matrix_corr_methods.create_cosineSimMatrix_2inputs(AVset_1', AVset_2', 1); %remember to permute the inputs!
                            vec_cos_sim_matrix_record.(curr_section).(combined_name(p)).matrix = AV_set_temp_matrix;
                            vec_cos_sim_matrix_record.(curr_section).(combined_name(p)).mean=  mean(AV_set_temp_matrix, 'all');
                            Vec_cosine_sims_struct.(curr_section).(combined_name(p)) = mean(AV_set_temp_matrix, 'all');        %store this for later linear representation
                        end
                    end %end error handling for NaN input vectors
                end %end loop over task section pair combos
            end %end section loop
        end %end function
        %% function- feature functions
        %% function make feature matrix linear
        function linear_feature_labels = make_feature_label_matrix_linear(feature_label_matrix)
            %input- struct with multiple fields that = features predefined %in aanlssis_config
            % %to, given a string x strimg matrix where element i = trial i has string at element i describing a feature, make into a vector
            %get names of interest from input struct
            feature_label_names = string(fieldnames(feature_label_matrix));
            error_feature_name = feature_label_names (contains(feature_label_names  , "err"));
            rule_feature_name = feature_label_names (contains(feature_label_names, "IA"));
            phase_feature_name = feature_label_names (contains(feature_label_names  , "phase"));
            %make vector bool that linearizes the matrix
            linear_bool = triu(true(size(feature_label_matrix.(error_feature_name))));
            %index indivudal vectors
            linear_feature_labels = struct();
            linear_feature_labels.(error_feature_name) = feature_label_matrix.(error_feature_name)(linear_bool);
            linear_feature_labels.(rule_feature_name) = feature_label_matrix.(rule_feature_name)(linear_bool);
            linear_feature_labels.(phase_feature_name) = feature_label_matrix.(phase_feature_name)(linear_bool);
        end %end fcuntion
        %% function join feature table with cosine sim matrix
        function AV_with_labels_table = create_linear_table_of_all_AVs(activityVecs, corr_err_trial_label_matrix ,IA_RS_trial_label_matrix,task_phase_trial_label_matrix)
            %TO= take a trial x trial sized matrix of cosine similarities between %vectors, take the upper triangle of that matrix and append feature as %columns for a  linear table
            %% take inputs-
            % cosine sim matrix for trial section (pre/post/ITI)
            %label matrix for each trial type
            %% create logical mask of upper diagonal
            %because the cosine sim matrix is symmetrical, I take the values above the diagonal, and flatten those
            cosine_sim_matrix_field_names = {'pre_cosine_sim_matrix','post_cosine_sim_matrix','ITI_cosine_sim_matrix' };
            tri_upper_bool = triu(true(activityVecs.(cosine_sim_matrix_field_names{1})),1); %any matrix will do to chose the diag chosen
            % the unclusion of 1 makes the identity not be included
            %% make labels linear
            % matrix(:) %stacks the COLUMNS, so column 1, column 2 are ordered
            %use the upper diagonal (above the identity line
            for s = 1:analysis_config.num_sections
                AV_cos_sim_matrix = activityVecs.(cosine_sim_matrix_field_names{s});
                AVs_column = AV_cos_sim_matrix(tri_upper_bool); %is raw AV cosine sim
                IA_RS_trial_col = IA_RS_trial_label_matrix(tri_upper_bool); %labels trial 1 and 2 as either IA or RS
                corr_error_trial_col = corr_err_trial_label_matrix(tri_upper_bool); %labels error/corr between the two trials here (corr-error, corr-corr, etc)
                task_phase_trial_col = task_phase_trial_label_matrix(tri_upper_bool);
                section_name_col = repmat(analysis_config.trial_section_names(s), size(IA_RS_trial_col,1), 1); % string  = "pre"/post/ITI
                % combine AVs and labels into table
                temp_table{s} = table(AVs_column, IA_RS_trial_col, corr_error_trial_col, task_phase_trial_col, section_name_col);
                %optional zscore values to to baseline
            end %end section loop
            AV_with_labels_table  = vertcat(temp_table{:});
        end % end of function
        %% function - add empty string slots to pad for baseline length
        function linear_feature_labels = pad_linear_feature_for_baseline(linear_feature_labels)
            fields = string(fieldnames(linear_feature_labels));
            pad_length = analysis_config.num_interphase_comparisons+1:analysis_config.num_interphase_comparisons+analysis_config.num_baseline_comparisons;
            for f = 1:length(fields)
                linear_feature_labels.(fields(f))(pad_length) = "baseline"; %sets the values you need to make = empty
            end
        end %end function

    end %end methods section
end %end class def