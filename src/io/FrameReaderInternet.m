% An implementation of FrameReaderInterface for reading frames from the internet
%   It implements an interface function getNewFrame()
%
% This class knows everything about cameras in NY,
%   about how to get frames from there, that duplicate frames should be
%   avoided and further on.

classdef FrameReaderInternet < FrameReaderInterface
    properties (Hidden)
        % url of the web-viewer
        urlViewerPart = 'http://dotsignals.org/multiview2.php?listcam=';
        % url example: http://207.251.86.238/cctv360.jpg?rand=0988954345345
        urlPart1 = 'http://207.251.86.238/cctv';
        urlPart2 = '.jpg?rand=';
        CallDelay = 0.7; % min interval after the previous successful call
        CallInterval = 0.1; % min interval in seconds between calls
        url               % is made up from parts 
        camId             % number of the camera, given in constructor
        lastFrame = [];   % to compare against a new one. If same then wait
        lastCall = tic;   % time of the last call. If too close then wait
        
        timeZone;
        verbose;
    end % properties
    
    methods
        function self = FrameReaderInternet (camId, varargin)
            parser = inputParser;
            addRequired (parser, 'camId', @isscalar);
            addParameter(parser, 'timeZone', 'America/New_York', @ischar);
            addParameter(parser, 'verbose', 0, @isscalar);
            parse (parser, camId, varargin{:});
            parsed = parser.Results;
            
            % open the viewer and read the html
            urlViewer = [self.urlViewerPart num2str(camId)];
            content = urlread(urlViewer);
            
            % find the camera number in the html
            match = regexp(content, 'http://207.251.86.238/cctv\d+', 'match');
            assert (~isempty(match));
            
            % set the camera number and image url
            self.camId = str2num( match{1}(27:end) );
            self.url = [self.urlPart1 num2str(self.camId) self.urlPart2];
            
            % the time will be in this timezone
            self.timeZone = parsed.timeZone;
            
            self.verbose = parsed.verbose;
        end
        function [frame, timestamp] = getNewFrame(self)
            % wait until new image is there
            if self.verbose > 1, fprintf ('getting a new image from web server...\n'); end
            while true
                
                % save some server requests
                while toc(self.lastCall) < self.CallDelay
                    pause(self.CallInterval);
                end
                
                if self.verbose > 1, fprintf ('trying to read...\n'); end
                try
                    frame = [];
                    frame = imread([self.url num2str(now)]);
                catch
                    if isempty(frame), continue; end
                    frame = self.lastFrame;
                end
                
                if isempty(self.lastFrame)
                    self.lastFrame = frame;
                    timestamp = matlabDatetime2dbTime(datetime('now','TimeZone',self.timeZone));
                    break
                else
                    if(ndims(self.lastFrame) ~= ndims(frame))
                        continue;
                    end
                    if nnz(self.lastFrame - frame) ~= 0
                        self.lastFrame = frame;
                        timestamp = matlabDatetime2dbTime(datetime('now','TimeZone',self.timeZone));
                        break
                    end
                end
                %if ~isempty(FR.lastFrame), nnz(FR.lastFrame - frame), end
                
                pause(self.CallInterval);
                
            end
            self.lastCall = tic;
            if self.verbose > 0, fprintf ('got a new image from web server.\n'); end
        end
    end % methods
end
