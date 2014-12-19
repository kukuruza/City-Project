% test for car features - how good features describe a car
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% setup all the paths
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');
roadCameraMap = geom.getCameraRoadMap();

% MetricLearner
counting = MetricLearner(geom);

% input cars
inCarsDir = [CITY_DATA_PATH 'testdata/detector/detections/'];

pandasPrev = [];

for t = 1 : 11
    carsList = dir([inCarsDir sprintf('%03d', t) '-car*.mat']);

    % all features in one matrix
    pandas = Panda.empty();

    % generate features from the current frame
    for i = 1 : length(carsList)

        % load car object
        load ([inCarsDir carsList(i).name]);

        % generate features
        clear panda
        panda = Panda(car);
        panda.segmentPatch([]);
        panda.generateFeature();
        %   [C.histHog, ~] = C.reduceDimensions();

        pandas(i) = panda;
    end
    
    % predict transitions matrix
    predicted = zeros(length(pandas), length(pandasPrev));
    for i = 1 : length(pandas)
        for j = 1 : length(pandasPrev)
            feature1 = pandas(i).histHog;
            feature2 = pandasPrev(j).histHog;
            distance = norm(pandas(i).color - pandasPrev(j).color);
            %distance = chi_square_statistics(feature1, feature2);
            predicted(i,j) = 1 / distance;
        end
    end
    predicted = predicted / sum(predicted(:));
    
    % ground truth transition matrix
    if (~isempty(pandas) && ~isempty(pandasPrev))
        truthPath = [inCarsDir sprintf('%03d', t-1) '-' sprintf('%03d', t) '.txt'];
        truthMatches = dlmread(truthPath, ' ', 1, 0);
        truth = matches2transition (truthMatches, length(pandasPrev), length(pandas));
        truth = truth / sum(truth(:));

        colormap('hot');
        subplot(1,2,1);
        imagesc(predicted);
        xlabel('previous');
        ylabel('current');
        subplot(1,2,2);
        imagesc(truth);
        xlabel('previous');
        ylabel('current');

        % compute distance between transition matrix histograms
        chi_errors(t) = chi_square_statistics (predicted(:)', truth(:)');
    end
    
    pandasPrev = pandas;
end

fprintf('avg error between images: %f\n', mean(chi_errors(chi_errors ~= 0)));
