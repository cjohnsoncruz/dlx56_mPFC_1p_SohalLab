classdef dataset_with_spatial_ROI % testing for creating dataset
    %% properties
    properties % TEMP-STORE PARAMETERS FOR TRIMMING
        name string {mustBeText}  = 'empty name'
        geno_day string {mustBeText}  = 'empty geno day'
        geno string  = 'empty geno'
        raster {mustBeFinite} = []
        labels (1,:) = [] %always a
        ROI_locations = []; %for storing good cells
        cells_kept_post_deduplication = [];
        deduplicated = false; %flag for whether the spatial deduplication through overlap analysis is complete
        output_struct = [];
        num_cells{double} = [];
        C = []; %NEW- 10.23.24, added for post-hoc spike dropping algorithm
        spike_thresh_data = []; %new 10.26.24, for storing spike threshold information
        low_act_cells_dropped = [];
    end
    %% methods
    methods %functions go after here
        function built_obj = dataset_with_spatial_ROI(name,C, spike_thresh_data, raster,labels, output_struct, already_ran_dedup_flag)
            if nargin > 0
                built_obj.name = name;
                split_name = strsplit(name, "_");
                built_obj.geno_day =join(split_name(3:end));
                built_obj.geno =join(split_name(3)); %geno must be in the name, at the 3rd _string_ entry
                built_obj.raster = raster;
                built_obj.labels = labels;
                built_obj.spike_thresh_data = spike_thresh_data; %keep information on the spike detection paramaters using
                built_obj.num_cells= size(raster,1);
                built_obj.C = C; %NEW- 10.23.24 for post post-hoc spike dropping
                built_obj.deduplicated = already_ran_dedup_flag;
                %check that raster and labels have matching lengths, if not, pad
                if length(raster) > length(labels)
                    fprintf("Raster is %d longer than labels, padding labels. \n", [length(raster)-length(labels)])
                    built_obj = pad_label_vector(built_obj);
                end
                
                %import, unpack output for spatial deduplication step later
                built_obj.output_struct.spatial_weights = output_struct.spatial_weights;
                built_obj.output_struct.temporal_weights = output_struct.temporal_weights;
                built_obj.output_struct.user_labels = output_struct.user_labels;
                built_obj.output_struct.subject_name = name;
                %if the input raster is same size as the temporal weights,%then you've fogotten to trim
                if all(size(built_obj.raster) == size(output_struct.temporal_weights))
                    %trim using the user labels
                    built_obj.raster = built_obj.raster(output_struct.user_labels == 1, :);
                end
                
                %run deduplication
                if ~built_obj.deduplicated %flag for whether the spatial deduplication through overlap analysis is complete
                    built_obj= deduplicate_ROI(built_obj);
                end
                %NEW- drop datasets with < 0 cells
                cell_mean_act = mean(built_obj.raster,2); %vector of mean activity
                if  analysis_config.drop_low_act_cell_in_dataset_obj
                    fprintf("Dropping cells below config activity mean act. threshold.")
                    cell_low_act = cell_mean_act < analysis_config.low_act_thresh_in_obj_init ;
                    built_obj.C = built_obj.C(~cell_low_act,:);
                    built_obj.raster = built_obj.raster(~cell_low_act,:);
                    built_obj.low_act_cells_dropped = sum(cell_low_act);
                end
                
                fprintf("Packaged dataset:" + built_obj.name + "\n")
                
            end %end init function
            
        end
        function [name, ras, labels] =  return_name_raster_labels(obj)
            [name, ras, labels] =  deal(obj.name, obj.raster, obj.labels);
        end
        
        function plot_activity(obj) %plot simple raster of dataset
            figure; imagesc(obj.raster); colorbar; title(strrep(obj.name, "_", " "));
        end
        
        function built_obj= deduplicate_ROI(built_obj) % code to run spatial deduplication here
            [de_duplicate_output] = spatial_activity_deduplication.find_sig_adjacency_and_remove_ROI(built_obj.output_struct);

            built_obj.cells_kept_post_deduplication = de_duplicate_output.preserved_cells;
            built_obj.raster = built_obj.raster(built_obj.cells_kept_post_deduplication,:);
            built_obj.deduplicated = true;
        end
        
        function built_obj = pad_label_vector(built_obj)
            %to- given a mismatched length of label and raster, pad label vector to match the length of the activity
            %remember to check that the last entry = 15, if not set to 15
            label = built_obj.labels;
            raster_size = size(built_obj.raster,2);
            label_len = length(label);
            last_label = 15;
            
            sizediff = raster_size - label_len;
            fprintf(strcat("Adding ", num2str(sizediff), " frames to end of labels vec \n"))
            if label_len < raster_size
                paddedLabels = [label, repelem(last_label, sizediff)]; %pad length
            else
                fprintf('label is not shorter than raster'); fprintf(' replacing 0s at end');
                last_real_label = find(label,1, 'last');
                paddedLabels = label;
                paddedLabels(last_real_label:end) = 15;
            end
            %set labels to now = padded version
            built_obj.labels = paddedLabels;
        end
    end %end methods
end %end class def
