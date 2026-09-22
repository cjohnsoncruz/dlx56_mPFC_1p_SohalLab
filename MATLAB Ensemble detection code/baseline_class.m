classdef baseline_class
    %to- store information for a baseline object
    properties
        is_usable{logical} = false; %set to true if 1) not empty and > baseline len
        length{double} = []; %length in frames
        mean_activity{double} = [];
        mean_correlation{double} = [];
        raster{double} = [];
        num_cells{double} = [];
       correlation_vec = [];
    end
    methods
        function baseline_obj = baseline_class(input_raster, input_labels) %constructor
            if nargin>0
                baseline_obj.raster = baseline_access_methods.extract_baseline_activity(input_raster, input_labels);
                baseline_obj.is_usable =~isempty(baseline_obj.raster) && (size(baseline_obj.raster, 2)> analysis_config.min_baseline_len); %set a flag to skip baseline if baseline_data =s too small
                baseline_obj.length = size(baseline_obj.raster,2); %length = num rows
                baseline_obj.mean_activity = mean(full(baseline_obj.raster),2);
                % baseline_obj.mean_correlation = corr(baseline_obj.raster');
                % baseline_obj.correlation_vec = matrix_corr_methods.zero_mat_identity_and_take_upper_tri(baseline_obj.mean_correlation); 
                baseline_obj.num_cells= size(input_raster,1);
            end
        end
        %% vectorize functions
        function sdev_vector = get_baseline_sdev_vec(baseline_obj)
             if ~isempty(baseline_obj.raster) %check if there's any raster input at all
                activity_vector = std(baseline_obj.raster');
            else
                activity_vector = NaN(baseline_obj.num_cells,1); %create a nan vector that is as long as num cells
            end
        end
        function activity_vector =  get_baseline_activity_vec(baseline_obj)
            if ~isempty(baseline_obj.raster) %check if there's any raster input at all
                activity_vector = vectorize_raster_methods.get_activity_vector(baseline_obj.raster);
            else
                activity_vector = NaN(baseline_obj.num_cells,1); %create a nan vector that is as long as num cells
            end
        end

        function corr_vector = get_baseline_corr_vec(baseline_obj)
            if ~isempty(phase_raster_obj.raster)
                corr_vector = vectorize_raster_methods.get_corr_vector(baseline_obj.raster);
            else
                corr_vector =  NaN(baseline_obj.num_cells,1); %create a nan vector that is as long as num cells
            end
        end
        %% end methods
    end
end