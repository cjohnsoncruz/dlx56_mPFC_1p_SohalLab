classdef dataset_file_methods
    %to- store static methods used to get/set names of dataset files
    %% properties
    properties
    end
    %% methods
    methods(Static)
        %
        function dataset_folders = get_dataset_folder_dir(server_use, data_type_used)
            if server_use
                dataset_folders = "/sohal1/cjcruz/Dlx mice inscopix/Dataset Components _11_23_24/dataset_objects_24-Nov-2024_hour_19"
            else
                %for concordance with CANON taco ensembles used in paper, %which used "Dataset Components_11_23_24/dataset_objects_24-Nov-2024_hour_19"
                    dataset_folders = fullfile(fileparts(fileparts(mfilename('fullpath'))), "data", "dataset_objects_24-Nov-2024_hour_19");
                % dataset_folders = "G:\My Drive\Colab Notebooks\Sohal Lab Datasets\Raw Mouse Datasets\dataset_object_storage"; %not canon taco ensembles
            end
        end
        %
        function root_dir = get_root_dir(server_use)
            if server_use
                root_dir = "/sohal1/cjcruz/Dlx mice inscopix/Joined dataset analysis"
            else
                root_dir = fullfile(fileparts(fileparts(mfilename('fullpath'))), "results", "matlab_ensemble_detection");
            end
        end
        %
        function dataset_object_i = get_dataset_object_i(content_names, data_type_used)
            %to- check the number of dataset objects in the folder, and
            %extract num i
            if data_type_used == "cluster"
                dataset_object_i = load(content_names).cluster_dataset;
            else
                dataset_object_i = load(content_names).dataset_object;
            end
        end
        %
        %if loading cluster dataset
        function dataset_object_i = get_cluster_object_i(content_names)
            %to- check the number of dataset objects in
            dataset_object_i = load(content_names).cluster_dataset;
        end

        %folder names
        function dataset_names = get_all_dataset_names_from_folder(content_names)
            %loops over all files found in folder
            num_files =length(content_names);
            dataset_names = strings(1,num_files);
            for f = 1:num_files
                dataset_names(f) = dataset_file_methods.get_dataset_name_from_filename(content_names{f});
            end
        end

        function single_dataset_name = get_dataset_name_from_filename(file_name)
            %requires 1x 1 string input with underscores joining each segment
            split_name = split(file_name, "_"); %create file x split array, cut at an underscore
            single_dataset_name = join(split_name(1:4), "_");
        end

        function storage_folder_name = make_storage_folder_name(root_dir, varargin )
            % #get variable input, formerly condition, data_type, analysis_type
            storage_folder_name = strcat(root_dir, "/" ,string(datetime("today")));
            for n= 1:nargin-1
                storage_folder_name = strcat(storage_folder_name, "_", varargin{n});
            end
            % storage_folder_name = strcat(root_dir, "/" ,string(datetime("today")), condition, "_",data_type,"_", analysis_type, "_run_", );
        end

        function content_names = get_list_datasets_in_folder(folder_name)
            %adds optional dataset_object suffix
            folder_contents = dir(strcat(folder_name, "/*_obj*"));
            content_names = cellfun(@string, {folder_contents.name});
        end
        function content_names  = get_folder_names(folder_name)
            %use PWD when you want to look at current folder
            folder_contents = dir(strcat(folder_name, "/*.mat"));
            content_names = cellfun(@string, {folder_contents.name});
        end

    end %end methods
end