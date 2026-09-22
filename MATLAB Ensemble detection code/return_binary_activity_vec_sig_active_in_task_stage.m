function sig_AV_table_join = return_binary_activity_vec_sig_active_in_task_stage(dataset_object)
%using dataset class for increased legibility, written 09/2023 by Carlos Johnson-Cruz, updated 12/24
%TO- return a table where each column = a task period, each row = a cell, %and each entry = 1 or 0 if that cell was sig. active > chance during that %task period
% INPUTS- daataset object, phase_type

fprintf(strcat(" Creating binary activity vector for dataset: ", dataset_object.name, "\n"))
%% NEW- WIP drop events if below peak value
if analysis_config.drop_low_value_peak_events
    [new_spikes,kept_spiketimes,kept_cellIDs ] = drop_spike_if_has_low_peak_dff(dataset_object.raster, dataset_object.C(dataset_object.good_cells,:),analysis_config.peak_event_cutoff_percentile );
else
    new_spikes = dataset_object.raster;
end
%% NEW_ switch between dff vs spikes

if analysis_config.use_dff_not_spikes
    %NEW-filter DFF by cells preserved post-deduplication
    C = dataset_object.C(dataset_object.cells_kept_post_deduplication,:);
    if analysis_config.zscore_dff
        new_spikes = zscore(C , 0, 2);
    else
        new_spikes = C;
    end
end
%% detect if baseline period exists
baseline_data = baseline_class(new_spikes, dataset_object.labels); %return the properties of the dataset object to make baseline class object
%%  %define early IA correct, early IA error, early RS correct, early RS error with trial number and index
phase_type = analysis_config.phase_division_types(2);
phase_index_obj = phase_index(dataset_object.labels,  phase_type ); %extract criteria from options, creates new phase object
all_phase_pair_rasters = all_section_phase_pair_rasters(new_spikes, dataset_object.labels, phase_index_obj); %create object where sec_phase_storage contains each version of this
%% new- 12/1/24- define what frames are used for what
frame_ID = [1:size(new_spikes,2)];
frame_by_stage = all_section_phase_pair_rasters(frame_ID, dataset_object.labels, phase_index_obj); %create object where sec_phase_storage contains each version of this
%% OLD METHOD- create shuffles- 1s per shuffle
% [shuffles_array, ~] = make_shuffle_methods.create_n_circ_shuffles(analysis_config.num_shuffles, new_spikes); %10 seconds - 10 shuffles/40 shuffles, 40 seconds
%% find, for each task period, what the shuffled version of activity would be, and threshold real data vs the percentile of that shuffle matrix
num_phase_pairs_curr = analysis_config.get_num_phase_pairs(phase_type);
task_section_stage_pairs = analysis_config.all_section_phase_pair_names;
%% find-task period corrs loop over shuffles and split
phase_shuffle_metric = struct();
stage_pvalue = struct();
all_vecs = all_phase_pair_rasters.sec_phase_storage; %get the actual vector objects 
%% loop over shuffles
n_shuf = analysis_config.num_shuffles; %100 shuffles- ~100s to get all metrics; 200- 275s on local
for p = 1:num_phase_pairs_curr                 % for p = 1:analysis_config.num_section_phase_pairs
    section= task_section_stage_pairs(p,1);  stage = task_section_stage_pairs(p,2);
    %shuffle mean act by stage
    frames_of_interest = frame_by_stage.sec_phase_storage.(section).(stage).raster; %get the frames you care about for the current breakdown
    %if frames don't exist (= subj. doesn't have trials, no point in    %shuffling)
    if all(isnan(frames_of_interest), 'all') | isempty(frames_of_interest) %if section doesnt exits, don't create threshold

        phase_shuffle_metric.(section).(stage) = NaN;
        num_cells = size(new_spikes,1); %preserve one placeholder per cell when this stage has no frames
        thresholded_vectors.(section).(stage) = repmat(-99,num_cells,1);
        %add nan cols to pvalue + threshold sections
        phase_shuffle_metric.(section).(stage) =  repmat(-99,num_cells,1);
        stage_pvalue.(section).(stage) = repmat(-99,num_cells,1);

    else % NEW- 12/12/24- shuffle indices instead of frames, speedup time
        % NEW- 3.1.26- add random permutation option for revision
        % comparison with circular shuffle:
        if analysis_config.shuffle_rand_permute
            task_act_by_shuffle = shuffle_randperm(new_spikes, size(frames_of_interest,2), n_shuf);
        else 
        task_act_by_shuffle = shuffle_frames_and_get_frame_activity(new_spikes, frames_of_interest, n_shuf);     % each shuffle is 1 col in output mat 
        end
        assert(size(task_act_by_shuffle,2) == analysis_config.num_shuffles, "error- combined vector num cols doesn't equal num shuffles")
        phase_shuffle_metric.(section).(stage) = prctile(task_act_by_shuffle, analysis_config.percentile,2); %is currently the AV that's returned
        %check percentile against AV
        real_av = mean(all_vecs.(section).(stage).raster,2);
        
        % new in 11/17/25- add shuffle threshold + p-value to struct, which
        assert(size(task_act_by_shuffle,1) == size(real_av,1), "error- # of cells in shuffle mat != # of cells in real AV")
        stage_pvalue.(section).(stage) = mean(real_av<=task_act_by_shuffle,2); %find % of shuffles >= real value
        thresholded_vectors.(section).(stage) = double( real_av> phase_shuffle_metric.(section).(stage)); %threshold by Nth %ile of shuffle datasets        
        % then becomes table% sig_AV_table_join.shuffle_threshold = phase_shuffle_metric.(section).(stage);

    end    %once you have thresholds, return thresholds vectors
