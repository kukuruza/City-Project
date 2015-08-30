classdef mask2roiTest < matlab.unittest.TestCase
   
   methods (Test)
        function testMask(testCase)
            mask = imread('testdata/mask.png');

            roi = mask2roi(mask);
            size(mask);
            
            %bbox = [roi(2), roi(1), roi(4)-roi(2)+1, roi(3)-roi(1)+1];
            %mask = insertObjectAnnotation (uint8(mask*255), 'rectangle', bbox, 'label');
            %imshow(mask);
            
            testCase.verifyEqual (roi, uint32([5 13 37 67]));
        end
        
    end
end
