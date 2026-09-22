function [new_spikes,kept_spiketimes,kept_cellIDs ] = drop_spike_if_has_low_peak_dff(spikes,C,cutoff_percentile)
% TO- find what spikes are detected for a peak dff below a threshold, and% drop them
%% params
get_percentile_of_unique_peaks = false;
%% get dataset from input spike raster
[row, col] = find(spikes);
ncells = size(spikes,1);
window_size = 20; %how many frames before/after spike event to keep 
%% create storage
tic
cell_row_storage = cell(ncells,1);
spike_storage = cell(ncells,1);
spike_window_mat= cell(ncells,1); % each cell = 1 window for cell N, of frames +/- around point of itnerest 
cell_spike_frame_max_df = cell(ncells, 1);
% make trimmed outputs
trimmed_cell_IDs = cell(ncells,1);
trimmed_spikes = cell(ncells, 1);
%%iterate over cells
for n = 1:ncells
    cell_n_bool = row==n;
    cell_n_spike_frame = col(cell_n_bool); %list of spike frames valid in this set
    spike_windows = cell(length(cell_n_spike_frame), 1); %cell: (n spikes detected)
    %cell IDs for current cell
    cell_row_storage {n} = row(cell_n_bool) ; %store the list of row elements, for concat later to recreate the spike raster
    spike_storage {n} = cell_n_spike_frame ; %store the list of spikes per cell , for concat later to recreate the spike raster
    % spikes for current cell
    for f = 1:length(cell_n_spike_frame)
        spike_windows{f} = zeros(1, window_size*2+1);
        window_start = max([cell_n_spike_frame(f)-window_size,1]);
        window_end = min([cell_n_spike_frame(f)+window_size, size(C,2)]);
        spike_windows{f}(1:1+window_end-window_start) =  C(n, window_start: window_end);
    end
    spike_window_mat{n} = cell2mat(spike_windows); %concat together each cell's dff window vector
    cell_spike_frame_max_df{n} = max(spike_window_mat{n}, [], 2); %get max value in each col (col = spike max)
    %with list of each spike's peak dff in surrounding frames, find which    %are << mean
    % sdev= std(cell_spike_frame_max_df);    % peak_avg = mean(cell_spike_frame_max_df);% cutoff = peak_avg - cutoff_factor*sdev; % mean and sdev based cutoff
    if get_percentile_of_unique_peaks 
    peak_percentile = prctile(unique(cell_spike_frame_max_df{n}),cutoff_percentile);
    else  %else, if you SHOULDN"T get unique percentile of dff peaks 
    peak_percentile = prctile(cell_spike_frame_max_df{n},cutoff_percentile);
    end
    cutoff = peak_percentile; %percentile based cutoff
    % find spikes with dff << avg
    kept_spikes = cell_spike_frame_max_df{n} > cutoff; %boolean vec for spikes that exceed thresh
    trimmed_cell_IDs{n} = cell_row_storage{n}(kept_spikes); %if deleting spikes, delete cell IDs to keep list consistent 
    trimmed_spikes{n} = spike_storage{n}(kept_spikes); %if deleting spikes, delete cell IDs to keep list consistent 
end
toc
%% create new spike_raster from kept spikes
kept_spiketimes = cell2mat(trimmed_spikes);
kept_cellIDs = cell2mat(trimmed_cell_IDs);
%remade spikes
remade_idx = sub2ind(size(C), kept_cellIDs, kept_spiketimes);
new_spikes = zeros(size(C));
new_spikes(remade_idx)  = 1;

end

