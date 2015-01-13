% implementation of CarDetectorInterface that allows different detectors for clusters

classdef FrombackDetector < CarDetectorInterface
    properties % required for all detetors
        mask;
    end
    properties
        
        % debugging - disable removing cars after filtering
        noFilter = false;
        
        % verbose = 0  no info
        %         = 1  how many filtered
        %         = 2  assign car indices to names, print indices at filter
        verbose = 2;
        
        background;
        sizeMap;

        SizeLimits = [0.7 1.7];
        Heght2WidthLimits = [0.5 1.2];
        SparseDist = 0.0;
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
        
        
        % filter by sizes (size is sqrt of area)
        function statuses = filterBySize (CD, cars, statuses)
            for i = 1 : length(cars)
                if ~strcmp(statuses{i}, 'ok'), continue, end
                center = cars(i).getBottomCenter(); % [y x]
                expectedSize = CD.sizeMap(center(1), center(2));
                actualSize = sqrt(single(cars(i).bbox(3) * cars(i).bbox(4)));
                if actualSize < expectedSize * CD.SizeLimits(1) || ...
                   actualSize > expectedSize * CD.SizeLimits(2)
                    if CD.verbose > 1
                        fprintf ('    car %d - bad size %f, expect %f\n', i, actualSize, expectedSize); 
                    end
                    statuses{i} = 'bad size';
                end
            end
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
        
        
        % filter too dense cars in the image
        function statuses = filterBySparsity (CD, cars, statuses)
            for i = 1 : length(cars)
                center = cars(i).getCenter(); % [y x]
                expectedSize = CD.sizeMap(center(1), center(2));
                for k = 1 : length(cars)
                    if ~strcmp(statuses{i}, 'ok'), continue, end
                    if i ~= k && dist(center, cars(k).getCenter()') < expectedSize * CD.SparseDist
                        if CD.verbose > 1, fprintf ('    car %d - too dense\n', i); end
                        statuses{i} = 'too dense'; 
                        break
                    end
                end
            end
        end
        
        
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
        
        function CD = FrombackDetector (geometry, background)
            parser = inputParser;
            addRequired(parser, 'geometry', @(x) isa(x, 'GeometryInterface'));
            addRequired(parser, 'background', @(x) isa(x, 'BackgroundGMM'));
            parse (parser, geometry, background);
            %parsed = parser.Results;
            
            CD.sizeMap = geometry.getCameraRoadMap();
            CD.background = background;
            
            CD.mask = CD.sizeMap > 0;
        end

        
        function mask = getMask(CD, varargin)
            mask = CD.mask;
        end

        
        function cars = detect (CD, img)
            parser = inputParser;
            addRequired(parser, 'img', @iscolorimage);
            parse (parser, img);
            
            % ASSUME that background already processed this frame
            % TODO: remove this assumption somehow
            foregroundMask = CD.background.result;
            bboxes = CD.background.mask2bboxes(foregroundMask);

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

            statuses = CD.filterBySize (cars, statuses);
            statuses = CD.filterByProportion (cars, statuses);
            statuses = CD.filterBySparsity (cars, statuses);
            %statuses = CD.filterByBorder (cars, statuses);
            
            % expand boxes
            for i = 1 : N
                cars(i).bbox = expandBboxes (cars(i).bbox, CD.ExpandPerc, img);
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
            if ~CD.noFilter
                cars (CD.filterByStatus(statuses, 'ok')) = [];
            end 
    
        end

    end % methods
end
