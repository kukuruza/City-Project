% Metric learning method for identifying same cars

classdef MetricLearner < handle
    properties (Hidden)
        framecounter = 0;
        seenCarapps = {};   % cars from previous frames
    end % properties
    methods
        function ML = MetricLearner()
            
            ML.framecounter = 0;
            ML.seenCarapps  = {};
            % a = 1
        
        end
        
        
        function [ProbCol, ProbHOG] = AppProb (ML, car1, car2)
            % HOG
            run('C:\Users\Shaolong\Documents\MATLAB\vlfeat-0.9.19\toolbox\vl_setup.m');
            
            carRe1 = imresize(car1,[64 48]);
            carRe2 = imresize(car2,[64 48]);
            HOG1 = vl_hog(single(carRe1), 4);
            HOG2 = vl_hog(single(carRe2), 4);
            m1 = numel(HOG1);
            m2 = numel(HOG2);
            feat1 = reshape(HOG1, 1, m1);
            feat2 = reshape(HOG2, 1, m2);
            hist1 = zeros(m1);
            hist2 = zeros(m2);
            hist1 = feat1/ sum(feat1(:)); % normalize, better for all probabilistic methods
            hist2 = feat2/ sum(feat2(:));
            
            dHOG = chi_square_statistics(hist1,hist2);
            ProbHOG = 1-dHOG;
            
            % Color          
            n_bins=4;
            edges=(0:(n_bins-1))/n_bins;
            histogram1=zeros(n_bins,n_bins,n_bins);
            histogram2=zeros(n_bins,n_bins,n_bins);
            histograms1=zeros(n_bins,n_bins,n_bins);
            histograms2=zeros(n_bins,n_bins,n_bins);
            
            
            IR=imresize(car1,[64 48]);
            IR=im2double(IR);         
            [~,r_bins] = histc(reshape(IR(:,:,1),1,[]),edges); r_bins = r_bins + 1;
            [~,g_bins] = histc(reshape(IR(:,:,1),1,[]),edges); g_bins = g_bins + 1;
            [~,b_bins] = histc(reshape(IR(:,:,1),1,[]),edges); b_bins = b_bins + 1;
            
            for j=1:numel(r_bins)
                histogram1(r_bins(j),g_bins(j),b_bins(j)) = histogram1(r_bins(j),g_bins(j),b_bins(j)) + 1;
            end
            histograms1= reshape(histogram1,1,[]) / sum(histogram1(:)); % normalize, better for all probabilistic methods
            
            IR=imresize(car2,[64 48]);
            IR=im2double(IR);         
            [~,r_bins] = histc(reshape(IR(:,:,1),1,[]),edges); r_bins = r_bins + 1;
            [~,g_bins] = histc(reshape(IR(:,:,1),1,[]),edges); g_bins = g_bins + 1;
            [~,b_bins] = histc(reshape(IR(:,:,1),1,[]),edges); b_bins = b_bins + 1;
            
            for j=1:numel(r_bins)
                histogram2(r_bins(j),g_bins(j),b_bins(j)) = histogram2(r_bins(j),g_bins(j),b_bins(j)) + 1;
            end
            histograms2= reshape(histogram2,1,[]) / sum(histogram2(:)); % normalize, better for all probabilistic methods
                
            dCol = chi_square_statistics(histograms1,histograms2);
            ProbCol = 1-4*dCol;
        end
            
            
        function [newCarNumber Match] = processFrame (ML, iframe, image, cars, geometryObj)
            if(iframe == 1)
                newCarNumber = 0;
                ML.seenCarapps{iframe} = cars;
                ML.framecounter = 1;
                Match = 1;
            else
                
            % validation of parameters
            assert (ndims(image) == 3);         % color image
            % assert (ismatrix(foregroundMask));  % grayscale mask
            % assert (all([size(image,1) size(image,2)] == size(foregroundMask)));
            % if ~isempty(carcell), assert (isa(carcell(1), 'Car')), end % cars are of class Car
                    
            ML.framecounter = ML.framecounter + 1;
            carapps = cars;
            seen = ML.seenCarapps{iframe-1};

            
            % make CarAppearance objects from Car objects
            %             carapps = [];
            %             for car = cars
            %                 carapp = CarAppearance (car, ML.framecounter);
            %                 carapps = [carapps, carapp];
            %             end
            
            % extract features
            %             for carapp = carapps
            %                 carapp.generateFeature (image, foregroundMask);
            %             end
            
            
            
            % compute matching probability between each in the new frame and each car in the former frames; construct similarity matrix with seen cars
          
            % probability of geometry
            ProbCol = zeros(length(carapps), length(seen));
            ProbHOG = zeros(length(carapps), length(seen));
            ProbWeighted = zeros(length(carapps), length(seen));
            
 
            for i = 1 : length(carapps)
                carapp = carapps{i};      % all the cars in new frame
                for j = 1 : length(seen)
                    seenCarapp = seen{j};   % all the cars in former frame                
                    ProbGeo(i,j) = geometryObj.getMutualProb(seenCarapp, carapp, 3);
                    % seenCarapp
                    % pause()
                    
                    %probMap = geometryObj.generateProbMap(seenCarapp, 1, image);
                    %imshow(probMap)
                    %pause()
                    fprintf('Prob : %f\n', ProbGeo(i,j));
                    [ProbCol(i,j), ProbHOG(i,j)] = ML.AppProb(carapp.feature, seenCarapp.feature);
                    ProbWeighted(i,j) = 0.5*ProbGeo(i,j) + 0.3*ProbCol(i,j) + 0.2*ProbHOG(i,j);
                    
                end
            end
           
            % build the match matrix
            Match = zeros(size(ProbWeighted));
            for k = 1: length(carapps)
                [maxProb, index] = max(ProbWeighted(k,:));
                if(maxProb>0.8)
                    Match(k,index) = 1;
                else
                    Match(k,index) = 0;
                end
            end
            % compute new car number
            CountMatch = sum(sum(Match));
            newCarNumber = length(carapps) - CountMatch;    
            ML.seenCarapps{iframe} = cars;
            
            fileGeoProb = strcat('GeoProb', num2str(iframe));
            save(fileGeoProb, 'ProbGeo');
            fileMatch = strcat('Match', num2str(iframe));
            save(fileMatch, 'Match');
            % element-wise operation to come up with a single matrix
            % constraints = GeoProb .* appearConstraints;
            
            % vl_hog(single(patch),1);
                       
            % == bookkeeping ==
            
            % prune the seen list and remove too old cars from there
            % for appearCar = ML.seenAppearCars find iFrame > ...
            
            % put the new cars into the list
            end
        end
    end % methods
end