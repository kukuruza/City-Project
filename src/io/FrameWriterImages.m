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
        FIG_NUM = 314159265; % random unlikely number
        
        ext = '.jpg';
        layout = [1 1] % images grid in a frame. [nrows, ncols]
        imDir          % output
        counter = 0    % to know how much was written
        framesz        % for debugging
    end % properties
    methods
        
        function FW = FrameWriterImages (imDir, layout, ext)
            if ~exist(imDir, 'file') % TODO: add: or it is not a folder
                fprintf ('FrameWriterImages: imDir: %s\n', imDir);
                error ('FrameWriterImages: imDir does not exist');
            end
            FW.imDir = imDir;
            FW.layout = layout;
            FW.ext = ext;
            
            % figure preparation
            addpath export_fig
            figure (FW.FIG_NUM);
            set (FW.FIG_NUM,'units','normalized','outerposition',[0 0 1 1]);
        end
        
        % accepts one image (if layout == 1) or cell array of images
        function writeNextFrame(FW, images)
            assert (~isempty(images));
            if iscell(images)
                assert (length(images) == FW.layout(1) * FW.layout(2));
                nrows = FW.layout(1);
                ncols = FW.layout(2);
                
                % remember the current figure, if any
                if ~isempty(findall(0,'Type','Figure'))
                    currentFigure = gcf;
                    figure (FW.FIG_NUM);
                else
                    currentFigure = figure (FW.FIG_NUM);
                end
                
                for row = 1 : nrows
                    for col = 1 : ncols
                        i = (row-1) * ncols + col;
                        subplot(nrows, ncols, i);
                        imshow(images{i});
                    end
                end
                
                imPath = fullfile(FW.imDir, [sprintf('%06d', FW.counter) FW.ext]);
                export_fig(imPath, gcf);
                
                % switch back to the remembered figure
                figure(currentFigure);
            else
                frame = images;
                imPath = fullfile(FW.imDir, [sprintf('%06d', FW.counter) FW.ext]);
                imwrite(frame, imPath);
            end
            FW.counter = FW.counter + 1;
        end
        
        function delete(FW)
            if ishandle(FW.FIG_NUM), close(FW.FIG_NUM), end
        end

    end % methods
end

