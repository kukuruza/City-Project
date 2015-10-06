classdef ImgDbWriterVideo < ImgDbWriterInterface
    % Implementation of only in a dataset based on storing images as a video
    
    properties
        relpath = '.';
        verbose = 0;
        
        videos;   % handles to open video writers
        framerate;  % common to everything
    end
    methods (Hidden)

        function video = openVideoWriter (self, videopath)
            % Open video and set up bookkeeping
            if self.verbose, fprintf ('opening video: %s\n', videopath); end
            videopath = fullfile (self.relpath, videopath);
            if ~exist(fileparts(videopath), 'dir')
                error ('directory of videopath does not exist: %s', videopath);
            end
            video = VideoWriter(videopath);
            video.FrameRate = self.framerate;
            open(video);
        end

    end
    methods 
        
        function self = ImgDbWriterVideo (varargin)
            % 'verbose' -- level of output verbosity
            % 'relpath' -- relative path in all further functions
            parser = inputParser;
            addParameter(parser, 'framerate', 2, @isscalar);
            addParameter(parser, 'verbose', 0, @isscalar);
            addParameter(parser, 'relpath', getenv('CITY_DATA_PATH'), @ischar);
            parse (parser, varargin{:});
            parsed = parser.Results;
        
            self.framerate = parsed.framerate;
            self.relpath = parsed.relpath;
            self.verbose = parsed.verbose;
            
            self.videos = containers.Map('KeyType','char','ValueType','any');
        end
        
        function writeImpl (self, videopath, frame)
            % video set up
            if ~isKey(self.videos, videopath)
                self.videos(videopath) = self.openVideoWriter (videopath);
            end
            if self.verbose, fprintf ('writing frame to %s\n', video_name); end
            writeVideo (self.videos(videopath), frame);
        end
        
        function imwrite (self, frame, dir_name)
            if self.verbose > 1, fprintf ('writing image.\n'); end
            self.writeImpl (dir_name, frame);
        end
        
        function maskwrite (self, mask, dir_name)
            if self.verbose > 1, fprintf ('writing mask.\n'); end
            mask = uint8(mask) * 255;
            mask = mask(:,:,[1,1,1]);
            self.writeImpl (dir_name, mask);
        end
        
        function close(self)
            videoKeys = keys(self.videos);
            for i = 1 : length(videoKeys)
                close(self.videos(videoKeys{i}))
            end
        end
        
        function delete(self)
            self.close()
        end
    end
end