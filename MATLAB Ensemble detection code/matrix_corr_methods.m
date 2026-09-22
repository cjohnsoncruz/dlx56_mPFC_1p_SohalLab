classdef matrix_corr_methods
    %To- find correlatiosn between rows of an input matrix
    properties
    end
    %% begin methods
    methods(Static)
        %% take upper triangle method
        function flattened_matrix =  zero_mat_identity_and_take_upper_tri(input_matrix)
            input_matrix(isnan(input_matrix)) = 0;
            flattened_matrix= input_matrix(triu(true(size(input_matrix)),1));          %turn rho_shuff into an upper triangle to exclude the identity
        end

        %% find cell-cell correlations in matrix
        function [matrix_corrs] = find_matrix_corrs(input_matrix, take_upper_triangle)
            % TO_ given a cell array, find the correlation within the cols of the permuted matrix within each cell, and optionally sparsify/take upper triangle
            assert(~isempty(full(input_matrix)), "error- Matrix is empty, cannot find corrs")
            matrix_corrs = corr(full(input_matrix)');
            if take_upper_triangle%delete the identity to avoid weird increase%turn rho_shuff into an upper triangle to exclude the identity
                matrix_corrs=  matrix_corr_methods.zero_mat_identity_and_take_upper_tri( matrix_corrs);
            end
            matrix_corrs(isnan(matrix_corrs))= 0;
        end %end function

        %% function- loop over individual cell entries to find correlations
        function [rho_shuff] = find_matrix_corr_in_cells(input_cell_array, take_upper_triangle)
            %TO_ given a cell array, find the correlation within the cols of the permuted matrix within each cell, and optionally sparsify/take upper triangle
            num_cells_in_array = numel(input_cell_array);
            rho_shuff = cell(1,num_cells_in_array); %store correlations
            % loop over each cell to find correlations within it
            for i=1:num_cells_in_array
                assert(~isempty(full(input_cell_array {i})), "error- cell #" + num2str(i) + " is empty, cannot find corrs")
                rho_shuff {i} = corr(full(input_cell_array {i})');
                if take_upper_triangle%delete the identity to avoid weird increase%turn rho_shuff into an upper triangle to exclude the identity
                    rho_shuff {i}=  matrix_corr_methods.zero_mat_identity_and_take_upper_tri( rho_shuff {i});
                end
                %final isnan-> 0 step just in case
                rho_shuff{i}(isnan(rho_shuff{i}))= 0;
            end %end cell array loop
        end %end function
        %% function- given 2 dissimilar matrices, compare vectors between each 
function output_similarity_matrix = create_cosineSimMatrix_2inputs(data, data_2, dimension)
numElements_d1 = size(data,dimension);
numElements_d2 = size(data_2, dimension);
output_similarity_matrix = zeros(numElements_d1, numElements_d2);
%rows are from matrix 1, columns are matrix 2 
for i=1:numElements_d1
    for j=1:numElements_d2
        output_similarity_matrix (i,j) = cosinesim(data(i,:), data_2(j,:)); %compares data vector I to data2 vector j
%         string_debug = strcat('comparing data 1 v ' ,num2str(i), 'and data 2 v', num2str(j));
         if isnan(output_similarity_matrix (i,j))
             output_similarity_matrix (i,j) = 0;
         end
%         output_similarity_matrix (j,i) =output_similarity_matrix (i,j);
    end
end
end


        %% function- full cosine sim matrix
        %% INPUT: dataset, dimension along which to find similarity
        function output_similarity_matrix = make_cosine_sim_matrix(data,dimension)
            numElements = size(data,dimension);
            output_similarity_matrix = zeros(numElements, numElements);
            for i=1:numElements
                for j=1:numElements
                    output_similarity_matrix (i,j) = cosinesim(data(i,:), data(j,:));
                    if isnan(output_similarity_matrix (i,j))
                        output_similarity_matrix (i,j) = 0;
                    end
                    output_similarity_matrix (j,i) =output_similarity_matrix (i,j);
                end
                output_similarity_matrix(i,i) = 1;
            end
        end
    end %end methods
end %end class definition