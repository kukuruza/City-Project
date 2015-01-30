% implementation of CarDetectorInterface that allows different detectors for clusters

classdef MultimodelDetector < CarDetectorBase
    properties
        
        verbose;
        
        % do not combine detections from different detectors
        noMerge = false;
        
        clusters   % descriptions of car clusters
        detectors  % detectors for each of the groups
        N          % number of both clusters and detectors
        
        mergeOverlap;
        
    end % properties
    methods
        
        function CD = MultimodelDetector (clusters, detectors, varargin)
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'clusters', @(x) ~isempty(x));
            addRequired(parser, 'detectors', @(x) ~isempty(x) && iscell(x));
            addParameter(parser, 'mergeOverlap', 0.8, @isscalar);
            addParameter(parser, 'verbose', 0, @isscalar);
            parse (parser, clusters, detectors, varargin{:});
            parsed = parser.Results;
            assert (length(parsed.clusters) == length(parsed.detectors));
            for i = 1 : length(detectors), assert(isa(detectors{i}, 'CarDetectorInterface')); end

            CD.clusters = parsed.clusters;
            CD.detectors = parsed.detectors;
            CD.N = length(parsed.clusters);
            CD.mergeOverlap = parsed.mergeOverlap;
            CD.setVerbosity(parsed.verbose);
        end

        
        function setVerbosity (CD, verbose)
            CD.verbose = verbose;
            for i = 1 : length(CD.detectors), CD.detectors{i}.setVerbosity(verbose); end
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
            
            % put into one array
            cars = Car.empty();
            for i = 1 : CD.N
                cars = [cars; carsByCluster{i}];
            end
            
            % combine detections
            cars = mergeCars (cars, 'overlap', CD.mergeOverlap);
        end

    end % methods
end
