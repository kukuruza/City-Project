classdef bboxRoiTest < matlab.unittest.TestCase
   
   methods (Test)
        function testBboxRoi (testCase)
            bbox = [1 4 6 8];
            
            testCase.verifyEqual (bbox, bbox2roi(roi2bbox(bbox)));
        end
        
    end
end
