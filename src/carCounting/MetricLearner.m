% Metric learning method for identifying same cars

classdef MetricLearner < handle
    properties (Hidden)
        framecounter = 0;
        seenCars = {};   % cars from previous frames
    end % properties
    methods
        function ML = MetricLearner()
            
            ML.framecounter = 0;
            ML.seenCars  = {};
            % a = 1
        
        end
        
        
        function [ProbCol, ProbHOG] = AppProb (ML, patch1, patch2)
            % HOG
            % run('C:\Users\Shaolong\Documents\MATLAB\vlfeat-0.9.19\toolbox\vl_setup.m');
            %run('vlfeat-0.9.19/toolbox/vl_setup.m');
            
            carRe1 = imresize(patch1,[64 48]);
            carRe2 = imresize(patch2,[64 48]);
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
            
            
            IR=imresize(patch1,[64 48]);
            IR=im2double(IR);         
            [~,r_bins] = histc(reshape(IR(:,:,1),1,[]),edges); r_bins = r_bins + 1;
            [~,g_bins] = histc(reshape(IR(:,:,1),1,[]),edges); g_bins = g_bins + 1;
            [~,b_bins] = histc(reshape(IR(:,:,1),1,[]),edges); b_bins = b_bins + 1;
            
            for j=1:numel(r_bins)
                histogram1(r_bins(j),g_bins(j),b_bins(j)) = histogram1(r_bins(j),g_bins(j),b_bins(j)) + 1;
            end
            histograms1= reshape(histogram1,1,[]) / sum(histogram1(:)); % normalize, better for all probabilistic methods
            
            IR=imresize(patch2,[64 48]);
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
            
            
        function [newCarNumber, Match, NewIndex] = processFrame (ML, iframe, image, cars, geometryObj)
            if (iframe == 1)
                newCarNumber = 0;
                ML.seenCars{iframe} = cars;
                ML.framecounter = 1;
                Match = 1;
                return
            end
                
            % validation of arguments
            % color image
            assert (ndims(image) == 3 && size(image,3) == 3);
            % usual vector instead of cell array
            if ~isempty(cars), assert (~iscell(cars) && isvector(cars)); end
            % car is an object of class Car
            if ~isempty(cars), assert (isa(cars(1), 'Car')); end
                    
            ML.framecounter = ML.framecounter + 1;
            seen = ML.seenCars{iframe-1};

            %size(cars)
            %size(seen)
            % extract features
            % for car = cars
            %     car.generateFeature (image);
            % end
            
            
            
            % compute matching probability between each in the new frame and each car in the former frames; construct similarity matrix with seen cars
          
            % probability of geometry
            ProbCol = zeros(length(cars), length(seen));
            ProbHOG = zeros(length(cars), length(seen));
            ProbWeighted = zeros(length(cars), length(seen));
            
 
            for i = 1 : length(cars)
                car = cars(i);      % all the cars in new frame
                for j = 1 : length(seen)
                    seenCar = seen(j);   % all the cars in former frame                
                    ProbGeo(i,j) = geometryObj.getMutualProb(seenCar, car, 1);  % seen car should be the first arguement
                    % seenCarapp
                    % pause()
                    
                    %probMap = geometryObj.generateProbMap(seenCarapp, 1, image);
                    %imshow(probMap)
                    %pause()
                    fprintf('Prob : %f\n', ProbGeo(i,j));
                    [ProbCol(i,j), ProbHOG(i,j)] = ML.AppProb(car.patch, seenCar.patch);
                    % ProbCol(i,j) = 0.5;
                    % ProbHOG(i,j) = 0.5;
                    ProbWeighted(i,j) = 0.5*100*ProbGeo(i,j) + 0.3*ProbCol(i,j) + 0.2*ProbHOG(i,j);
                end
            end
           
            % build the match matrix
            Match = zeros(size(ProbWeighted));
            NewIndex = zeros(length(cars), 1);
            for k = 1: length(cars)
                [maxProb, index] = max(ProbWeighted(k,:));
                if(maxProb>0.8)
                    Match(k,index) = 1;
                    NewIndex(k)= 1;
                else
                    NewIndex(k)= 0;
                end
            end
            % compute new car number
            CountMatch = sum(sum(Match));
            newCarNumber = length(cars) - CountMatch;    
            ML.seenCars{iframe} = cars;
            
            %fileGeoProb = strcat('GeoProb', num2str(iframe));
            %save(fileGeoProb, 'ProbGeo');
            %fileMatch = strcat('Match', num2str(iframe));
            %save(fileMatch, 'Match');
            % element-wise operation to come up with a single matrix
            % constraints = GeoProb .* appearConstraints;
            
            % vl_hog(single(patch),1);
                       
            % == bookkeeping ==
            
            % prune the seen list and remove too old cars from there
            % for appearCar = ML.seenAppearCars find iFrame > ...
            
            % put the new cars into the list
        end
    end % methods
end