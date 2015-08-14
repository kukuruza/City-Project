% An implementation of FrameGetter for reading frames from a video
%   It implements an interface getNewFrame()
%
% It is essentially a thin wrapper of vision.VideoFileReader

classdef FrameReaderVideo < FrameReader
    properties (Hidden)
        videoSource
        timesTable
        counter = 1;
        eof = false;
    end % properties
    methods
        function FR = FrameReaderVideo (videoPath, timeStampPath)
            % usually timestamp has the same prefix as video, so make timestamp from videoPath
            if nargin == 1
                [dir, name, ~] = fileparts(videoPath);
                timeStampPath = fullfile(dir, [name, '.txt']);
            end
            
            if ~exist(videoPath,'file') || ~exist(timeStampPath, 'file')
                fprintf ('FrameReaderVideo: files: %s, %s\n', videoPath, timeStampPath);
                error (['FrameReaderVideo: videoPath or timeStampPath doesn''t exist: ' ...
                        videoPath ', ' timeStampPath]);
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
            if ~FR.eof
                [frame, FR.eof] = step(FR.videoSource);
            end
            if FR.eof
                frame = [];
                timeStamp = [];
            else
                timeStamp = FR.timesTable(FR.counter, :);
                FR.counter = FR.counter + 1;
            end
        end
    end % methods

end

     
