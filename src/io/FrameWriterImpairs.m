% An implementation of FrameWriter for writing pairs of frames as images
%   It implements an interface writeNextFrame()
%
% This class takes multiple frames and puts them together as [first second]
%   The purpose of the calss is to prepare pairs for Mechanical Turk
%


classdef FrameWriterImpairs < FrameWriter
    properties (Hidden)
        ext = '.jpg';
        imDir          % for output
        prevFrame = [] % the previous frame to pair with a new one
        prevName  = [] % name of the previous frame to compose pair name
    end % properties
    methods
        function FW = FrameWriterImpairs (imDir)
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'imDir', @(x) ischar(x) && exist(x, 'dir'));
            parse(parser, imDir);
            parsed = parser.Results;

            FW.imDir = parsed.imDir;
        end
        
        % accepts image pair
        function writeNextFrame(FW, frame, frameName)
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'frame', @(x) ~iscell(x) && (ismatrix(x) || ndims(x) == 3));
            addRequired(parser, 'frameName', @ischar);
            parse(parser, frame, frameName);
            
            % the very first frame
            if isempty(FW.prevFrame)
                FW.prevFrame = frame;
                FW.prevName = frameName;
                return
            end
            
            % check sizes
            assert (all(size(FW.prevFrame) == size(frame)));
            
            % make composite image
            img = [FW.prevFrame; frame];
            imgName = [FW.prevName '-' frameName FW.ext];
            
            % write
            imwrite (img, fullfile(FW.imDir, imgName));
            
            FW.prevFrame = frame;
            FW.prevName = frameName;
        end

    end % methods
end

