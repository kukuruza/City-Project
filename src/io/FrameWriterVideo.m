% An implementation of FrameWriter for writing frames to a video
%   It implements an interface writeNextFrame()
%
% This class takes multiple images and puts them together in a grid
%   as specified by layout
%
% It is essentially a wrapper of vision.VideoWriter
%
% (based on Lynna's createAVI.m code)
%


classdef FrameWriterVideo < FrameWriter
    properties (Hidden)
        FIG_NUM = 314159265; % random unlikely number
        
        layout = [1 1] % images grid in a frame. [nrows, ncols]
        video          % output
        counter = 0    % to know how much was written
        framesz        % for debugging
    end % properties
    methods
        function FW = FrameWriterVideo (videopath, framerate)
            FW.video = VideoWriter(videopath);
            FW.video.FrameRate = framerate;
            open(FW.video);
            
            % figure for output
            figure ()
        end
        % accepts one image (if layout == 1) or cell array of images
        function writeNextFrame(FW, images)
            assert (~isempty(images));
            if iscell(images)
                assert (length(images) == FW.layout(1) * FW.layout(2));
                nrows = FW.layout(1);
                ncols = FW.layout(2);
                currentFigure = gcf;
                figure (FW.FIG_NUM);
                for row = 1 : nrows
                    for col = 1 : ncols
                        i = (row-1) * ncols + col;
                        subplot(nrows, ncols, i);
                        imshow(images{i});
                    end
                end
                F = getframe(gcf);
                frame = image(F.cdata);
                imshow(frame);
                error('');
                figure(currentFigure);
            else
                frame = images;
            end
%        function writeNextFrame(FW, frame)
            if isempty(FW.framesz), FW.framesz = size(frame); end
            if ndims(frame) ~= length(FW.framesz) || any(size(frame) ~= FW.framesz)
                FW.framesz
                size(frame)
                error('frame size changed');
            end
            writeVideo (FW.video, frame);
            FW.counter = FW.counter + 1;
        end
        function delete(FW)
            fprintf('FrameWriterVideo: %d frames written.\n', FW.counter);
            close (FW.video);
        end

    end % methods
end

