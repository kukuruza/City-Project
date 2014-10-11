% An implementation of FrameReader for reading .jpg images from a dir
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
        function FR = FrameReaderImages (camNum)
            global CITY_DATA_PATH
            if isempty(CITY_DATA_PATH), error('run rootPathsSetup.m first'); end
            
            ext = '.jpg';
            FR.imDir = [CITY_DATA_PATH, '2-min/camera' num2str(camNum) '/'];
            if ~exist(FR.imDir, 'file')
                FR.imDir
                error ('FrameReaderImages: dir doesn''t exist');
            end
            imTemplate = [FR.imDir, 'image*', ext];
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

