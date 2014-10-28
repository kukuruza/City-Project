% An implementation of FrameGetter for reading frames from a video
%   It implements an interface getNewFrame()
%
% It is essentially a thin wrapper of vision.VideoFileReader

classdef FrameReaderVideo < FrameReader
    properties (Hidden)
        videoSource
        timesTable
        counter = 1;
    end % properties
    methods
        function FR = FrameReaderVideo (videoPath, intervalsPath)
            if ~exist(videoPath,'file') || ~exists(intervalsPath, 'file')
                fprintf ('FrameReaderVideo: files: %s, %s\n', videoPath, intervalsPath);
                error ('FrameReaderVideo: videoPath or intervalsPath doesn''t exist');
            end
            FR.timesTable = dlmread(intervalsPath);
            FR.videoSource = vision.VideoFileReader(videoPath, ...
                'ImageColorSpace','RGB','VideoOutputDataType','uint8'); 
        end
        function [frame, timeinterval] = getNewFrame(FR)
            [frame, EOF] = step(FR.videoSource);
            if EOF == true
                frame = [];
            end
            timeinterval = FR.timesTable(FR.counter);
            FR.counter = FR.counter + 1;
        end
    end % methods

end

     
