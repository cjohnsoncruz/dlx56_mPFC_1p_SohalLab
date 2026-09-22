classdef table_methods
    %To- store functions that are static and meant ot be sued fo rmultiple
    %CSV processing
    properties
    end
    %% methods section
    methods(Static)
        %% turn struct with section names into table
        function table_row_full=  unpack_sectioned_struct_to_table(struct_section_storage, expt_name)
            %turns cosine similarity matrices into tables where each row = 1 element of %similarity matrix
            sections = analysis_config.trial_section_names;
            table_output = struct();
            for s= 1:3
                curr_section = sections (s);
                table_output.(curr_section) = struct2table(struct_section_storage.(curr_section));
                table_output.(curr_section).section = string(curr_section);  %need to make this into a string otherwise the vert cat of talbve  doesn't work well due to it being char
                table_output.(curr_section).name= string(expt_name);
            end
            table_row_full = [table_output.(sections(1)); table_output.(sections(2)); table_output.(sections(3))]; %create stacked table
        end
        %% shorten variable names
        function shortened_names_table = shorten_phase_names(input_table)
            new_table_vars = string(input_table.Properties.VariableNames);
            % shorten names
            short_section_names = ["pre", "post", "ITI"];
            short_error_correct_names = ["Corr", "Err"];
            for s = 1:length(short_section_names)
                new_table_vars = replace(new_table_vars, analysis_config.trial_section_names(s), short_section_names(s));
            end
            new_table_vars = replace(new_table_vars, "Correct", short_error_correct_names(1));
            new_table_vars = replace(new_table_vars, "Error", short_error_correct_names(2));
            new_table_vars = cellstr(new_table_vars);
            shortened_names_table = renamevars(input_table, input_table.Properties.VariableNames, new_table_vars);
        end

        %%manipulate cols
        function stacked_table = stack_tables_in_cell_array(cell_array_of_tables)
            for c = 1:length(cell_array_of_tables)-1 %stack table entry c with entry c+1, which means you stop 1 entry before table ends
                stacked_table = [cell_array_of_tables{c};cell_array_of_tables{c+1}];
            end
        end
        function table_with_dummy_col = add_nan_col(input_table, varargin)
            %to- add a column (named Var1 with Nans replicated for the current number
            %of rows in the table
            if nargin > 1
                dummy_nan = varargin(1);
            else
                dummy_nan = NaN;
            end
            Var1 = repelem(dummy_nan, size(input_table,1),1); %repeat NaN for number of rows
            Var1 = table(Var1); %if it's empty, make it a section of NaNs
            table_with_dummy_col = [input_table, Var1];

            % Var1 = repelem(NaN, size(dataset_object.raster,1),1);Var1 = table(Var1); %if it's empty, make it a section of NaNs
            % sig_AV_table_stack = [sig_AV_table_stack, Var1];
        end
        %% process csv outputs
        function process_csv_outputs(csv_name, suffix)
            %run in a directory with ONLY csvs of interest
            %% read all sheets in directory you're currently in
            files = dir(strcat('*', suffix)); %read all file information
            filenames = {files.name};  %extract names
            fprintf(strcat("Number of files found:", num2str(length(filenames))));
            %% use for loop to download each table and stack
            table_storage = cell(1,length(filenames));
            for i = 1:length(filenames)
                table_storage{i}= readtable(filenames{i}, 'VariableNamingRule', 'preserve'); %create cell array where each cell is 1 table
            end
            table_stack= vertcat(table_storage{:});
            % save
            writetable(table_stack, csv_name)
        end
    end
end