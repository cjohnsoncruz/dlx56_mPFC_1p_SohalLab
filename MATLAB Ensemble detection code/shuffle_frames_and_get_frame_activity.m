function shuffle_act  = shuffle_frames_and_get_frame_activity(matrix, frames_of_interest, n_shuf)
% TO- given a n_cell x n_frames matrix and a 1 x n_frames_of_interest vector,
% shuffle position of frames of interest vector, and get activity over N shuffles
%% set important frames
% n_shuf = 1000
[num_rows, num_cols] = size(matrix);

%create N_row x 1 vector, where elem = # of cols to rotate a given cell     %raster
shift_mat = randi(num_cols-1, [num_rows, n_shuf ]); %col S- shift for cell in shuffle S
%% shuffle data
shuffle_act = zeros(num_rows, n_shuf); %row = cell, col = shuffle N, elem = mean act of cell in shuffle N
for S = 1:n_shuf %for the S shuffles you need to do, (0.03s per shuffle)
    S;
    %given frames of activity of interest,

    shifted_idx = shift_frame_of_interest_index(frames_of_interest, shift_mat(:,S), num_cols);%get col S from shift mat, use for rotation
        %shifted index = row is indices for new random circularly shifted   %frames
    %get new matrix of cells in their new assigned indices
    rot_cells = return_shifted_array(matrix, shifted_idx); %return smaller mat where row = test_mat(shift_w_wrap)
   %rot cells = n_cells x n_frames (where frames have been moved already
    shuffle_act(:,S)  = mean(rot_cells,2); 
end
% mean_shuffle_act  = mean(shuffle_act,2);
%% optional print_time
% fprintf([" mean time of " + num2str(n_shuf) + " shuffles: " + num2str(mean(time_vec))])
% fprintf([" total time of " + num2str(n_shuf) + " shuffles: " + num2str(sum(time_vec))])
% figure; imagesc(shuffle_act); title('act by shuff'); colorbar
end