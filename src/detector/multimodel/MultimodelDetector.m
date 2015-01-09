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

        end
        
        function cars = detect (CD, img)

            cars = [];

            for icluster = 1 : length(CD.clusters)
                cluster = CD.clusters(icluster);
                mask = cluster.recallMask;
                
                % TODO: crop image to the bbox of the mask

                cars_cluster = CD.detectors(icluster).detect(img);
                for icar = 1 : length(cars_cluster)
                    car = cars_cluster(icar);
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
