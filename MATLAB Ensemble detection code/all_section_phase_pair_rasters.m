classdef all_section_phase_pair_rasters
    %TO- create an object containing phase rasters for ALL trial section/task
    %phase pair possible combinations
    properties
        base_sections = analysis_config.trial_section_names;
        base_phases = analysis_config.task_phase_names;
        sec_phase_pair_names = analysis_config.all_section_phase_pair_names;
        sec_phase_storage = struct(); %struct where (trial_section).(task_phase) for a given phase-task combo contains a phase_raster object
        num_cells = [];
        phase_type = "undefined";
    end

    methods
        %% INIT
        function sec_phase_pair_raster_obj = all_section_phase_pair_rasters(input_raster,input_labels, phase_obj) %constructor
            %%TO- create a object containing each task phase raster,
            %%broken down by what section it belongs to. Performs slicing
            %%and trimming methods automatically. Input must be a raw cell
            %%x frame activity raster + input label vector
            %get phase type from phase obj index
            phase_type = phase_obj.phase_type;
            if nargin >0
                [trim_raster_struct] =  vectorize_raster_methods.slice_trim_raster(input_raster, input_labels); %trims input
                %NEW- handle case of simple phases
                
                num_phase_pairs_curr = analysis_config.get_num_phase_pairs(phase_type);
                for p = 1:num_phase_pairs_curr                 % for p = 1:analysis_config.num_section_phase_pairs
                    [section, phase] = analysis_config.get_section_phase_pair_names(p, phase_type);
                    sec_phase_pair_raster_obj.sec_phase_storage.(section).(phase) = phase_raster(trim_raster_struct,phase_obj, section,phase); %store a phase object in each field name pair
                end
                sec_phase_pair_raster_obj.num_cells = size(input_raster,1);
                sec_phase_pair_raster_obj.phase_type= phase_type; %incorpotate phase type in INIT for storage
            end
        end %end constructor
        %% non constructor functions
        function thresholded_vectors = threshold_phase_vectors(sec_phase_pair_raster_obj, vector_type, threshold)
            %TO- get the specified vector (activity or corr vector), then threshold versus the supplied shuffle percentiles
            %input- 
            % threshold- struct with (trial_section) keys, with
            % (phase/stage) keys nested for each trial section. Contains
            % threhold 
            %sec_phase_pair_raster_obj- struct with above key setup.
            %% Main
            all_vecs = get_all_phase_vecs_general(sec_phase_pair_raster_obj, vector_type);
            %NEW- handle simple phase cases
            %NEW- handle case of simple phases
            num_phase_pairs_curr = analysis_config.get_num_phase_pairs(sec_phase_pair_raster_obj.phase_type);
            for p = 1:num_phase_pairs_curr                 % for p = 1:analysis_config.num_section_phase_pairs
                [section, phase] = analysis_config.get_section_phase_pair_names(p, sec_phase_pair_raster_obj.phase_type);
                %flag to detect empty input
                if isempty(all_vecs.(section).(phase)) || all(isnan(all_vecs.(section).(phase)), 'all')
                    %adding logic for vector version of corr matrix
                    %if current phae is empty, check on next section to get the size of what this period should be
                    [~, next_phase] = analysis_config.get_section_phase_pair_names(p+3,sec_phase_pair_raster_obj.phase_type);
                    thresholded_vectors.(section).(phase) = repmat(-99,size(all_vecs.(section).(next_phase),1),1);
                else
                    thresholded_vectors.(section).(phase) = double(all_vecs.(section).(phase) > threshold.(section).(phase)); %threshold by Nth %ile of shuffle datasets
                end
            end
        end

        function all_activity_vecs = get_all_phase_activity_vectors(sec_phase_pair_raster_obj)
            %to- given a all_section_phase_pair_raster object, produce
            %a struct containing the mean activity of each phase %raster_pair
            all_activity_vecs = struct(); %stores the activity vector output
            %NEW- handle case of simple phases
            num_phase_pairs_curr = analysis_config.get_num_phase_pairs(sec_phase_pair_raster_obj.phase_type);
            for p = 1:num_phase_pairs_curr                 % for p = 1:analysis_config.num_section_phase_pairs
                [section, phase] = analysis_config.get_section_phase_pair_names(p, sec_phase_pair_raster_obj.phase_type);
                all_activity_vecs.(section).(phase)  = create_activity_vector(sec_phase_pair_raster_obj.sec_phase_storage.(section).(phase)); %call for each permutation of the section_phase_pairs
            end
        end

        function all_corr_vecs = get_all_phase_corr_vectors(sec_phase_pair_raster_obj)
            %to- given a all_section_phase_pair_raster object, produce
            %a struct containing the mean activity of each phase %raster_pair
            all_corr_vecs = struct(); %stores the activity vector output
            %NEW- handle case of simple phases

            num_phase_pairs_curr = analysis_config.get_num_phase_pairs(sec_phase_pair_raster_obj.phase_type);
            for p = 1:num_phase_pairs_curr                 % for p = 1:analysis_config.num_section_phase_pairs
                [section, phase] = analysis_config.get_section_phase_pair_names(p, sec_phase_pair_raster_obj.phase_type);
                all_corr_vecs.(section).(phase)  = create_corr_vector(sec_phase_pair_raster_obj.sec_phase_storage.(section).(phase)); %call for each permutation of the section_phase_pairs
            end
        end

        function all_vecs = get_all_phase_vecs_general(sec_phase_pair_raster_obj, input_datatype)
            %TO- given a string input, return the type of vector corresponding to specified %string
            switch input_datatype
                case "activity"
                    all_vecs= get_all_phase_activity_vectors(sec_phase_pair_raster_obj); % output = struct with all activity vectors
                case "corr"% find corrs in current phase raster
                    %this creates a 1 x # of cell pairs combinations vector of %cell-cell corrs, as it has built in triangularization
                    all_vecs =  get_all_phase_corr_vectors(sec_phase_pair_raster_obj);
                case "corr_binned" %find corrs within multiple bins of current phae raster
                    %step 1- create binned raster
                case "activity_binned" %find activity within multiple bins of curren tphase raster

            end
        end
    end
end