% An implementation of FrameWriterInterface for writing frames to a video
%
% It is essentially a wrapper of vision.VideoWriter
%
% (based on Lynna's createAVI.m code)
%


classdef FrameWriterVideo < FrameWriterInterface
    properties (Hidden)
        video          % output
        
        verbose;
    end % properties
    methods
        
        function self = FrameWriterVideo (videopath, framerate, varargin)
            parser = inputParser;
            addRequired (parser, 'videopath', @ischar);
            addRequired (parser, 'framerate', @isscalar);
            addParameter(parser, 'relpath', getenv('CITY_DATA_PATH'), @(x) ischar(x) && exist((x),'dir'));
            parse (parser, videopath, framerate, varargin{:});
            parsed = parser.Results;
            
            % make paths relative to input 'relpath'
            videopath = fullfile(parsed.relpath, videopath);
            
            if ~exist(fileparts(videopath), 'dir')
                error('parent dir of %s does not exist', videopath);
            end

            self.video = VideoWriter(videopath);
            self.video.FrameRate = framerate;
            open(self.video);
        end
        
        function step (self, frame)
            assert (~isempty(frame));
            writeVideo (self.video, frame);
        end
        
        function delete(FW)
            close (FW.video);
        end

    end % methods
end

