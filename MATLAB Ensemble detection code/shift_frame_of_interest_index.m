function shifted_idx = shift_frame_of_interest_index(input_frames, shift_vec,num_cols)
%TO- given a vector of frames of interest, broadcast to create new shifted
%frames by row
%input frames- 1 x n_frames vector of raster frames to grab
%shift vec- n_cells x 1 vector of how many indx to move each cell's frames
% returns: shifted_idx- n_cells x n_frames where each row is uniquely
% shifted frames in cells' rasteer
%% main

offset_mat = input_frames + shift_vec;
remainder_shift = 1+ rem(offset_mat, num_cols); %get remainder of (stage_frames + shift value)/ total num of columns in dataset
overflow_shift = offset_mat > num_cols; %find elements that > # of cols in original dataframe
%if shift exceeds the N columns in dataset, wrap them around
shifted_idx = offset_mat;
shifted_idx (overflow_shift) = remainder_shift(overflow_shift);
shifted_idx = shifted_idx; %to avoid if it's exactly 0 
end %end function