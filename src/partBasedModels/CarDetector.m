classdef CarDetector < handle
    properties (Hidden)
        model;
        csc_model;
    end % properties
    methods
        
        function detector = CarDetector (modelPath, modelYear, pca, thresh)
            % load the model
            temp = load(modelPath);
            detector.model = temp.model;
            clear temp
            
            % run startup
            cd /Users/evg/projects/City-Project/src/partBasedModels/voc-dpm-voc-release5.02
            %startup;
            
            detector.csc_model = cascade_model(detector.model, modelYear, pca, thresh);
            cd ..
        end
        
        % car:
        %      bboxes:    N x {x1 y1 x2 y2}
        %      score:     the more the more certain
        %      component: the view of the car
        %      orig:      for showboxes.m - original format
        %
        function cars = detect (detector, im)
            %cd('voc-dpm-voc-release5.02');

            % actual detecting
            pyra = featpyramid(double(im), detector.csc_model);
            [dCSC, bCSC] = cascade_detect(pyra, detector.csc_model, detector.csc_model.thresh);
            bboxes = getboxes(detector.csc_model, im, dCSC, bCSC);

            %[ds, bs] = process(colorim, detector.model);
            %bboxes = getboxes(detector.model, colorim, ds, reduceboxes(detector.model, bs));
            
            % copy to cars structure
            for i = 1 : size(bboxes,1)
                cars{i}.bboxes = reshape(bboxes(i,1:end-2), [4 length(bboxes(i,1:end-2))/4])';
                cars{i}.component = bboxes(i,end-1);
                cars{i}.score = bboxes(i,end);
                cars{i}.orig = bboxes(i,:);
            end
            
            %cd ..
        end
    end % methods
end % classdef
