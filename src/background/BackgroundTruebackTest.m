classdef BackgroundTruebackTest < matlab.unittest.TestCase
    % Tests the BackgroundGMM class.

    properties
        dowriteOut = true;
        
        inDir = 'testdata/';
        outDir;

        frameReader;
        background;
    end

    methods (TestClassSetup)
        function setupPaths (testCase)
            cd (fileparts(mfilename('fullpath')));
            run ../rootPathsSetup.m;
            run ../subdirPathsSetup.m;
            
            testCase.outDir = [CITY_DATA_PATH 'testdata/background/outTrueback/'];
        end
    end

   methods(TestMethodSetup)
        function constructObjects(testCase)
            run ../rootPathsSetup.m;

            % load geometry
            load([testCase.inDir 'geom.mat']);

            testCase.background = BackgroundTrueback (...
                                    [testCase.inDir 'background1.png'], ...
                                    geom, ...
                                    'black_threshold', 50);
                                             
            testCase.frameReader = FrameReaderImages (testCase.inDir);
        end
   end
   
   methods (Test)
        function testMask(testCase)
            for i = 0 : 1000000
                frame = testCase.frameReader.getNewFrame();
                if isempty(frame), break; end

                mask = testCase.background.subtract(frame);

                testCase.verifyTrue (islogical(mask));
                testCase.verifyEqual (size(mask,1), size(frame,1));
                testCase.verifyEqual (size(mask,2), size(frame,2));
                if i ~= 0, testCase.verifyTrue(nnz(mask) > 0); end
                
                if testCase.dowriteOut
                    imwrite (mask, [testCase.outDir, sprintf('mask-%06d.png', i)]);
                end
            end
            testCase.verifyEqual (i, 20);
        end
        
        function testBoxes(testCase)
            for i = 0 : 10000
                frame = testCase.frameReader.getNewFrame();
                if isempty(frame), break; end

                mask = testCase.background.subtract(frame);
                bboxes = testCase.background.mask2bboxes(mask);
                if i ~= 0
                    testCase.verifyTrue (~isempty(bboxes));
                    testCase.verifyTrue (size(bboxes,2) == 4);
                end
                
                frame_out = testCase.background.drawboxes(frame, bboxes);
                
                if testCase.dowriteOut
                    imwrite (frame_out, [testCase.outDir, sprintf('boxes-%06d.jpg', i)]);
                end
            end
            testCase.verifyEqual (i, 20);
        end
    end
end
