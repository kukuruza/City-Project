classdef fitcropTest < matlab.unittest.TestCase
    properties

        image = uint8([1:10]' * ones(1,5));
        
        easyRoi = [2 3 4 5];
        easyExpected = uint8([2 2 2; 3 3 3; 4 4 4]);

    end
    methods (Test)
        
        function testEasyGray(T)
            crop = fitcrop (T.image, T.easyRoi);
            T.verifyEqual (crop, T.easyExpected);
        end
        
        function testDoubleGray(T)
            crop = fitcrop (double(T.image), T.easyRoi);
            T.verifyEqual (crop, double(T.easyExpected));
        end
        
        function testLogicalGray(T)
            crop = fitcrop (logical(T.image), T.easyRoi);
            T.verifyEqual (crop, logical(T.easyExpected));
        end
        
        function testEasyColor(T)
            crop = fitcrop (T.image(:,:,[1 1 1]), T.easyRoi);
            T.verifyEqual (crop, T.easyExpected(:,:,[1 1 1]));
        end
        
        function testLowX(T)
            crop = fitcrop (T.image, [2 -2 4 2]);
            T.verifyEqual (crop, uint8([2 2; 3 3; 4 4]));
        end
        
        function testLowY(T)
            crop = fitcrop (T.image, [-2 2 2 4]);
            T.verifyEqual (crop, uint8([1 1 1; 2 2 2]));
        end
        
        function testHighX(T)
            crop = fitcrop (T.image, [1 3 2 7]);
            T.verifyEqual (crop, uint8([1 1 1; 2 2 2]));
        end
        
        function testHighY(T)
            crop = fitcrop (T.image, [8 1 11 2]);
            T.verifyEqual (crop, uint8([8 8; 9 9; 10 10]));
        end
    end
end
