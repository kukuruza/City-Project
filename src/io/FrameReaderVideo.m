% An implementation of FrameGetter for reading frames from a video
%   It implements an interface getNewFrame()
%
% It is essentially a thin wrapper of vision.VideoFileReader

classdef FrameReaderVideo < FrameReader
    properties (Hidden)
        videoSource
    end % properties
    methods
        function FR = FrameReaderVideo (videoPath)
            if ~exist(videoPath,'file')
                fprintf ('FrameReaderVideo: videoPath: %s\n', videoPath);
                error ('FrameReaderVideo: videoPath doesn''t exist');
            end
            FR.videoSource = vision.VideoFileReader(videoPath, ...
                'ImageColorSpace','RGB','VideoOutputDataType','uint8'); 
        end
        function [frame, timeinterval] = getNewFrame(FR)
            [frame, EOF] = step(FR.videoSource);
            if EOF == true
                frame = [];
            end
            timeinterval = 1;
        end
    end % methods

end

     
