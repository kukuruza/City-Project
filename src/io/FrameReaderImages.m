% An implementation of FrameGetter for reading .jpg images from a dir
%   It implements an interface getNewFrame()
%
% It is essentially a thin wrapper of imread()

classdef FrameReaderImages < FrameReader
    properties (Hidden)
        imNames;
        imDir;
        counter;
    end % properties
    
    methods
        function FR = FrameReaderImages (icam)
            global CITY_DATA_PATH
            if isempty(CITY_DATA_PATH), error('run rootPathsSetup.m first'); end
            
            % default camera
            if ~exist('icam', 'var'), icam = 360; end
            
            % move out constants
            FR.imDir = [CITY_DATA_PATH, 'five camera for 2 min/cameraNumber', ...
                                        sprintf('%03d', icam), '/'];
            imTemplate = [FR.imDir, '*.jpg'];
            FR.imNames = dir (imTemplate);
            FR.counter = 1;
            
            if isempty(FR.imNames)
                fprintf ('FrameReaderImages(): imTemplate = %s \n', imTemplate);
                error('FrameReaderImages(): imNames is empty');
            end
        end
        function frame = getNewFrame(FR)
            if FR.counter > length(FR.imNames)
                frame = [];
            else
                frame = imread([FR.imDir, FR.imNames(FR.counter).name]);
            end
            FR.counter = FR.counter + 1;
        end
    end % methods
    
end

