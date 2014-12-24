% This class is for descriptors of cars
%

classdef Panda < Car
    properties
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
        function C = Panda (car)
            C = C@Car([-1 -1 -1 -1]);
            C.bbox = car.bbox;
            C.patch = car.patch;
            C.segmentMask = car.segmentMask; 
            C.timeStamp = car.timeStamp;
            C.orientation = car.orientation;
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
        
    end % methods
end

