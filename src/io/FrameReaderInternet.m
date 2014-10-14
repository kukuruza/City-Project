% An implementation of FrameGetter for reading frames from the internet
%   It implements an interface function getNewFrame()
%
% This class knows everything about cameras in NY,
%   about how to get frames from there, that duplicate frames should be
%   avoided and further on.

classdef FrameReaderInternet < FrameReader
    properties (Hidden)
        % url example: http://207.251.86.238/cctv360.jpg?rand=0988954345345
        urlPart1 = 'http://207.251.86.238/cctv';
        urlPart2 = '.jpg?rand=';
        CallDelay = 0.7; % min interval after the previous successful call
        CallInterval = 0.1; % min interval in seconds between calls
        url               % is made up from parts 
        camNum            % number of the camera, given in constructor
        lastFrame = [];   % to compare against a new one. If same then wait
        lastCall = tic;   % time of the last call. If too close then wait
    end % properties
    
    methods
        function FR = FrameReaderInternet (camNum)
            FR.camNum = camNum;
            FR.url = [FR.urlPart1 num2str(camNum) FR.urlPart2];
        end
        function [frame, timeinterval] = getNewFrame(FR)
            % wait until new image is there
            while true
                
                % save some server requests
                while toc(FR.lastCall) < FR.CallDelay
                    pause(FR.CallInterval);
                end
                
                frame = imread([FR.url num2str(now)]);
                if isempty(FR.lastFrame)
                    timeinterval = -1;
                    FR.lastFrame = frame;
                    break
                elseif nnz(FR.lastFrame - frame) ~= 0
                    timeinterval = toc(FR.lastCall);
                    FR.lastFrame = frame;
                    break
                end
                %if ~isempty(FR.lastFrame), nnz(FR.lastFrame - frame), end
                
                pause(FR.CallInterval);
                
            end
            FR.lastCall = tic;
        end
    end % methods
end