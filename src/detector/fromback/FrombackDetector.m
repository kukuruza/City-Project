% implementation of CarDetectorInterface that allows different detectors for clusters

classdef FrombackDetector < CarDetectorBase
    properties % required for all detetors
        mask;
    end
    properties
        
        % verbose = 0  no info
        %         = 1  how many filtered
        %         = 2  assign car indices to names, print indices at filter
        verbose;
        
        % debugging
        %disable removing cars after filtering
        noFilter = false;
        % make sure that mask is actually updated. See subtract() function
        maskDebug = [];
        
        background;
        sizeMap;

        Heght2WidthLimits = [0.5 1.2];
        %SparseDist = 0.0;
        DensitySigma = 0.7;
        DensityRatio = 2.0;
        DistToBorder = 20;
        ExpandPerc = 0.0;

    end % properties
    methods (Hidden)
        
        function indices = findByStatus (~, statuses, name)
            indices = find(not(cellfun('isempty', strfind(statuses, name))));
        end
        
        function indices = filterByStatus (~, statuses, name)
            indices = find(cellfun('isempty', strfind(statuses, name)));
        end
        
        
        % filter by bbox proportions
        function statuses = filterByProportion (CD, cars, statuses)
            for i = 1 : length(cars)
                if ~strcmp(statuses{i}, 'ok'), continue, end
                proportion = double(cars(i).bbox(4)) / double(cars(i).bbox(3));
                if proportion < CD.Heght2WidthLimits(1) || proportion > CD.Heght2WidthLimits(2)
                    if CD.verbose > 1
                        fprintf ('    car %d - bad ratio %f\n', i, proportion); 
                    end
                    statuses{i} = 'bad ratio';
                end
            end
        end

        
        function result = filterOnce (~, mask, center, sz, kernel)
            assert (ismatrix(mask));
            mask = double(mask);
            kernel = kernel (max(1, sz-center(1)+2) : min(sz*2+1, sz+1+size(mask,1)-center(1)), ...
                             max(1, sz-center(2)+2) : min(sz*2+1, sz+1+size(mask,2)-center(2)));
            mask = mask (max(1, center(1)-sz) : min(center(1)+sz, size(mask,1)), ...
                         max(1, center(2)-sz) : min(center(2)+sz, size(mask,2)));
            result = mask .* kernel;
            %imagesc(result);
            %colormap('gray')
            %pause;
            result = sum(result(:));
        end

        
        function statuses = filterBySparsity (CD, mask, cars, statuses)
            parser = inputParser;
            addRequired(parser, 'mask', @(x) islogical(x) && ismatrix(x));
            addRequired(parser, 'cars', @(x) isempty(x) || isa(x, 'Car'));
            addRequired(parser, 'statuses', @(x) isvector(x));
            parse (parser, mask, cars, statuses);

            whites = ones(size(mask,1),size(mask,2));
            for i = 1 : length(cars)
                center = cars(i).getCenter();
                sigma = (cars(i).bbox(3) + cars(i).bbox(4)) / 2 * CD.DensitySigma;
                sz = floor(sigma * 2.5);
                gaussKernel = fspecial('gaussian', sz * 2 + 1, sigma);
                
                roi = cars(i).getROI();
                maskInside = zeros (size(mask,1), size(mask,2));
                maskInside(roi(1):roi(3), roi(2):roi(4)) = mask(roi(1):roi(3), roi(2):roi(4));
                insideResponse = CD.filterOnce (maskInside, center, sz, gaussKernel);
                whitesInside = zeros (size(whites,1), size(whites,2));
                whitesInside(roi(1):roi(3), roi(2):roi(4)) = 1;
                insideNorm = CD.filterOnce (whitesInside, center, sz, gaussKernel);
                assert (insideNorm ~= 0);
                insideDensity = insideResponse / insideNorm;
                %fprintf ('insideDensity %f, insideNorm %f\n', insideDensity, insideNorm);

                roi = cars(i).getROI();
                maskOutside = mask;
                maskOutside(roi(1):roi(3), roi(2):roi(4)) = 0;
                outsideResponse = CD.filterOnce (maskOutside, center, sz, gaussKernel);
                whitesOutside = whites;
                whitesOutside(roi(1):roi(3), roi(2):roi(4)) = 0;
                outsideNorm = CD.filterOnce (whitesOutside, center, sz, gaussKernel);
                assert (outsideNorm ~= 0);
                outsideDensity = outsideResponse / outsideNorm;
                %fprintf ('outsideDensity %f, outsideNorm %f\n', outsideDensity, outsideNorm);
                
                density = insideDensity / outsideDensity;
%                 if CD.verbose > 1
%                     fprintf ('    car %d - density %f\n', i, density); 
%                 end
                if density < CD.DensityRatio
                    if CD.verbose > 1
                        fprintf ('    car %d - density %f\n', i, density); 
                    end
                    statuses{i} = 'too dense';
                end
            end
        end
        
        
