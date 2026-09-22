%%TO- store static methods for vectorizing (creating AV vectors, corr %%vectors, etc)
classdef vectorize_raster_methods
    methods(Static)
        function [trim_raster_struct] =  slice_trim_raster(input_raster, input_labels)
            %combines both types - slice then trim
            sliced_struct = vectorize_raster_methods.slice_raster_into_sections(input_raster, input_labels);
            trim_raster_struct = vectorize_raster_methods.trim_sliced_raster(sliced_struct);
        end
        %% function to get corr within N frame window 
        %% function to merely reshape raster
        function reshaped_raster = reshape_2D_raster_to_3D_bins(input_matrix, bin_size)
                n_tail_elements = rem(size(input_matrix,2), bin_size); %find out how many elements extend past an evenly divisible subset
                input_matrix_trunc = input_matrix(:,1:[size(input_matrix,2)-n_tail_elements]); %remove any tail elements that exist
                reshaped_raster = reshape(input_matrix_trunc, size(input_matrix_trunc,1), bin_size, []); %reshapes into NumNeurons X WindowSize X (automatically calculated number to match original )
        end
        %% function to downsample
        function final_downsample_raster = downsample_raster(raster, windowSize)
        % create new downsampled raster- specifying to use the num columns % to downsample rather than length (allows for cases where there % are more ROI than frames in element)
                num_tail_elements = rem(size(raster,2), windowSize); %find out how many elements extend past an evenly divisible subset
                raster = full(raster(:,1:[size(raster,2)-num_tail_elements])); %remove any tail elements that exist
                reshaped_raster = reshape(raster, size(raster,1), windowSize, []); %reshapes into NumNeurons X WindowSize X (automatically calculated number to match original )
                final_downsample_raster = squeeze(mean(reshaped_raster, 2));
        end

        function [trimmed_raster_cell_array] =  trim_raster_sec_in_cell_array(raster_cell_array, trim_length, trim_type)
            trimmed_raster_cell_array = cell(size(raster_cell_array)); %because the input array is a cell array, you can do this
            switch trim_type
                case 'none'
                    trimmed_raster_cell_array{t}= raster_cell_array{t};
                case 'end'
                    for t = 1:length(raster_cell_array)
                        window_to_keep = min(size(raster_cell_array{t}, 2), trim_length); %find the min between either the length of the existing raster and length to trim
                        trimmed_raster_cell_array{t}= raster_cell_array{t}(:, [1+size(raster_cell_array{t}, 2)-window_to_keep]:end);
                    end
                case 'start'
                    for t = 1:length(raster_cell_array)
                        window_to_keep = min(size(raster_cell_array{t}, 2), trim_length); %find the min between either the length of the existing raster and length to trim
                        trimmed_raster_cell_array{t}= raster_cell_array{t}(:, 1:window_to_keep); %if trimLength > the total raster, then you just keep the whole dataset
                    end
            end
        end
        %% to- get isRS, is Error
        function [in_RS, is_error] = get_inRS_isError(input_labels)
            [trial_num_at_frame, ~, num_trials] = vectorize_raster_methods.return_trial_num_at_frame(input_labels);% slice input raster into trial numbers
            %create logical vectors that == true when trial i is in inRS or IsError
            in_RS = false([1, num_trials]); is_error = false([1, num_trials]);
            for i = 1:num_trials  % create loop to squash range of values into each section

                in_RS(i) = sum(unique(input_labels(trial_num_at_frame == i)) > 8) > 1; %detect if the current trial is IA or RS by seeing if all vals above 8
                is_error(i) = sum(ismember([6, 13], input_labels(trial_num_at_frame == i))) >0; %check if i is incorrect trial
            end
        end
        %%

        %% TO: take 3 dittinc cell arrays each with a raster, and crop to either the start or end of that raster, dependent on a parameter
        function [trim_raster_struct] = trim_sliced_raster(sliced_struct)
            %% TO_ slice a predetermined amount starting either from the START or END of the dataset section
            %assuming the input is a struct with N fields, corresponding to analysis_config.trial_section_names
            param_multiple = 20; %if trim params in seconds, multiply the values by this to get the value in frames
            section_names = analysis_config.trial_section_names;
            trim_raster_struct.(section_names(1)) = vectorize_raster_methods.trim_raster_sec_in_cell_array(sliced_struct.(section_names(1)), param_multiple* trim_params.trial_len, trim_params.Pre);
            trim_raster_struct.(section_names(2)) = vectorize_raster_methods.trim_raster_sec_in_cell_array(sliced_struct.(section_names(2)), param_multiple*trim_params.trial_len, trim_params.Post);
            trim_raster_struct.(section_names(3)) = vectorize_raster_methods.trim_raster_sec_in_cell_array(sliced_struct.(section_names(3)), param_multiple* trim_params.ITI_len, trim_params.ITI);
        end
        %% slice raw raster function in struct
        function sliced_struct = slice_raster_into_sections(raster_to_slice, input_labels)
            %% TO- OUTPUT TRIAL SECTIONED into cells within a struct
            %% make cell arrays to store the values of trial of interest, labels, PCA raster, etc
            [trial_num_at_frame, ~, num_trials] = vectorize_raster_methods.return_trial_num_at_frame(input_labels);% slice input raster into trial numbers
            %create logical vectors that == true when trial i is in inRS or IsError
            [in_RS, ~] = vectorize_raster_methods.get_inRS_isError(input_labels);
            %create storage cell arrays
            labels_by_trial = cell(1, num_trials); raster_by_trial= cell(1, num_trials);
            sliced_struct = struct();
            for s = 1:length(analysis_config.trial_section_names)
                sliced_struct.(analysis_config.trial_section_names{s}) = cell(1, num_trials);
            end
            %% create storage struct, 1 cell element bin per trial's section
            for i = 1:num_trials  % create loop to squash range of values into each section
                labels_by_trial{i} = input_labels(trial_num_at_frame == i); %extract only the labels that are in the current trial
                raster_by_trial{i} = raster_to_slice(:, trial_num_at_frame == i);
                %check if trial I is RS, and/or error trial
                if in_RS(i) %extract pre
                    sliced_struct.(analysis_config.trial_section_names{1}){i}  = raster_by_trial{i}(:,(9 <= labels_by_trial{i}) & (labels_by_trial{i}<= 11)); %start to dig
                    sliced_struct.(analysis_config.trial_section_names{2}){i} = raster_by_trial{i}(:,(11 <= labels_by_trial{i}) & (labels_by_trial{i}<= 14)); %dig to end
                    sliced_struct.(analysis_config.trial_section_names{3}){i}= raster_by_trial{i}(:,(labels_by_trial{i} == 15)); %dig to end
                else
                    sliced_struct.(analysis_config.trial_section_names{1}){i} = raster_by_trial{i}(:, (2<= labels_by_trial{i}) & (labels_by_trial{i} <=4));
                    sliced_struct.(analysis_config.trial_section_names{2}){i}= raster_by_trial{i}(:, (4<= labels_by_trial{i}) & (labels_by_trial{i} <=7));
                    sliced_struct.(analysis_config.trial_section_names{3}){i} = raster_by_trial{i}(:, (labels_by_trial{i} == 8));
                end
            end
        end
        %% function- return_trial_num_at_frame
        function [trial_num_at_frame, trial_start_index, num_trials] = return_trial_num_at_frame(labels)
            %% find start frames in raster
            % calculate where each trial starts by finding delta between frame i and i + 1, and noting when its negative %(find better way, that accounts for bad trials coming AFTER good trials,
            trial_start_index = []; j = 1;
            % loop over all labels
            for i = 2:length(labels) %needs to start at 2, because check requires at value at i-1, which only exists if i > 1
                if ((labels(i-1) ~= 2 ) && (labels(i) == 2 )) || ((labels(i-1) ~= 9 ) && (labels(i) == 9 ))  %if entry i-1 = NOT 2, and entry i ==2
                    trial_start_index(j) = i;%trial starts at frame i
                    j = j+1;
                end
            end
            num_trials= length(trial_start_index);
            %now create 1 x Frame vector where each frame says what trial it's in, with %0 being no trial or error
            trial_num_at_frame = zeros(1, length(labels));
            for j = 1:num_trials-1
                trial_num_at_frame(trial_start_index(j):trial_start_index(j+1))  = j;
            end
            trial_num_at_frame(trial_start_index(num_trials):length(trial_num_at_frame)) = num_trials; %as there's no trial index at position j +1 for a vector of size j, fill in the end trial name manually
        end
        function    current_phase_raster = concat_task_period_frames(original_raster, phase_index, phase, section)
            %TO: given a early_divisons_index, and a raster cell array where each cell
            %= trial, extract the trials that are of the task phase of interest
            current_task_phase_trials_bool = phase_index.phase_vec.(phase); %changed to add .phase vec as using new class setup
            %use boolean to index into original raster
            current_phase_raster_cells = original_raster.(section)(current_task_phase_trials_bool); %take cells that are true for the boolean corresponding to the task section of interest
            current_phase_raster = cell2mat(current_phase_raster_cells); %combine all cells %full is just in case an error slips up
            current_phase_raster = full(current_phase_raster);
            %what does this return when the dataset is empty for the
            %current task phase? empty?
        end
        %% vector functions
        function activity_vector = get_activity_vector(input_raster)
            if isempty(input_raster)  ||  all(isnan(input_raster), 'all') %check if there's any raster input at all
                activity_vector = NaN(size(input_raster,1),1); %create a nan vector that is as long as num cells
            else
                activity_vector = mean(input_raster,2);
            end
        end

        function corr_vector = get_corr_vector(input_raster)
            if ~isempty(input_raster) && ~all(isnan(input_raster), 'all')
                corr_vector = matrix_corr_methods.find_matrix_corrs(input_raster, analysis_config.corr_vector_is_triangular); %true = take upper triangle, so extracts diagonal and linearizes
            else
                if isempty(input_raster) %then you have no size information?
                    corr_vector =  NaN(size(input_raster,1),1); %create a nan vector that is as long as num cells (if it's a single nan value, then will be a nan)
                end
                if isnan(input_raster)
                    corr_vector =  NaN(size(input_raster,1),1); %create a nan vector that is as long as num cells
                end
            end
        end

        %% table conversion
        function single_sec_vec_table = convert_phase_vecs_to_table(single_section_vecs, input_section_name)
            single_sec_vec_table = struct2table(single_section_vecs); %, 'VariableNames', task_section_names(n));
            %rename variable names to let it be concated horzontally
            single_sec_vec_table.Properties.VariableNames = strcat(string(input_section_name), "_",single_sec_vec_table.Properties.VariableNames);
        end

        function Vec_table_stack = convert_section_phase_vecs_to_table_and_join(vectors)
            %TO- given 3 pre defined sections of the trial (pre.post/ITI) and N
            %defined task phases, iterate overa of them and stack them
            Vec_tables = cell(1,analysis_config.num_sections);
            for s = 1:analysis_config.num_sections %iterate over sections
                Vec_tables{s} = vectorize_raster_methods.convert_phase_vecs_to_table(vectors.(analysis_config.trial_section_names(s)),analysis_config.trial_section_names(s));
                % struct2table(); %, 'VariableNames', task_section_names(n));
                %rename variable names to let it be concated horzontally
            end
            Vec_table_stack = [Vec_tables{1}, Vec_tables{2},Vec_tables{3}];
        end
%% end methods 
    end 
end %end class 