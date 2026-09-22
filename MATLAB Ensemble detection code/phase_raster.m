classdef phase_raster
    %object
    %to- hold the concatenated raster for a given task period phase
    properties
        raster{double} = [-1]
        section_name{string} = "no section"
        phase_name{string} = "no phase"
        num_cells{double} = [];
    end

    methods
        function phase_raster_obj = phase_raster(input_raster,phase_index, section,phase)
            %create a phase raster object, don't need to save input raster
            if nargin > 0
                phase_raster_obj.section_name= section;
                phase_raster_obj.phase_name= phase;
                phase_raster_obj.raster = vectorize_raster_methods.concat_task_period_frames(input_raster,phase_index, phase, section);
             phase_raster_obj.num_cells=  size(phase_raster_obj.raster,1);
            end %end init function
        end

        function activity_vector = create_activity_vector(phase_raster_obj)
                activity_vector = vectorize_raster_methods.get_activity_vector(phase_raster_obj.raster);
            end

        function corr_vector = create_corr_vector(phase_raster_obj)
            %this creates a 1 x # of cell pairs combinations vector of
            %cell-cell correlations, as it has built in triangularization
            corr_vector = vectorize_raster_methods.get_corr_vector(phase_raster_obj.raster);
            end

        % function %return percentile high
        % end
        % 
        % function %return percentile low
        % end

    end
end