end %loop over all stage-section pairs
%% convert concated task phases to table
sig_AV_table_join = vectorize_raster_methods.convert_section_phase_vecs_to_table_and_join(thresholded_vectors);
pval_table = vectorize_raster_methods.convert_section_phase_vecs_to_table_and_join(stage_pvalue);
thresh_table = vectorize_raster_methods.convert_section_phase_vecs_to_table_and_join(phase_shuffle_metric);
% 11/17/2025- made and concat pvalue and threshold tables add correct labels
pval_table.Properties.VariableNames = strcat("pvalue", "_",pval_table.Properties.VariableNames);
thresh_table .Properties.VariableNames = strcat("threshold_95", "_",thresh_table .Properties.VariableNames);
sig_AV_table_join = horzcat([sig_AV_table_join,pval_table,thresh_table]);
%% extract baseline activity vectors
if baseline_data.is_usable % take baseline period of shuffles
    %new method using frame permutation extended to baseline
    baseline_frames = find(dataset_object.labels == 1);
    baseline_act_by_shuffle = shuffle_frames_and_get_frame_activity(dataset_object.raster, baseline_frames, n_shuf);
    baseline_thresh = prctile(baseline_act_by_shuffle, analysis_config.percentile,2); %is currently the AV that's returned
    baseline_AV = mean(baseline_data.raster,2);
    baseline_sig_cells = baseline_AV> baseline_thresh;
    %Old 2023 method     % shuff_baseline_percentiles = baseline_access_methods.get_shuffle_baseline_percentile(shuffles_array, dataset_object.labels);
    sig_AV_table_join = [sig_AV_table_join, table(baseline_sig_cells)]; %take Nth %ile of activity of concated baselines, no need to individualize %for the AVs
else
    sig_AV_table_join = table_methods.add_nan_col(sig_AV_table_join,-99);
end
% sig_AV_table_join = renamevars(sig_AV_table_join, "Var1", "baseline");
%add name col, % add geno_day col  % add geno col
sig_AV_table_join.name = repmat(string(dataset_object.name), size(dataset_object.raster,1),1);
sig_AV_table_join.geno_day = repmat(string(dataset_object.geno_day), size(dataset_object.raster,1),1);
sig_AV_table_join.geno = repmat(string(dataset_object.geno), size(dataset_object.raster,1),1);
sig_AV_table_join.neuron_ID = [1:size(dataset_object.raster,1)]';
sig_AV_table_join.peak_dff_threshold_percentile = repelem(analysis_config.peak_event_cutoff_percentile,size(dataset_object.raster,1),1); %detail on the percentile cutoff used for excluding raster events
end