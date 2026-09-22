%To- collect all shuffle methods that are useful, in one place (as static
%methods)
classdef make_shuffle_methods
    properties
    end
    methods(Static)
        function [shuffled_raster, shuff_offset] = circ_shuf(input_raster)
            %takes n neuron x t time  slice calcium data from raster and shifts each neuron by
            %random number x magnitude (in frames). output is shuffled data %sparsified raster
            %NAF 1/2018, update CJC 4/2023, put into static method 9/23
            %% shuffle settings
            len_to_shuffle = size(input_raster,2)-1; %magnitude of span you will be randonly moving within
                       %% shuffle implementations
            shuffled_raster= zeros(size(input_raster));
            % shift dataset forward by N frames
            % index_min =-len_to_shuffle+offset; index_max = % len_to_shuffle-offset;  % assert(index_min <= index_max, "Randi generator range start int %u is not <= end int %u ", index_min, index_max)
            shuff_offset = randi(len_to_shuffle, [size(input_raster,1),1]);  %return vector of ints up to magnitude offset, with rows
            for i = 1:size(input_raster,1)
                shuffled_raster(i,:) = circshift(input_raster(i,:),shuff_offset(i));
            end
            %% output raster
            shuffled_raster = sparse(shuffled_raster); %sparsify raster
        end %end circ_shuff method

        function [circ_shuffle_cell_array, shuff_offsets] = create_n_circ_shuffles(num_shuffles, input_raster)
            %original function- create_n_circ_shuffles
            %%TO- use NAF code circ shuffle to output a sparse circularly shuffled
            %%matrix, into a cell array, with each of the num_shuffles cells being a shuffle of the input_matrix
            %% declare vars
            circ_shuffle_cell_array= cell(1,num_shuffles);
            shuff_offsets= cell(1,num_shuffles);
            %% main body
            for z = 1:num_shuffles
                [circ_shuffle_cell_array{z}, shuff_offsets] = make_shuffle_methods.circ_shuf(input_raster);
            end %end shuff loop
        end%end function
%% finding percentile functions
function find_shuffle_percentile
end
%%

        function shuff_activity_vec_z = make_shuffle_phase_activity_vector()
            %to- given a set task phase and trial section, extract the
            %period of interest activity, and find mean activity (activity
            %vector)
            shuff_activity_vec_z = curr_phase_raster.create_activity_vector();

        end

        function make_shuffle_phase_corr_vector()
            %to- given a set task phase and trial section, extract the
            %period of interest activity, and find correlation vector over
            %period
        end
    end

end