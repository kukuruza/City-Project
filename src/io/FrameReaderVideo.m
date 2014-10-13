% An implementation of FrameGetter for reading frames from a video
%   It implements an interface getNewFrame()
%
% It is essentially a thin wrapper of vision.VideoFileReader

classdef FrameReaderVideo < FrameReader
    properties (Hidden)
        videoSource
    end % properties
    methods
        function FR = FrameReaderVideo ()
            global CITY_DATA_PATH
            if isempty(CITY_DATA_PATH), error('run rootPathsSetup.m first'); end
            
            % move out constants
            workingDir = [CITY_DATA_PATH, '/five camera for 2 min'];
            resultDir = fullfile(workingDir,'Result');
            videoName = fullfile(resultDir,'shuttle_out.avi');
            FR.videoSource = vision.VideoFileReader(videoName,'ImageColorSpace','RGB','VideoOutputDataType','uint8'); 
        end
        function delete (FR)
            release(FR.videoSource);
        end
        function frame = getNewFrame(FR)
            [frame, EOF] = step(FR.videoSource);
            if EOF == true
                frame = [];
            end
        end
    end % methods

end

     
