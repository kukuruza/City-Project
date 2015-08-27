% An implementation of FrameWriter for writing frames to a video
%   It implements an interface step()
%
% It is essentially a wrapper of vision.VideoWriter
%
% (based on Lynna's createAVI.m code)
%


classdef FrameWriterVideo < FrameWriter
    properties (Hidden)
        video          % output
        counter = 0    % to know how much was written
    end % properties
    methods
        
        function FW = FrameWriterVideo (videopath, framerate)
            FW.video = VideoWriter(videopath);
            FW.video.FrameRate = framerate;
            open(FW.video);
        end
        
        function step (FW, frame)
            assert (~isempty(frame));
            writeVideo (FW.video, frame);
            FW.counter = FW.counter + 1;
        end
        
        function delete(FW)
            close (FW.video);
        end

    end % methods
end

