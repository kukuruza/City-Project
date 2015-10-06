% An implementation of FrameReaderInterface for reading frames from a video
%   It implements an interface getNewFrame()
%
% It is essentially a thin wrapper of vision.VideoFileReader

classdef FrameReaderVideo < FrameReaderInterface
    properties (Hidden)
        
        videoFid
        timesFid
        eof = false;
        
        verbose;
        
    end % properties
    methods
        
        function self = FrameReaderVideo (videoPath, timestampPath, varargin)
            parser = inputParser;
            addRequired(parser, 'videoPath', @ischar);
            addRequired(parser, 'timestampPath', @(x) ischar(x) || isempty(x));
            addParameter(parser, 'relpath', getenv('CITY_DATA_PATH'), @(x) ischar(x) && exist((x),'dir'));
            parse (parser, videoPath, timestampPath, varargin{:});
            parsed = parser.Results;
            
            % usually timestamp has the same prefix as video, so make timestamp from videoPath
            if isempty(timestampPath)
                [dir, name, ~] = fileparts(videoPath);
                timestampPath = fullfile(dir, [name, '.txt']);
            end
            
            % make paths relative to input 'relpath'
            videoPath     = fullfile(parsed.relpath, videoPath);
            timestampPath = fullfile(parsed.relpath, timestampPath);

            % check existance of files
            if ~exist(videoPath,'file') || ~exist(timestampPath, 'file')
                fprintf ('FrameReaderVideo: files: %s, %s\n', videoPath, timestampPath);
                error (['FrameReaderVideo: videoPath or timeStampPath doesn''t exist: ' ...
                        videoPath ', ' timestampPath]);
            end
            
            % open video and timestaamp files
            self.timesFid = fopen(timestampPath);
            self.videoFid = vision.VideoFileReader(videoPath, ...
                'ImageColorSpace','RGB','VideoOutputDataType','uint8'); 
        end
        function [frame, timestamp] = getNewFrame(self)
            if self.eof
                frame = [];
                timestamp = [];
            else
                [frame, self.eof] = step(self.videoFid);
                timestamp = fgetl(self.timesFid);
                assert (ischar(timestamp)); % there should be enough timestamp entries
            end
        end
        function delete(self)
            fclose(self.timesFid);
        end
        
    end % methods

end

     
