% An implementation of FrameGetter for reading frames from the internet
%   It implements an interface function getNewFrame()
%
% This class knows everything about cameras in NY,
%   about how to get frames from there, that duplicate frames should be
%   avoided and further on.

classdef FrameReaderInternet < FrameReader
    properties (Hidden)
        camNumber
    end % properties
    
    methods
        function FR = FrameReaderInternet ()
            % initialize connection, FR.camNumber or whatever else you need
        end
        function frame = getNewFrame(FR)
            % should return a new frame
            % if there is a problem should return []
        end
    end % methods
end