classdef PBMDetector < handle
    properties (Hidden)
        model;
        csc_model;
    end % properties
    methods
        
        function detector = PBMDetector (modelPath, modelYear, pca, thresh)

            % load the model
            temp = load(modelPath);
            detector.model = temp.model;
            clear temp
            
            % run startup
            currentDir = pwd;
            global CITY_SRC_PATH
            if isempty(CITY_SRC_PATH)
                error('run rootPathsSetup.m first');
            end
            
            cd ([CITY_SRC_PATH, 'detector/PBM/voc-dpm-voc-release5.02']);
            %startup;
            detector.csc_model = cascade_model(detector.model, modelYear, pca, thresh);
            cd (currentDir)
        end
        
        % car:
        %      bboxes:    N x {x1 y1 width height}
        %      score:     the more the more certain
        %      component: the view of the car
        %      orig:      for showboxes.m - original format
        %
        function cars = detect (detector, im)

            % actual detecting
            pyra = featpyramid(double(im), detector.csc_model);
            [dCSC, bCSC] = cascade_detect(pyra, detector.csc_model, detector.csc_model.thresh);
            bboxes = getboxes(detector.csc_model, im, dCSC, bCSC);

            %[ds, bs] = process(colorim, detector.model);
            %bboxes = getboxes(detector.model, colorim, ds, reduceboxes(detector.model, bs));
            
            % default empty output
            cars = {};
            
            % copy to cars structure
            for i = 1 : size(bboxes,1)
                bb = reshape(bboxes(i,1:end-2), [4 length(bboxes(i,1:end-2))/4])';
                bb = [bb(:,1:2), bb(:,3)-bb(:,1), bb(:,4)-bb(:,2)];
                cars{i}.bboxes = bb;
                cars{i}.component = bboxes(i,end-1);
                cars{i}.score = bboxes(i,end);
                cars{i}.orig = bboxes(i,:);
            end
            
        end
    end % methods
end % classdef
