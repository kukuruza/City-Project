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
            addRequired(parser, 'cargroups', @(x) ~isempty(x) && );
            addRequired(parser, 'detectors', @isscalar);
            parse (parser, clusters, detectors);
            parsed = parser.Results;
            assert (length(parser.clusters) == length(parser.detectors));

            CD.clusters = parsed.clusters;
            CD.detectors = parsed.detectors;

        end
        function cars = detect (CD, img)

            cars = [];

            for icluster = 1 : length(clusters)
                cluster = clusters{icluster};
                mask = cluster.mask;

                cars_cluster = CD.detector.detect(img);
                for car = cars_cluster
                    center = car.getBottomCenter();
                    if mask(center(1), center(2)) && ...
                       car.bbox(3) > cluster.minsize && car.bbox(4) <= cluster.maxsize
                          cars = [cars; car];
                    end
                end
            end

        end % detect
    end % methods
end
