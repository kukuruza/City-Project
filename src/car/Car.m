% This class is primarily for halping CarDetector classes to provide
%   more verbose output: besides the bounding box, the class may store
%   any additional information like size, orientation, etc.
%

classdef Car < CarInterface
    properties
        bbox;  % [x1 y1 width height]
        patch = [];
        
        % features
        timeStamp; % the time the frame was taken. [yyyy mm dd hh mm ss]. sec. is float
        feature = [];
        histHog = [];
        histCol = [];
        
    end % propertioes
    methods
        function C = Car (bbox, timestamp)
            C.bbox = bbox;
            
            if (nargin < 2)
                % assigning a default value to timeStamp
                C.timeStamp = [];
            else
                C.timeStamp = timestamp;
            end
        end
        
        
        function roi = getROI (C)  % [y1, x1, y2, x2]
            roi = [C.bbox(2) C.bbox(1) C.bbox(4)+C.bbox(2)-1 C.bbox(3)+C.bbox(1)-1];
        end
        
        
        function patch = extractPatch (C, image)
            roi = C.getROI();
            C.patch = image(roi(1) : roi(3), roi(2) : roi(4), :);
            patch = C.patch;
        end
        
        
        function generateFeature (C, image)
            
            carPatch = C.extractPatch(image);
            
            % Hog Feature
            carRe = imresize(carPatch,[32 24]);   % [64 48] is too large
            HOG = vl_hog(single(carRe), 2);
            m = numel(HOG);
            feat = reshape(HOG, 1, m);
            C.histHog = zeros(m);
            C.histHog = feat/ sum(feat(:)); % normalize, better for all probabilistic methods
            
            % Color Feature
            n_bins=4;
            edges=(0:(n_bins-1))/n_bins;
            histogramCol=zeros(n_bins,n_bins,n_bins);     
            C.histCol=zeros(n_bins,n_bins,n_bins);
        
            IR=imresize(carPatch,[64 48]);
            IR=im2double(IR);
            [~,r_bins] = histc(reshape(IR(:,:,1),1,[]),edges); r_bins = r_bins + 1;
            [~,g_bins] = histc(reshape(IR(:,:,1),1,[]),edges); g_bins = g_bins + 1;
            [~,b_bins] = histc(reshape(IR(:,:,1),1,[]),edges); b_bins = b_bins + 1;
            
            for j=1:numel(r_bins)
                histogramCol(r_bins(j),g_bins(j),b_bins(j)) = histogramCol(r_bins(j),g_bins(j),b_bins(j)) + 1;
            end
            C.histCol= reshape(histogramCol,1,[]) / sum(histogramCol(:)); % normalize, better for all probabilistic methods
                      
        end
        
        
        function center = getCenter (C) % [y x]
            center = [int32(C.bbox(2) + C.bbox(4) / 2), ...
                int32(C.bbox(1) + C.bbox(3) / 2)];
        end
        
        
        function im = drawCar (C, im, color, tag, boxOpacity)
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
