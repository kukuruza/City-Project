% An implementation of FrameWriter for writing frames to a set of images
%   It implements an interface writeNextFrame()
%
% This class takes multiple images and puts them together in a grid
%   as specified by layout
%
% It is essentially a wrapper of vision.VideoWriter
%
% (based on Lynna's createAVI.m code)
%


classdef FrameWriterImages < FrameWriter
    properties (Hidden)
        ext = '.jpg';
        layout = [1 1] % images grid in a frame. [nrows, ncols]
        imDir          % output
        counter = 0    % to know how much was written
        framesz        % for debugging
    end % properties
    methods
        
        function FW = FrameWriterImages (imDir, layout, ext)
            if ~exist(imDir, 'dir')
                fprintf ('FrameWriterImages: imDir: %s\n', imDir);
                error ('FrameWriterImages: imDir does not exist');
            end
            FW.imDir = imDir;
            FW.layout = layout;
            FW.ext = ext;
        end
        
        % accepts one image (if layout == 1) or cell array of images
        function writeNextFrame(FW, images)
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'images', @(x) iscell(x) || ismatrix(x) || ndims(x) == 3 && size(x,3) == 3); % TODO: replace with iscolorimage when merged backDetector
            parse (parser, images);
            assert (~iscell(images) || length(images) == FW.layout(1) * FW.layout(2));

            nrows = FW.layout(1);
            ncols = FW.layout(2);
            if ~iscell(images)
                frame = images;
            elseif nrows == 1 && ncols == 1
                frame = images{1};
            elseif nrows == 2 && ncols == 1
                frame = [images{1}; images{2}];
            elseif nrows == 1 && ncols == 2
                frame = [images{1}, images{2}];
            elseif nrows == 1 && ncols == 3
                frame = [images{1}, images{2}, images{3}];
            elseif nrows == 3 && ncols == 1
                frame = [images{1}; images{2}; images{3}];
            elseif nrows == 2 && ncols == 2
                frame = [images{1}, images{2}; images{3}, images{4}];
            else
                assert (0);
            end

            imPath = fullfile(FW.imDir, [sprintf('%06d', FW.counter) FW.ext]);
            imwrite(frame, imPath);

            FW.counter = FW.counter + 1;
        end
        
    end % methods
end

