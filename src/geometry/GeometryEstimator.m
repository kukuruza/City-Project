%Class definition for Geometry Detection along with methods

classdef GeometryEstimator < handle
    properties
        %Paths for various components of the code
        geometryPath;
        returnPath;
        classifierPath;
        
        %Road object
        road;
        imageSize; %Size of the image
        roadMask; %Mask to know where exactly the road is present
            %We use the lanes from the road for now.
    end
    methods
        %% Constructor
        function[obj] = GeometryEstimator()
            %Paths to the geometry folder and back to current
            obj.geometryPath = '../objectsInPerspective/GeometricContext/';
            obj.returnPath = '../../../pipeline';
            %Relative to geometry Path
            obj.classifierPath = '../data/classifiers_08_22_2005.mat';
            
            %Adding the path to geometry context verification 
            addpath(fullfile(obj.geometryPath, 'src/'));
            
            %Matfile name given manually for now, can be passed based on
            %the camera we are using it with
            matFile = 'Geometry_Camera_360.mat';
            %Creating the road object from mat
            obj.road = Road(matFile);
        end
        
        %% Method to calculate confidence maps to detect various geometries
        % in the image
        function[cMaps, cMapNames] = getConfidenceMaps(obj, inputImg)
            cd(strcat(obj.geometryPath, 'src'));
            %[cMaps, cMapNames] = photoPopup(inputImg, obj.classifierPath ,...
            %           '../test_dir/images/city10.jpg', [], ... 
            %           'OutputImages');
            [cMaps, cMapNames] = photoPopup(inputImg, obj.classifierPath ,...
                        'inputImage.jpg', [], '');
            cd(obj.returnPath);
        end
        
        %% Creating a road Mask indicating the presence / absence of road
        function [] = getRoadMask(obj)
            roadMask = zeros(obj.imageSize);
            for i = 1:obj.imageSize(1)
                for j = 1:obj.imageSize(2)
                    roadMask(i, j) = obj.road.detectCarLane([j, i]);
                end
            end
            obj.roadMask = roadMask;
        end
        
        %% interface for initial map. by Evgeny
        function mask = getCameraRoadMap (obj)%, camDirName? )
            %Using the geometry from objects in perspective paper
            [~, mask] = meshgrid(1:obj.imageSize(2), 1:obj.imageSize(1));
            
            %Need to normalize the image co-ordinates using f
            mask = max(double(mask - obj.road.vanishPt(2)) * obj.road.carHeightMu / obj.road.camHeightMu, zeros(obj.imageSize));
            mask = mask .* (obj.roadMask ~= 0);
        end
        
        %% interface for probability for a car to move. by Evgeny
        function prob = getMutualProb (obj, car1, car2, frameDiff)
            assert (isa(car1, 'Car') && isa(car2, 'Car'));
            assert (isscalar(frameDiff));
            
        end
        
    end
end
