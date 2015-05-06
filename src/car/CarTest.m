classdef CarTest < matlab.unittest.TestCase
    % Tests the Car class.

    properties
        image;
        carsList;
    end

    methods (TestClassSetup)
        function setupPaths (testCase)
            % set paths
            assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
            CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
            addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
            cd (fileparts(mfilename('fullpath')));        % change dir to this script

            inCarsDir = 'testdata/';
            testCase.image = imread([inCarsDir '002-clear.png']);
            testCase.carsList = dir([inCarsDir '002-car*.mat']);
        end
        
    end

    methods (Test)
        function testBasicConstructor(testCase)
            car = Car([10 10 20 20], [2014 12 19 01 01 01]);
            testCase.verifyEqual(car.bbox, [10 10 20 20], ...
                'Constructor failed to set up bbox');
            testCase.verifyEqual(car.timeStamp, [2014 12 19 01 01 01], ...
                'Constructor failed to set up time stamp');
        end
        
        function testDefaultTimestamp(testCase)
            car = Car([10 10 20 20]);
            testCase.verifySize(car.timeStamp, [1 6]);
        end
        
        function testGetCenter(testCase)
            car = Car([10 30 20 20]);   % [x y w h]
            testCase.verifyEqual(car.getCenter(), int32([30+20/2 10+20/2]));
        end
        
        function testGetBottomCenter(testCase)
            car = Car([10 30 20 20]);   % [x y w h]
            testCase.verifyEqual(car.getBottomCenter(), int32([30+20*0.75-1 10+20/2]));
        end
        
        function testEmptyCar(testCase)
            car = Car();
            testCase.verifyFalse (car.isOk())
        end
    end
end