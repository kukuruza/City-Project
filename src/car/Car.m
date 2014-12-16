% This class is primarily for halping CarDetector classes to provide
%   more verbose output: besides the bounding box, the class may store
%   any additional information like size, orientation, etc.
%

classdef Car < CarInterface
    properties
        bbox;  % [x1 y1 width height]
        patch = [];
        segmentMask;
        
        % parameters
        timeStamp; % time of the frame. [yyyy mm dd hh mm ss]. sec. is float
        orientation; % to be determined
        
        % descriptors
        feature = [];
        histHog = [];
        histCol = [];
        color = [];
        
    end % propertioes
    methods (Static)
        
        % if pcaCoef and pcaOffset are not loaded then load. Else fetch them
        function [pcaCoeffOut, pcaOffsetOut] = getModelPCA()
            persistent pcaColorCoeff;
            persistent pcaColorOffset;
            if isempty(pcaColorCoeff) || isempty(pcaColorOffset)
                assert (exist('pcaColor.mat', 'file') > 0);
                assert (exist('pcaHog.mat', 'file') > 0);
                load ('pcaColor.mat');
                load ('pcaHog.mat');
                pcaColorCoeff = coeff;
                pcaColorOffset = offset;
                fprintf ('Car.getModelPCA(): loaded model from file.\n');
            end
            pcaCoeffOut = pcaColorCoeff;
            pcaOffsetOut = pcaColorOffset;
        end
        
    end
    methods
        function C = Car (bbox, timestamp)
            C.bbox = bbox;
            
            if nargin < 2
                % assigning a default value to timeStamp
                C.timeStamp = [0 0 0 0 0 0];
            else
                C.timeStamp = timestamp;
            end
        end
        
        
        function roi = getROI (C)  % [y1, x1, y2, x2]
            roi = [C.bbox(2) C.bbox(1) C.bbox(4)+C.bbox(2)-1 C.bbox(3)+C.bbox(1)-1];
        end
        
        
        % this function must be called after C.patch is set
        function segmentPatch (C, image)
            assert (~isempty(C.patch));
            
            % actual segmentation
            UnariesOffset = 0.4;
            EdgeWeight = 0.2;
            mask = segmentWrapper(C.patch, UnariesOffset, EdgeWeight);
            
            % remove small artefacts from mask
            ArtefactSize = 5;
            mask = bwareaopen (mask, ArtefactSize^2);
            C.segmentMask = mask;
%             roi = mask2roi(mask);
%             mask = mask(roi(1) : roi(3), roi(2) : roi(4));
%             C.bbox = [C.bbox(1), C.bbox(2), 0, 0] + ...
%                      [roi(2), roi(1), roi(4)-roi(2)+1, roi(3)-roi(1)+1];

%             % expand bbox
%             ExpandPerc = 0.2;
%             oldBbox = C.bbox;
%             C.bbox = expandBboxes (C.bbox, ExpandPerc, image);
%             offsets = oldBbox - C.bbox;
%             roi = C.getROI();
% 
%             % enlarge
%             C.patch = image(roi(1) : roi(3), roi(2) : roi(4), :);
%             C.segmentMask = zeros (C.bbox(4), C.bbox(3));
%             C.segmentMask (offsets(2) + 1 : offsets(2) + oldBbox(4), ...
%                            offsets(1) + 1 : offsets(1) + oldBbox(3)) = mask;
        end
        
                        
        function patch = extractPatch (C, image)
            roi = C.getROI();
            C.patch = image(roi(1) : roi(3), roi(2) : roi(4), :);
            patch = C.patch;
            C.segmentMask = ones (size(patch,1), size(patch,2));
        end
        
        
        function generateHogFeature (C)
            assert (~isempty(C.patch)); % must call C.extractPatch() before
            
            % Hog Feature
            HOG = vl_hog(single(imresize(C.patch, [36 36])), 12);
            C.histHog = reshape(HOG, 1, numel(HOG));
            % normalize, better for all probabilistic methods
            %C.histHog = C.histHog / sum(C.histHog(:)) * numel(HOG); 
        end
        
        
        function generateColorHistFeature (C)
            assert (~isempty(C.patch)); % must call C.extractPatch() before
            
            n_bins=4;
            edges=(0:(n_bins-1))/n_bins;
            histogramCol=zeros(n_bins,n_bins,n_bins);
            C.histCol=zeros(n_bins,n_bins,n_bins);
            
            IR=imresize(C.patch,[64 48]);
            IR=im2double(IR);
            [~,r_bins] = histc(reshape(IR(:,:,1),1,[]),edges); r_bins = r_bins + 1;
            [~,g_bins] = histc(reshape(IR(:,:,1),1,[]),edges); g_bins = g_bins + 1;
            [~,b_bins] = histc(reshape(IR(:,:,1),1,[]),edges); b_bins = b_bins + 1;
            
            for j=1:numel(r_bins)
                histogramCol(r_bins(j),g_bins(j),b_bins(j)) = histogramCol(r_bins(j),g_bins(j),b_bins(j)) + 1;
            end
            % normalize, better for all probabilistic methods
            C.histCol = reshape(histogramCol,1,[]) / sum(histogramCol(:));
        end

        
        function generateSingleColorFeature (C)
            assert (~isempty(C.patch)); % must call C.extractPatch() before
            % Color Feature
            rCh = C.patch(:,:,1);
            r = mean(mean(rCh(C.segmentMask)));
            gCh = C.patch(:,:,2);
            g = mean(mean(gCh(C.segmentMask)));
            bCh = C.patch(:,:,3);
            b = mean(mean(bCh(C.segmentMask)));
            C.color = [r g b] / 255;
        end
        
        
        % transform according to pre-learned PCA
        function [histHog, histCol] = reduceDimensions(C)
            [hogCoeff, hogOffset] = C.getModelPCA();
            %size(C.histHog)
            %size(hogCoeff)
            %size(hogOffset)
            histHog = (C.histHog - hogOffset) * hogCoeff;
            histCol = [];
            %[colorCoeff, colorOffset] = C.getModelPCA();
            %histCol = C.histCol * colorCoeff + colorOffset;
        end
        
        
        % choose here which features you like
        function generateFeature (C)
            C.generateHogFeature();
            C.generateColorHistFeature();
            C.generateSingleColorFeature();
        end
        
        
        function center = getCenter (C) % [y x]
            center = [int32(C.bbox(2) + C.bbox(4) / 2), ...
                      int32(C.bbox(1) + C.bbox(3) / 2)];
        end
        
        
        function center = getBottomCenter (C) % [y x]
            center = [int32(C.bbox(2) + C.bbox(4) - 1), ...
                      int32(C.bbox(1) + C.bbox(3) / 2)];
        end
        
        
        function im = drawCar (C, im, color, tag)
            if nargin < 3, color = 'yellow'; end
            if nargin < 4, tag = 'car'; end
            if nargin < 5, boxOpacity = 0.6; end
            if boxOpacity > 0.5
                textColor = 'black';
            else
                textColor = 'white';
            end
            %color = 128 + rand(1,3) * 127;
            im = insertObjectAnnotation(im, 'rectangle', C.bbox, ...
                tag, 'Color', color, ...
                'TextBoxOpacity', boxOpacity, 'TextColor', textColor, ...
                'FontSize', 12);
        end
        
    end % methods
end
