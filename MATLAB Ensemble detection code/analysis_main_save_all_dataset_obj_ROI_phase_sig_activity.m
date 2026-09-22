%% import/ list all datasetsrunning_on_server = true;
% Creates: TACO, mean activation 
%written Oct 2023 by Carlos Johnson-Cruz, Sohal Lab
%% import/ list all datasets
server_use = false;
root_dir = dataset_file_methods.get_root_dir(server_use);
if ~exist(root_dir, 'dir'), mkdir(root_dir); end
cd(root_dir)
%% create file storage
data_type_used = "neurons"; %other option is "neurons"/"cluster"
analysis_name =  [" sig enrichment vectors by task stage" , num2str(analysis_config.num_shuffles), "_shuffles_hour_"];
storage_folder_name = dataset_file_methods.make_storage_folder_name(root_dir, join([data_type_used, analysis_name, string(datetime('now', 'Format', 'HH'))],"_"));
mkdir(storage_folder_name); cd(storage_folder_name);
%% new- specify whether to skip AV sig activity
run_activity_enrichment = true;
export_mean_active = true;
%% iterate over all datasets
use_WT_CLNZ_folder = true
if use_WT_CLNZ_folder
dataset_folders = dataset_file_methods.get_dataset_folder_dir(server_use, data_type_used) % import dataset

% dataset_folders = 'C:\Users\13car\Dropbox\UCSF\vikaas\Ruleshifting task notes\dlx mice notes\All datasets- Padded Labels, raster, EXTRACT outputs\dataset_objects'
else
dataset_folders = dataset_file_methods.get_dataset_folder_dir(server_use, data_type_used) % import dataset
end

phase_type = analysis_config.phase_division_types(2)
content_names  = dataset_file_methods.get_list_datasets_in_folder(dataset_folders);
% #uncomment for debug
% f = 1;         dataset_object = dataset_file_methods.get_dataset_object_i(strcat(dataset_folders, "/", content_names(f)), data_type_used); %import object i

%% main enrichment loop 
if run_activity_enrichment
    cell_sig_active_table = cell(1,length(content_names));
    % for f = 1:length(content_names)
        parfor f = 1:length(content_names) %iterate over all datasets within the fields of the current database struct
        f
        dataset_object = dataset_file_methods.get_dataset_object_i(strcat(dataset_folders, "/", content_names(f)), data_type_used); %import object i
        cell_sig_active_table{f}  = return_binary_activity_vec_sig_active_in_task_stage(dataset_object); %25s for sample
    end  %% end loop over current batch's fields
    %% export table
    table_sizes = cellfun(@size, cell_sig_active_table, 'UniformOutput', false);
    for t = 1:length(table_sizes)
        if table_sizes{t}(2) < analysis_config.get_num_phase_pairs(phase_type)+2 %detect if missing baseline col
            cell_sig_active_table{t} = horzcat(cell_sig_active_table{t},table(zeros(table_sizes{t}(1),1), 'VariableNames', ["baseline"]));
        end
    end
    %%  add run table metadata
    combined_data = vertcat(cell_sig_active_table{:});
    metadata_vec = [string(datetime), analysis_config.num_shuffles,analysis_config.percentile, analysis_config.drop_low_value_peak_events, analysis_config.cutoff_filter , analysis_config.peak_event_cutoff_percentile]
    metadata_cols = table(repmat(metadata_vec,size(combined_data,1),1));
    standalone_metadata_table = table(metadata_vec)
    combined_data = horzcat(combined_data, metadata_cols);
    %note type of dataset used 
    if use_WT_CLNZ_folder
    dataset_cohort  = "WT_CLNZ_"
    else
        dataset_cohort = "main_datasets_"
    end
    %% save dataset as table
    metadata_tag = ""
if analysis_config.use_dff_not_spikes
    metadata_tag = join([metadata_tag, "dff"],"_")
end
if analysis_config.zscore_dff
    metadata_tag = join([metadata_tag, "zscore"],"_")
end

if analysis_config.shuffle_rand_permute
    metadata_tag = join([metadata_tag, "randperm"],"_")
end

    table_name = strcat(dataset_cohort, phase_type, "TACO- ", data_type_used, metadata_tag, "_activity by task phase_", string(datetime("today")),".xls")
    writetable(combined_data, table_name ); %write table
end %ends activity enrichment block
%% optional- export activity
if export_mean_active
    mean_activation_by_dataset = cell(1,length(content_names));
    for f = 1:length(content_names) %iterate over all datasets within the fields of the current database struct
        fprintf('%d/%d mean activity found\n', f, length(content_names));
        dataset_object = dataset_file_methods.get_dataset_object_i(strcat(dataset_folders, "/", content_names(f)), data_type_used); %import object i
        curr_mean_active = mean(dataset_object.raster,2);
        name_col = repmat(dataset_object.name,size(curr_mean_active,1),1);
        mean_activation_by_dataset{f} = table(curr_mean_active, name_col);
        activation_table = vertcat(mean_activation_by_dataset{:});
        writetable(activation_table, strcat(data_type_used, "_mean dataset activity_", string(datetime("today")),".xls")); %write table
    end
end

fprintf("Done creating all thresholded activity vectors for all datasets. Exported /n") % 2200s for 15 datasets
%% save analysis config information
%https://www.mathworks.com/help/matlab/matlab_oop/getting-information-about-properties.html
config_properties = ?analysis_config%
config_properties = config_properties.PropertyList; %list of currently active properties
n_properties = length(config_properties);
all_config_names = cell(1,n_properties);
for n = 1:n_properties
    all_config_names{n} = config_properties(n).Name;
end

config_to_skip = all_config_names([4, 6,28,29,31,32,35, 36,38,39,41]); %list of string names
% config_to_skip = all_config_names([6,28,29,31,32]); %list of string names 
property_struct = struct() ;% storage for property value
for n = 1:n_properties
    prop_name = config_properties(n).Name
    if ismember(prop_name, config_to_skip);
        continue
    end
    property_struct.(prop_name) = config_properties(n).DefaultValue;
end
%save property table
property_table = struct2table(property_struct, 'AsArray', true); 
writetable(property_table , strcat( "analysis config settings_ran_", string(datetime("today")),".xls")); %write table
