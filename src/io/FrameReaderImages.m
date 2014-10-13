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
        function FR = FrameReaderImages (imDir)

            FR.imDir = imDir;
            imTemplate = [FR.imDir, '*.jpg'];
            FR.imNames = dir (imTemplate);
            FR.counter = 1;
            
            if ~exist(FR.imDir, 'file')
                fprintf('FrameReaderImages(): FR.imDir = %s \n', FR.imDir);
                error('FrameReaderImages(): imDir doesn''t exist');
            end
            
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

