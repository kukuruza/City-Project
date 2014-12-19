classdef CarTest < matlab.unittest.TestCase
    % Tests the Car class.

    properties
        image;
        carsList;
    end

    methods (TestClassSetup)
        function setupPaths (~)
            cd (fileparts(mfilename('fullpath')));
            run ../rootPathsSetup.m;
            run ../subdirPathsSetup.m;
        end
        
        function setupData(testCase)
            inCarsDir = 'unitTestData/';
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
        
        function testConstructorNotEnoughInputs(testCase)
            import matlab.unittest.constraints.Throws;
            testCase.verifyThat(@()Car, Throws('MATLAB:InputParser:notEnoughInputs'));
        end

        function testConstructorBadBbox(testCase)
            import matlab.unittest.constraints.Throws;
            testCase.verifyThat(@()Car([]), Throws('MATLAB:InputParser:ArgumentFailedValidation'));
        end

        function testDefaultTimestamp(testCase)
            car = Car([10 10 20 20]);
            testCase.verifySize(car.timeStamp, [1 6]);
        end
    end
end