classdef baseline_access_methods
    %% To-  "For accessing baseline period data in ruleshifting recordings"
    properties
        help = "For accessing baseline period data in ruleshifting recordings"
    end
    methods(Static)
        function baseline_data = extract_baseline_activity(input_raster, input_labels)
            %set logical for baseline frames
            baseline_frames = input_labels == 1;
             baseline_data = full(input_raster(:, baseline_frames));

            if sum(baseline_frames) >= analysis_config.min_baseline_len  %if baseline is longer than 10 minutes, take only 10 minutes
                baseline_data = baseline_data(:,sum(baseline_frames)-analysis_config.min_baseline_len:end);
            end
            if sum(baseline_frames) < analysis_config.min_baseline_len 
                fprintf("WARNING- baseline < minimum length in analysis_config")
                baseline_data = NaN
            end
        end
        
        function shuff_baselines_all_frames = extract_baseline_from_shuffles(shuff_cell_array, input_labels)
            %set logical for baseline frames
            %import and iterate over relevant baseline frames from each of
            %%the z shuffles, returnign a cell array
            shuff_baselines_all_frames = cell(1,analysis_config.num_shuffles);
            for z = 1:numel(shuff_baselines_all_frames)
                shuff_baselines_all_frames{z} =   baseline_access_methods.extract_baseline_activity(shuff_cell_array{z}, input_labels);
            end
        end
        %% shuffle based percentile gathering
        function shuff_baseline_percentiles = get_shuffle_baseline_percentile(shuffle_cell_array, input_labels)
            shuff_baseline_all_frames = baseline_access_methods.extract_baseline_from_shuffles(shuffle_cell_array,input_labels );
            shuff_baseline_means = squeeze(mean(reshape(full(cell2mat(shuff_baseline_all_frames)), size(shuffle_cell_array{1},1), [], analysis_config.num_shuffles),2));
            shuff_baseline_percentiles = prctile(shuff_baseline_means, analysis_config.percentile,2);
        end
        
        function shuff_baseline_corr_thresh = get_shuffle_baseline_corr_vec_percentile(shuffle_cell_array, input_labels)
            %returns vector of %ile in question for each cell-pair across %the shuffles
            shuff_baseline_all_frames = baseline_access_methods.extract_baseline_from_shuffles(shuffle_cell_array,input_labels); %return cell array
            shuff_baseline_corr = cell(1,length(shuff_baseline_all_frames));
            for s = 1:length(shuff_baseline_all_frames)
                shuff_baseline_corr{s} = corr(full(shuff_baseline_all_frames{s})'); %get correlation of shuffle frames
                shuff_baseline_corr{s} = matrix_corr_methods.zero_mat_identity_and_take_upper_tri( shuff_baseline_corr{s}); %return 1x unique cell pair corr vector
            end
            shuff_concat_corr_vecs= full(cell2mat(shuff_baseline_corr));
            shuff_baseline_corr_thresh = prctile(shuff_concat_corr_vecs, analysis_config.percentile,2); %when corr vector input, percentile is for each shuffle
        end

        %% baseline analysis methods

        %% downsample baseline 
        function post_downsample_raster = downsample_baseline(dataset_object, vargin) %vargin allows for downsampling rate to be decided
            if nargin == 2
                downsample_rate = vargin;
            else
                downsample_rate = analysis_config.time_series_bin_size; 
            end
            baseline_obj = baseline_class(dataset_object.raster, dataset_object.labels);
            if baseline_obj.is_usable% perform analysis only if there are sufficient baseline recording
                post_downsample_raster = vectorize_raster_methods.downsample_raster(baseline_obj.raster, downsample_rate);
            else
                fprinf('ERROR- baseline not long enough to be used, skipped downsample.')
            end
        end %end downsampling 
        %% return struct of mean and sdev of baseline raster
        function firingRates = get_baseline_mean_sdev(baseline_raster)
                neuron_mean_event= mean(baseline_raster, 2);
                neuron_sdev_event = std(baseline_raster');
                %% store outputs
                firingRates = struct();
                firingRates.mean_events_hz= neuron_mean_event;
                firingRates.sdev_events = neuron_sdev_event';
        end %end baselien function 

        %% export baseline sdev to table 
        function export_baseline_activity_sdev_to_table(dataset_object, storage_folder)
            %% create baseline object
            post_downsample_raster = downsample_baseline(dataset_object);
            %% perform analysis only if there are sufficient baseline recording
            if baseline_obj.is_usable
                %% find summary statistics
                firingRates = get_baseline_mean_sdev(post_downsample_raster);
                %% create table for storage
                baseline_event_table = table(repelem(dataset_object.name,size(dataset_object.raster,1))', neuron_mean_event, neuron_sdev_event');
                baseline_event_table.Properties.VariableNames = ["Experiment Name", "Neuron Mean Event Rate (hz)", "Neuron SDev"];
                csv_name = strcat(dataset_object.name, '-Baseline Firing Rate Analysis.xls'); %string array telling what name to give downloaded CSV
                %% create dir and save
                createFolder = false;
                fprintf(strcat('Saving baseline FR for ', dataset_object.name, ' \n'))
                writetable(baseline_event_table, strcat(dataset_object.name, csv_name));
                save(strcat(storage_folder, dataset_object.name, '-Baseline Firing Rate Analysis outputs.mat'), 'firingRates')
            else
                %do not export table
                 fprinf('ERROR- baseline not long enough to be used, skipped export and quantification.')
            end

        end

    end %end static methods
end