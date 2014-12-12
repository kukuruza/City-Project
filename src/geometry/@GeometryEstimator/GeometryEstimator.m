%Class definition for Geometry Detection along with methods

classdef GeometryEstimator < GeometryInterface
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
        cameraRoadMap; %Contains the map for size estimations
        orientationMap; % Orientation of cars at the given point
        homography; % Computing the homography to get 'cannonical' form
        
        % Belief that builds through accumulating foreground pixels in
        % someway
        roadBelief;
        
    end
    methods
        %% Constructor
        function [obj] = GeometryEstimator(initImage, camPropertyFile)
            %Paths to the geometry folder and back to current
            %obj.geometryPath = '../objectsInPerspective/GeometricContext/';
            %obj.returnPath = '../../../pipeline';
            %Relative to geometry Path
            %obj.classifierPath = '../data/classifiers_08_22_2005.mat';
           
            addpath('.');
            
            % Initializing the belief about the road
            obj.roadBelief = zeros(size(initImage));
            
            % Reading the mat file that contains the manually marked points
            % Creating the road object from the mat
            obj.road = Road(camPropertyFile);
            obj.imageSize = [size(initImage, 1), size(initImage, 2)];
            
            % Identifying the car lanes for the given image and given lanes
            obj.computeRoadMask();
            
            % Computing the homography
            obj.computeHomography();
            
            % Creating map of expected car sizes at different locations on
            % the image - should also include the orientation extension
            % because of the orientations
            obj.computeCameraRoadMapWithH();   
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
      
        % interface for probability for a car to move
        % Extended functionality to calculate the probabilities for either
        % between pairs of points/cars or between a point and a car
        prob = getMutualProb (obj, carOrPoint1, carOrPoint2, frameDiff);
        
        % Function to read the car lane using pre-computed roadMask
        function laneId = readCarLane(obj, carObj)
            %Input : carObj - A car object with valid bbox
            %Output : laneId - returns the id of the lane on which the car
            %is present
            
            carPoint = [carObj.bbox(1) + carObj.bbox(3)/2 ; carObj.bbox(2) + carObj.bbox(4)];
            laneId = obj.roadMask(int32(carPoint(2)), int32(carPoint(1)));
        end
        
        % Generating the probability matrix given the cars in one frame; cars in another frame
        % according to the geometric constraints
        probMatrix = generateProbMatrix(obj, carsFrame1, carsFrame2)

        % Interface to update the speed of the lanes based on approximate matching matrix
        updateSpeed(obj, carsFrame1, carsFrame2, matchingMat, geomMatrix);
        
        % Function to return the 3D distance for the given geometry
        dist3D = computeDistance3D(obj, point1, point2);
        
        % Function to get a belief about the road using foreground (binary)
        function generateRoadBelief(obj, foreground)
            %figure(1); 
        end
        
        % Computing the camera road map, for cannonical system using
        % homography estimated before
        computeCameraRoadMapWithH(obj);
        
        %% Getters (debugging and interface)
        % Function to get the expected orientation of cars at a particular
        % point using geometry
        function orientationMap = getOrientationMap(obj)
            orientationMap = obj.orientationMap;
        end
        
        % Creating a road Mask indicating the presence / absence of road
        function roadMask = getRoadMask(obj)
            roadMask = obj.roadMask;
        end
        
        % interface for initial map
        function sizeMap = getCameraRoadMap (obj)
            sizeMap = obj.cameraRoadMap;
        end
        
        % Get the homography
        function homography = getHomography(obj)
            homography = obj.homography;
        end
        
        %% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Function signatures found in the folder @GeometryEstimator
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        % Given the current position of cars, draws their expectated
        % position in next frame (1 sec)
        drawImage = drawNextPosition(obj, carFrames, image);
        
        % Computes homography necessary to convert the given setup into a
        % cannonical setup (vanishing point at center of image, etc)
        computeHomography(obj);
        
        % Computes the corresponding, opposite point on other side of the 
        % road for the cannonical configuration
        oppositePt = getOppositePoint(obj, point, line, oppLine);
        
        %% DEBUGGING FUNCTIONS
        % Get the probability map of next transition given a point /
        % position of the car and overlaying for visualization
        [probMap, overlaidImg] = generateProbMap(obj, carOrPoint, frameDiff, image);
    end
    
    %% Methods that are hidden and private to the class
    methods (Hidden)
        % Computing the road mask, to be used for segmenting the road
        computeRoadMask(obj);
        
        % Computing the camera road map
        computeCameraRoadMap(obj);
        
        % Function to get the expected orientation of cars at a particular
        % point using geometry
        function orientationMap = computeOrientationMap(obj)
            orientationMap = zeros(obj.imSize);
        end
    end
end