%         % filter too dense cars in the image
%         function statuses = filterBySparsity (CD, cars, statuses)
%             for i = 1 : length(cars)
%                 center = cars(i).getCenter(); % [y x]
%                 expectedSize = CD.sizeMap(center(1), center(2));
%                 for k = 1 : length(cars)
%                     if ~strcmp(statuses{i}, 'ok'), continue, end
%                     if i ~= k && dist(center, cars(k).getCenter()') < expectedSize * CD.SparseDist
%                         if CD.verbose > 1, fprintf ('    car %d - too dense\n', i); end
%                         statuses{i} = 'too dense'; 
%                         break
%                     end
%                 end
%             end
%         end
        
        
        % filter too dense cars in the image
%         function statuses = filterBySparsity2 (CD, cars, statuses)
%             for i = 1 : length(cars)
%                 pdf = normpdf
%         end
        
        % filter those too close to the border
        function statuses = filterByBorder (CD, cars, statuses)
            % need at least DistToBorder pixels to border
            sz = size(CD.sizeMap);
            for i = 1 : length(cars)
                if ~strcmp(statuses{i}, 'ok'), continue, end
                roi = cars(i).getROI();
                distToBorder = min([roi(1:2), sz(1)-roi(3), sz(2)-roi(4)]);
                if distToBorder < CD.DistToBorder
                    if CD.verbose > 1, 
                        fprintf ('    car %d - too close to border = %d\n', i, distToBorder); 
                    end
                    statuses{i} = 'close to border'; 
                end
            end
        end
        
    end
    methods
        
        function CD = FrombackDetector (geometry, background, varargin)
            parser = inputParser;
            addRequired(parser, 'geometry', @(x) isa(x, 'GeometryInterface'));
            addRequired(parser, 'background', @(x) isa(x, 'BackgroundGMM'));
            addParameter(parser, 'verbose', 0, @isscalar);
            parse (parser, geometry, background, varargin{:});
            parsed = parser.Results;
            
            CD.verbose = parsed.verbose;
            CD.sizeMap = geometry.getCameraRoadMap();
            CD.background = background;
            
            CD.mask = CD.sizeMap > 0;
        end

        
        function mask = getMask(CD, varargin)
            mask = CD.mask;
        end

        
        function setVerbosity (CD, verbose)
            CD.verbose = verbose;
        end

        
        function cars = detect (CD, img)
            parser = inputParser;
            addRequired(parser, 'img', @iscolorimage);
            parse (parser, img);

            if CD.verbose > 1, fprintf ('FrombackDetector\n'); end

            % ASSUME that background already processed this frame
            % TODO: remove this assumption somehow
            foregroundMask = CD.background.result;
            bboxes = CD.background.mask2bboxes(foregroundMask);

            % debug: background has to be attached to a frombackDetector,
            %        otherwise the it will always return the same mask.
            %        Make sure the mask is different
            assert (isempty(CD.maskDebug) || any(foregroundMask(:) ~= CD.maskDebug(:)));
            CD.maskDebug = foregroundMask;
            %imshow(foregroundMask);
            %pause;
                     
            N = size(bboxes,1);
            cars = Car.empty;
            statuses = cell(N,1);
            for i = 1 : N
                cars(i) = Car(bboxes(i,:));
                cars(i).name = sprintf ('%d', i);
                cars(i).segmentMask = cars(i).extractPatch(foregroundMask);
                statuses{i} = 'ok';
            end
            cars = cars';
            %     mask = imerode (mask, strel('disk', 2));
            %     mask = imdilate(mask, strel('disk', 2));

             % expand boxes
            for i = 1 : N
                cars(i).bbox = expandBboxes (cars(i).bbox, CD.ExpandPerc, img);
            end
            
            % filter by size
            if ~CD.noFilter
                cars = CD.filterCarsBySize (cars, CD.sizeMap, 'verbose', CD.verbose);
            end
            
            % filters specific for backimagedetector
            if ~CD.noFilter
                statuses = CD.filterByProportion (cars, statuses);
                statuses = CD.filterBySparsity (foregroundMask, cars, statuses);
                %statuses = CD.filterByBorder (cars, statuses);
            end
            
            if CD.verbose
                fprintf ('FrombackDetector\n');
                fprintf ('    filtered bad size:     %d\n', ...
                    length(CD.findByStatus(statuses, 'bad size')));
                fprintf ('    filtered proportions:  %d\n', ...
                    length(CD.findByStatus(statuses, 'bad ratio')));
                fprintf ('    filtered too dense:    %d\n', ...
                    length(CD.findByStatus(statuses, 'too dense')));
                fprintf ('    filtered close border: %d\n', ...
                    length(CD.findByStatus(statuses, 'close to border')));
                fprintf ('    left ok:               %d\n', ...
                    length(CD.findByStatus(statuses, 'ok')));
            end

            % filter bad cars
            cars (CD.filterByStatus(statuses, 'ok')) = [];
        end

    end % methods
end
