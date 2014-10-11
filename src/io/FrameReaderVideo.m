% An implementation of FrameGetter for reading frames from a video
%   It implements an interface getNewFrame()
%
% It is essentially a thin wrapper of vision.VideoFileReader

classdef FrameReaderVideo < FrameReader
    properties (Hidden)
        videoSource
    end % properties
    methods
        function FR = FrameReaderVideo (camName)
            global CITY_DATA_PATH
            if isempty(CITY_DATA_PATH), error('run rootPathsSetup.m first'); end
            
            videoPath = [CITY_DATA_PATH, '2-min/camera' num2str(camName) '.avi'];
            if ~exist (videoPath, 'file')
                disp (videoPath)
                error ('FrameReaderVideo: path does not exist');
            end
            
            FR.videoSource = vision.VideoFileReader (videoPath, ...
                'ImageColorSpace', 'RGB', 'VideoOutputDataType', 'uint8'); 
        end
        function frame = getNewFrame(FR)
            [frame, EOF] = step(FR.videoSource);
            if EOF == true
                frame = [];
            end
        end
    end % methods

end

     
