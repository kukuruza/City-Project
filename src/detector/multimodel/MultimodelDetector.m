% implementation of CarDetectorInterface that allows different detectors for clusters

classdef MultimodelDetector < CarDetectorInterface
    properties
        
        % do not combine detections from different detectors
        noMerge = false;
        
        clusters   % descriptions of car clusters
        detectors  % detectors for each of the groups
        N          % number of both clusters and detectors
        
        mergeThreshold;
        
        verbose = 1;
        
    end % properties
    methods (Hidden)
        
        function result = areClose (~, bbox1, bbox2, threshold)
            result = false;

            roi1 = bbox2roi(bbox1);
            roi2 = bbox2roi(bbox2);
            inters = [max(roi1(1:2), roi2(1:2)), min(roi1(3:4), roi2(3:4))];
            
            % no intersection case
            if inters(1) > inters(3) || inters(2) > inters(4), return, end
            
            % intersection case
            areaInters = (inters(3) - inters(1) + 1) * (inters(4) - inters(2) + 1);
            if areaInters / min(bbox1(3)*bbox1(4), bbox2(3)*bbox2(4)) > threshold
                result = true;
            end
        end
        
        function [cars1, cars2] = combineTwoClusters(CD, cars1, cars2)
            m = length(cars1) + length(cars2);
            toTrash = [];
            for i1 = 1 : length(cars1)
                for i2 = 1 : length(cars2)
                    if CD.areClose (cars1(i1).bbox, cars2(i2).bbox, CD.mergeThreshold)
                        toTrash = [toTrash i1];
                    end
                end
            end
            cars1(toTrash) = [];
            if CD.verbose, fprintf ('removed %d cars\n', m - length(cars2) - length(cars1)); end
        end
        
        function carsByCluster = combineClustersCars(CD, carsByCluster)
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'carsByCluster', @(x) iscell(x) && (isempty(x{1}) || isa(x{1}, 'Car')));
            parse (parser, carsByCluster);

            for i = CD.N : -1 : 1
                for j = i : CD.N
                    if nnz(CD.detectors{i}.mask & CD.detectors{j}.mask)
                        if CD.verbose
                            fprintf('MultimodelDetector: combining clusters %d and %d... ', i, j);
                        end 
                        [carsByCluster{i}, carsByCluster{j}] = ...
                            CD.combineTwoClusters (carsByCluster{i}, carsByCluster{j});
                    end
                end
            end
        end
        
    end
    methods
        
        function CD = MultimodelDetector (clusters, detectors)
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'clusters', @(x) ~isempty(x));
            addRequired(parser, 'detectors', @(x) ~isempty(x) && iscell(x));
            addParameter(parser, 'mergeThreshold', 0.5, @isscalar);
            parse (parser, clusters, detectors);
            parsed = parser.Results;
            assert (length(parsed.clusters) == length(parsed.detectors));
            for i = 1 : length(detectors), assert(isa(detectors{i}, 'CarDetectorInterface')); end

            CD.clusters = parsed.clusters;
            CD.detectors = parsed.detectors;
            CD.N = length(parsed.clusters);
            CD.mergeThreshold = parsed.mergeThreshold;
        end

        
        function mask = getMask(CD, varargin)
            % parse and validate input
            parser = inputParser;
            addParameter(parser, 'colormask', false, @islogical);
            parse (parser, varargin{:});
            parsed = parser.Results;

            assert (~isempty(CD.detectors));
            
            if (parsed.colormask)
                % sum up the individual masks in colors
                cmap = colormap('lines');
                m = CD.detectors{1}.getMask();
                mask = double(zeros(size(m,1), size(m,2), 3));
                for i = 1 : CD.N
                    m = double(CD.detectors{i}.getMask());
                    mask = mask + cat(3, m * cmap(i,1), m * cmap(i,2), m * cmap(i,3));
                end
            else
                % do OR for detectors masks
                mask = CD.detectors{1}.getMask();
                for i = 2 : CD.N
                     mask = mask | CD.detectors{i}.getMask();
                end
            end
        end

        
        function cars = detect (CD, img)
            
            % detect cars from every cluster
            carsByCluster = {[]};
            for i = 1 : CD.N
                carsCluster = CD.detectors{i}.detect(img);
                for icar = 1 : length(carsCluster)
                    carsCluster(icar).name = CD.clusters(i).name; 
                end
                carsByCluster{i} = carsCluster;
            end
            
            % remove duplicates
            if ~CD.noMerge
                carsByCluster = CD.combineClustersCars(carsByCluster);
            end
            
            % put into one array
            cars = Car.empty();
            for i = 1 : CD.N
                cars = [cars; carsByCluster{i}];
            end
        end

    end % methods
end
