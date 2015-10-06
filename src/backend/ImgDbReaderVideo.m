classdef ImgDbReaderVideo < ImgDbReaderInterface
    % Implementation of only in a dataset based on storing images as a video
    
    properties
        relpath = '.';
        verbose = 0;
        
        image_video
        mask_video
        
        image_cache
        mask_cache
        
        % keep current frame. Use map to have handle
        current_frames
        
    end
    methods (Hidden)

        function video = openVideoReader (self, videopath)
            % Open video and set up bookkeeping
            if self.verbose, fprintf ('opening video: %s\n', videopath); end
            videopath = fullfile (self.relpath, videopath);
            if ~exist(videopath, 'file')
                error ('videopath does not exist: %s', videopath);
            end
            video = vision.VideoFileReader(videopath, 'VideoOutputDataType','uint8');
        end

    end
    methods 
        
        function self = ImgDbReaderVideo (varargin)
            % 'verbose' -- level of output verbosity
            % 'relpath' -- relative path in all further functions
            parser = inputParser;
            addParameter(parser, 'cache_size', 50, @isscalar);
            addParameter(parser, 'verbose', 0, @isscalar);
            addParameter(parser, 'relpath', getenv('CITY_DATA_PATH'), @ischar);
            parse (parser, varargin{:});
            parsed = parser.Results;
        
            self.relpath = parsed.relpath;
            self.verbose = parsed.verbose;
            
            self.image_video = containers.Map('KeyType','char','ValueType','any');
            self.mask_video  = containers.Map('KeyType','char','ValueType','any');

            self.image_cache = CacheStack (parsed.cache_size);
            self.mask_cache  = CacheStack (parsed.cache_size);
            
            % keep current frame. Use map to have handle
            self.current_frames = containers.Map ({'image','mask'}, {0, 0});
        end
        
        function frame = readImpl (self, image_id, ismask)
            % choose the dictionary, depending on whether it's image or mask
            if ~ismask
                video_dict = self.image_video;
                expected_frame = self.current_frames('image');
                cache = self.image_cache;
            else
                video_dict = self.mask_video;
                expected_frame = self.current_frames('mask');
                cache = self.mask_cache;
            end
            % check cache first
            frame = cache.find(image_id);
            if isempty(frame)
                if self.verbose > 1, fprintf ('%s is not in cache.\n', image_id); end
            else
                if self.verbose > 1, fprintf ('found %s in cache.\n', image_id); end
                return
            end
            % video id set up
            [dir_name, frame_name] = fileparts(image_id);
            videopath = [dir_name '.avi'];
            if ~isKey(video_dict, videopath)
                video_dict(videopath) = self.openVideoReader (videopath);
            end
            % frame id
            frame_id = sscanf(frame_name, '%d');
            if self.verbose
                fprintf ('from image_id %s, got frame_id %d\n', image_id, frame_id);
            end
            % read the frame
            if expected_frame > frame_id
                self.current_frames('mask')
                error ('expected_frame=%d > frame_id=%d is not supported', ....
                       expected_frame, frame_id);
            end
            % read until reached the frame_id
            while true
                if self.verbose > 1, fprintf ('expected_frame %d\n', expected_frame); end
                % do not check if read past the eof
                [frame, eof] = video_dict(videopath).step();
                expected_frame = expected_frame + 1;
                % update cache
                cache.pushWithReplace (image_id, frame);
                % stop condition
                if expected_frame > frame_id, break; end
            end
            % assign the dict back to where it was taken from
            if ~ismask
                self.current_frames('image') = expected_frame;
                self.image_cache = cache;
            else
                self.current_frames('mask') = expected_frame;
                self.mask_cache = cache;
            end
        end
        
        
        function image = imread (self, image_id)
            if self.verbose > 1, fprintf ('reading image.\n'); end
            image = self.readImpl (image_id, false);
        end
        
        
        function mask = maskread (self, mask_id)
            if self.verbose > 1, fprintf ('reading mask.\n'); end
            mask = self.readImpl (mask_id, true);
            mask = mask(:,:,1) > 128;
        end
        
        
        function close(self)
            videoKeys = keys(self.image_video);
            for i = 1 : length(videoKeys)
                release(self.image_video(videoKeys{i}))
            end
            videoKeys = keys(self.mask_video);
            for i = 1 : length(videoKeys)
                release(self.mask_video(videoKeys{i}))
            end
        end
        
        function delete(self)
            self.close()
        end
    end
    
end