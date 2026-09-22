% shuffle_randperm
%written 3.1.26 by CJC
%To- efficiently create random matrix of new frame indices. Used to slice into
%activity raster, to find mean activiyt of random slices of equal size to
%task stage
function rand_mat_mean = shuffle_randperm(raster, task_stage_len, n_shuffles)
    [n_cells, n_frames] = size(raster);
    rand_mat_mean = zeros(n_cells, n_shuffles);
    
    for s = 1:n_shuffles
        idx = randperm(n_frames, task_stage_len);  % T random frames, no replacement
        rand_mat_mean(:, s) = mean(raster(:, idx), 2);
    end
end

% %% set params
% n_total_frames = size(raster,2)
% stage_size = task_stage_len
% n_rows = n_shuffles
% %%  make random perm
% %question- do you want to do 1 Matrix per cell, or 1 matrix per shuffle. 
% rand_indices = randi(n_total_frames, stage_size, n_rows);
% % produces stage_size X n_shuffles matrix, with max = n_total frames
% new_mat = raster(rand_indices)
% %% find mean of new mat
% rand_mat_mean = mean(new_mat, 1);

