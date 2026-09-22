classdef trim_params %for: setting a static declaration of how much data to take from each period
    properties (Constant)
        %% trim_params = struct(); %the parameters that will be fed into the trim function to truncate a sliced raster
        Pre = 'end'; %options are 'start', 'end', or 'none' if you want no trimming
        Post = 'start';
        ITI = 'start';
        %think about incorporating the accesible standar dname
        trial_len = 15; %10 seconds at 20 hz for main trial body
        ITI_len = 90; % 60 s at 20 hz
    end
end