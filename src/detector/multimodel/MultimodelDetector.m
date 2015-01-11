% implementation of CarDetectorInterface that allows different detectors for clusters

classdef MultimodelDetector < CarDetectorInterface
    properties (Hidden)
        
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
            if 2 * areaInters / (bbox1(3)*bbox1(4) + bbox2(3)*bbox2(4)) > threshold
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
            if CD.verbose, fprintf ('combineClustersCars removed %d cars\n', ...
                    m - length(cars2) - length(cars1)); end
        end
        
        function carsByCluster = combineClustersCars(CD, carsByCluster)
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'carsByCluster', @(x) iscell(x) && isa(x{1}, 'Car'));
            parse (parser, carsByCluster);

            for i = 1 : CD.N
                for j = i + 1 : CD.N
                    if nnz(CD.detectors(i).mask & CD.detectors(j).mask)
                        if CD.verbose, fprintf('combining detectors %d and %d\n', i, j); end 
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
            addRequired(parser, 'detectors', @(x) isa(x, 'CarDetectorInterface'));
            addParameter(parser, 'mergeThreshold', 0.5, @isscalar);
            parse (parser, clusters, detectors);
            parsed = parser.Results;
            assert (length(parsed.clusters) == length(parsed.detectors));

            CD.clusters = parsed.clusters;
            CD.detectors = parsed.detectors;
            CD.N = length(parsed.clusters);
            CD.mergeThreshold = parsed.mergeThreshold;
            for i = 1 : CD.N
                CD.detectors(i).mask = CD.clusters(i).recallMask;
            end
        end

        
        function mask = getMask(CD)
            assert (~isempty(CD.detectors));
            % do OR for detectors masks
            mask = CD.detectors(1).getMask();
            for i = 2 : CD.N
                 mask = mask | CD.detectors(i).getMask();
            end
        end

        
        function cars = detect (CD, img)
            
            % detect cars from every cluster
            carsByCluster = {[]};
            for i = 1 : CD.N
                carsCluster = CD.detectors(i).detect(img);
                for icar = 1 : length(carsCluster)
                    carsCluster(icar).name = CD.clusters(i).name; 
                end
                carsByCluster{i} = carsCluster;
            end
            
            % remove duplicates
            carsByCluster = CD.combineClustersCars(carsByCluster);
            
            % put into one array
            cars = Car.empty();
            for i = 1 : CD.N
                cars = [cars; carsByCluster{i}];
            end
        end

    end % methods
end
