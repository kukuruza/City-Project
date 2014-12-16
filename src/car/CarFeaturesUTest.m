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

carsPrev = [];

for t = 1 : 11
    carsList = dir([inCarsDir sprintf('%03d', t) '-car*.mat']);

    % all features in one matrix
    cars = Car.empty();

    % generate features from the current frame
    for i = 1 : length(carsList)

        % load car object
        clear car
        load ([inCarsDir carsList(i).name]);

        % generate features
        car.segmentPatch([]);
        car.generateFeature();
        %   [C.histHog, ~] = C.reduceDimensions();

        cars(i) = car;
    end
    
    % predict transitions matrix
    predicted = zeros(length(cars), length(carsPrev));
    for i = 1 : length(cars)
        for j = 1 : length(carsPrev)
            feature1 = cars(i).histHog;
            feature2 = carsPrev(j).histHog;
            distance = norm(cars(i).color - carsPrev(j).color);
            %distance = chi_square_statistics(feature1, feature2);
            predicted(i,j) = 1 / distance;
        end
    end
    predicted = predicted / sum(predicted(:));
    
    % ground truth transition matrix
    if (~isempty(cars) && ~isempty(carsPrev))
        truthPath = [inCarsDir sprintf('%03d', t-1) '-' sprintf('%03d', t) '.txt'];
        truthMatches = dlmread(truthPath, ' ', 1, 0);
        truth = matches2transition (truthMatches, length(carsPrev), length(cars));
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
    
    carsPrev = cars;
end

fprintf('avg error between images: %f\n', mean(chi_errors(chi_errors ~= 0)));
