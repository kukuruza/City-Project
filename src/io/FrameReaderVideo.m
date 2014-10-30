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
        function FR = FrameReaderVideo (videoPath, timeStampPath)
            if ~exist(videoPath,'file') || ~exist(timeStampPath, 'file')
                fprintf ('FrameReaderVideo: files: %s, %s\n', videoPath, timeStampPath);
                error ('FrameReaderVideo: videoPath or timeStampPath doesn''t exist');
            end
            FR.timesTable = dlmread(timeStampPath);
            
            % Checking if the timestamp is indeed 6-elemented
            if(size(FR.timesTable, 2) ~= 6)
                error('FrameReaderVideo:Timestamp', ...
                    'TimeStamps expected to be 6 elemented : yyyy mm dd hh:mm:ss');
            end
            FR.videoSource = vision.VideoFileReader(videoPath, ...
                'ImageColorSpace','RGB','VideoOutputDataType','uint8'); 
        end
        function [frame, timeStamp] = getNewFrame(FR)
            [frame, EOF] = step(FR.videoSource);
            if EOF == true
                frame = [];
            end
            timeStamp = FR.timesTable(FR.counter, :);
            FR.counter = FR.counter + 1;
        end
    end % methods

end

     
