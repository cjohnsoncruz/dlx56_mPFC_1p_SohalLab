function  rot_cells = return_shifted_array(array_to_shift, frames_to_get_array)
%% ''' TO- return a matrix where eacy row = row of array to shift, indexed by equivalent row of frames_to_get_array'''
%frames_to_get_array = (n_cells) x (n_frames_of_interest) matrix where each
%row = indices to get of matching row of array_to_shift
%% main

    rot_cells = zeros(size(frames_to_get_array));
        for n = 1:size(rot_cells,1)
            rot_cells(n,:) = array_to_shift(n, frames_to_get_array(n,:));
        end %end iter over columns
end %end function 