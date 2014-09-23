classdef CarDetector < handle
    properties (Hidden)
        model;
    end % properties
    methods
        
        function detector = CarDetector (modelPath) % constructor
            % load the model
            temp = load(modelPath);
            detector.model = temp.model;
            clear temp
            
            % run startup
            cd voc-dpm-voc-release5.02
            startup;
            cd ..
        end
        
        function cars = detect (detector, colorim)
            cd('voc-dpm-voc-release5.02');

            % actual detecting
            [ds, bs] = process(colorim, detector.model);
            bboxes = getboxes(detector.model, colorim, ds, reduceboxes(detector.model, bs));
            
            % copy to cars structure
            for i = 1 : size(bboxes,1)
                cars{i}.bboxes = bboxes(i,1:end-2);
                cars{i}.component = bboxes(i,end-1);
                cars{i}.score = bboxes(i,end);
            end
            
            cd ..
        end
    end % methods
end % classdef
