%Class definition for Geometry Detection along with methods

classdef GeometryEstimator
    properties
        geometryPath;
        returnPath;
        classifierPath;
    end
    methods
        %Constructor
        function[obj] = GeometryEstimator()
            %Paths to the geometry folder and back to current
            obj.geometryPath = '../objectsInPerspective/GeometricContext/';
            obj.returnPath = '../../../pipeline';
            %Relative to geometry Path
            obj.classifierPath = '../data/classifiers_08_22_2005.mat';
            
            %Adding the path to geometry context verification 
            addpath(strcat(obj.geometryPath, 'src/'));
            
        end
        %Method to calculate confidence maps to detect various geometries
        %in the image
        function[cMaps, cMapNames] = getConfidenceMaps(obj, inputImg)
            cd(strcat(obj.geometryPath, 'src'));
            %[cMaps, cMapNames] = photoPopup(inputImg, obj.classifierPath ,...
            %           '../test_dir/images/city10.jpg', [], ... 
            %           'OutputImages');
            [cMaps, cMapNames] = photoPopup(inputImg, obj.classifierPath ,...
                        'inputImage.jpg', [], '');
            cd(obj.returnPath);
        end
        
        
        
        %% interface for initial map. by Evgeny
        function mask = getCameraRoadmask (obj)%, camDirName? )
            
        end
        
        %% interface for probability for a car to move. by Evgeny
        function prob = getMutualProb (obj, car1, car2, frameDiff)
            assert (isa(car1, 'Car') && isa(car2, 'Car'));
            assert (isscalar(frameDiff));
            
        end
    end
end
