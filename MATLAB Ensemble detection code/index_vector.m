classdef index_vector
    % to store the Is RS and Is Error, and be a superclass for the phase_index calss 
    properties
    in_RS{logical} = [];
    is_error{logical} = [];
    end

    methods 
        function index_obj = index_vector(input_labels) %constructor
            if nargin > 0
                [index_obj.in_RS, index_obj.is_error] = vectorize_raster_methods.get_inRS_isError(input_labels);
            end

        end
    end
end