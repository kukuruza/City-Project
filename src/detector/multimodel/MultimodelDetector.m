% implementation of CarDetectorInterface that allows different detectors for clusters

classdef MultimodelDetector < CarDetectorInterface
    properties (Hidden)
        
        clusters  % descriptions of car clusters
        detectors  % detectors for each of the groups
        
    end % properties
    methods
        function CD = MultimodelDetector (clusters, detectors)
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'clusters', @(x) ~isempty(x));
            addRequired(parser, 'detectors', @(x) isa(x, 'CarDetectorInterface'));
            parse (parser, clusters, detectors);
            parsed = parser.Results;
            assert (length(parsed.clusters) == length(parsed.detectors));

            CD.clusters = parsed.clusters;
            CD.detectors = parsed.detectors;
            for i = 1 : length(clusters)
                CD.detectors(i).mask = CD.clusters(i).recallMask;
            end

        end

        
        function mask = getMask(CD)
            assert (~isempty(CD.detectors));
            % do OR for detectors masks
            mask = CD.detectors(1).getMask();
            for i = 2 : length(CD.detectors)
                 mask = mask | CD.detectors(i).getMask();
            end
        end

        
        function cars = detect (CD, img)

            cars = [];
            for icluster = 1 : length(CD.clusters)
                cars_cluster = CD.detectors(icluster).detect(img);
                for icar = 1 : length(cars_cluster)
                    car = cars_cluster(icar);
                    car.name = CD.clusters(icluster).name; 
                    cars = [cars, car];
                end
            end

        end % detect
    end % methods
end
