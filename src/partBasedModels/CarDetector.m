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
        
        % car:
        %      bboxes:    N x {x1 y1 x2 y2}
        %      score:     the more the more certain
        %      component: the view of the car
        %      orig:      for showboxes.m - original format
        %
        function cars = detect (detector, colorim)
            cd('voc-dpm-voc-release5.02');

            % actual detecting
            [ds, bs] = process(colorim, detector.model);
            bboxes = getboxes(detector.model, colorim, ds, reduceboxes(detector.model, bs));
            
            % copy to cars structure
            for i = 1 : size(bboxes,1)
                cars{i}.bboxes = reshape(bboxes(i,1:end-2), [4 length(bboxes(i,1:end-2))/4])';
                cars{i}.component = bboxes(i,end-1);
                cars{i}.score = bboxes(i,end);
                cars{i}.orig = bboxes(i,:);
            end
            
            cd ..
        end
    end % methods
end % classdef
