% implementation of CarDetectorInterface that allows different detectors for clusters

classdef FrombackDetector < CarDetectorInterface
    properties
        
        doFilter = true;
        verbose = 1;
        
        background;
        sizeMap;

        SizeTolerance = 1.5;
        Heght2WidthLimits = [0.5 1.2];
        SparseDist = 0.0;
        DistToBorder = 20;
        ExpandPerc = 0.15;

    end % properties
    methods (Hidden)
        
        function indices = findByStatus (~, statuses, name)
            indices = find(not(cellfun('isempty', strfind(statuses, name))));
        end
        
        
        % filter by sizes (size is sqrt of area)
        function statuses = filterBySize (CD, cars, statuses)
            for i = 1 : length(cars)
                center = cars(i).getBottomCenter(); % [y x]
                expectedSize = CD.sizeMap(center(1), center(2));
                actualSize = sqrt(single(cars(i).bbox(3) * cars(i).bbox(4)));
                if actualSize < expectedSize / CD.SizeTolerance || ...
                   actualSize > expectedSize * CD.SizeTolerance
                    statuses{i} = 'bad size';
                end
            end
        end
        
        
        % filter by bbox proportions
        function statuses = filterByProportion (CD, cars, statuses)
            for i = 1 : length(cars)
                proportion = cars(i).bbox(4) / double(cars(i).bbox(3));
                if proportion < CD.Heght2WidthLimits(1) || proportion > CD.Heght2WidthLimits(2)
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
                    if i ~= k && dist(center, cars(k).getCenter()') < expectedSize * CD.SparseDist
                        statuses{i} = 'too dense'; 
                        break
                    end
                end
            end
        end
        
        
        % filter those too close to the border
        function statuses = filterByBorder (CD, cars, statuses)
            % need at least DistToBorder pixels to border
            for i = 1 : length(cars)
                roi = cars(i).getROI();
                if min([roi(1:2), size(frame,1)-roi(3), size(frame,2)-roi(4)]) > CD.DistToBorder
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
            
            CD.sizeMap = geometry.getRoadMask();
            CD.background = background;
        end

        
        function mask = getMask(CD, varargin)
            mask = CD.sizeMap > 0;
        end

        
        function cars = detect (CD, img, mask, varargin)
            parser = inputParser;
            addRequired(parser, 'img', @iscolorimage);
            addRequired(parser, 'mask', @(x) ismatrix(x) && islogical(x));
            parse (parser, img, mask, varargin{:});
            assert (all(size(mask) == size(CD.sizeMap)));
            
            bboxes = CD.background.mask2bboxes(mask);

            N = size(bboxes,1);
            cars = Car.empty;
            statuses = cell(N,1);
            for i = 1 : N
                cars(i) = Car(bboxes(i,:));
                cars(i).segmentMask = cars(i).extractPatch(mask);
                statuses{i} = 'ok';
            end
            %     mask = imerode (mask, strel('disk', 2));
            %     mask = imdilate(mask, strel('disk', 2));

            if CD.doFilter
                statuses = CD.filterBySize (cars, statuses);
                statuses = CD.filterByProportion (cars, statuses);
                statuses = CD.filterBySparsity (cars, statuses);
                statuses = CD.filterByBorder (cars, statuses);
            end
            
            % expand boxes
            for i = 1 : N
                cars(i).bbox = expandBboxes (cars(i).bbox, CD.ExpandPerc, img);
            end
            
            if CD.verbose
                fprintf ('FrombackDetector filtered bad size:     %d\n', ...
                    length(CD.findByStatus(statuses, 'bad size')));
                fprintf ('FrombackDetector filtered proportions:  %d\n', ...
                    length(CD.findByStatus(statuses, 'bad ratio')));
                fprintf ('FrombackDetector filtered too dense:    %d\n', ...
                    length(CD.findByStatus(statuses, 'too dense')));
                fprintf ('FrombackDetector filtered close border: %d\n', ...
                    length(CD.findByStatus(statuses, 'close to border')));
                fprintf ('FrombackDetector left ok:               %d\n', ...
                    length(CD.findByStatus(statuses, 'ok')));
            end

            % filter bad cars
            cars (~CD.findByStatus(statuses, 'ok')) = [];
    
        end

    end % methods
end
