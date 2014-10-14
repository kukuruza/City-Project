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
            FW.imDir = imDir;
            
            if ~exist(imDir, 'file')
                fprintf ('FrameWriterVideo(): imDir: %s\n', imDir);
                error ('FrameWriterVideo(): imDir doesn''t exist');
            end
        end
        
        % accepts image pair
        function writeNextFrame(FW, frame, frameName)
            assert (~isempty(frame));
            
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

