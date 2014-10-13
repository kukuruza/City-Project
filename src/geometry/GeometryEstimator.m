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
        cameraRoadMap; %Contains the map for size estimations
    end
    methods
        %% Constructor
        function [obj] = GeometryEstimator(initImage, camPropertyFile)
            %Paths to the geometry folder and back to current
            obj.geometryPath = '../objectsInPerspective/GeometricContext/';
            obj.returnPath = '../../../pipeline';
            %Relative to geometry Path
            obj.classifierPath = '../data/classifiers_08_22_2005.mat';
            
            %Matfile name given manually for now, can be passed based on
            %the camera we are using it with
            %matFile = 'Geometry_Camera_360.mat';
            %Creating the road object from mat
            obj.road = Road(camPropertyFile);
            obj.imageSize = [size(initImage, 1), size(initImage, 2)];
            
            obj.roadMask = zeros(obj.imageSize);
            for i = 1:obj.imageSize(1)
                for j = 1:obj.imageSize(2)
                    obj.roadMask(i, j) = obj.road.detectCarLane([j, i]);
                end
            end

            %Using the geometry from objects in perspective paper
            [~, mask] = meshgrid(1:obj.imageSize(2), 1:obj.imageSize(1));
            
            %Need to normalize the image co-ordinates using f
            mask = max(double(mask - obj.road.vanishPt(2)) * obj.road.scaleFactor, zeros(obj.imageSize));
            mask = mask .* (obj.roadMask ~= 0);
            obj.cameraRoadMap = mask;
            
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
        function roadMask = getRoadMask(obj)
            roadMask = obj.roadMask;
        end
        
        %% interface for initial map
        function mask = getCameraRoadMap (obj)
            mask = obj.cameraRoadMap;
        end
        
        %% interface for probability for a car to move
        function prob = getMutualProb (obj, car1, car2, frameDiff)
            %assert (isa(car1, 'Car') && isa(car2, 'Car'));
            assert (isscalar(frameDiff));
            
            carPt1 = [car1.bbox(1) + car1.bbox(3)/2 ; car1.bbox(2) + car1.bbox(4)/2];
            carPt2 = [car2.bbox(1) + car2.bbox(3)/2 ; car2.bbox(2) + car2.bbox(4)/2];
            
            %Reading car lanes from the mask
            laneId1 = obj.roadMask(carPt1(2), carPt1(1));
            laneId2 = obj.roadMask(carPt2(2), carPt2(1));
            
            %[laneId1, lane1] = obj.road.getCarLane(car1);
            %[laneId2, lane2] = obj.road.getCarLane(car2);
            
            %Invalid car locations return zero probability (might need to
            %improve this for robustness) 
            if(laneId1 == 0 || laneId2 == 0)
                %Debug messages
                fprintf('One of the cars probably is not on the road, please re-check probabilities...\n');
                prob = 0;
                return;
            end
            
            lane1 = obj.road.lanes{laneId1};
            lane2 = obj.road.lanes{laneId2};
            
            %Invalid transitions
            %Direction doesnt match
            if(strcmp(lane1.direction, lane2.direction) ~= 1)
                %Debug messages
                fprintf('Specified transition not permitted..\n');
                prob = 0;
                return;
            end
            
            if(strcmp(lane1.direction, 'in'))
                %Checking for time consistency
                if(carPt2(2) > carPt1(2))
                    %Debug message
                    fprintf('Time inconsistency found between the car positions\n');
                    prob = 0;
                    return;
                end

                %If cars are from the same lane (no turning)
                if(laneId1 == laneId2)
                    slope = (carPt1(2) - carPt2(2)) / (carPt1(1) - carPt2(1));
                    %Evaluating the distance (approx) along the road
                    dist3D = (slope^2 + 1) ^ 0.5 / obj.road.scaleFactor * log(carPt1(2)/carPt2(2));
                    
                    %Use the distance to evaluate the probability
                    %Distribution = Guassian (frameDiff * obj.road.roadVelMu,
                    %frameDiff^2 * obj.road.roadVelVar)
                    prob = (1 - obj.road.laneChangeProb) * ...
                        normpdf(dist3D, frameDiff*obj.road.roadVelMu, frameDiff * obj.road.roadVelSigma);
                    return;
                else
                    %Car changing lanes (currently handles only one lane
                    %change between the given two frames)
                    laneId1
                    laneId2
                    if(abs(laneId1, laneId2) > 1)
                        fprintf('More than one car lane change, handles only one\n');
                        prob = 0;
                        return;
                    end
                    slope = (carPt1(2) - carPt2(2)) / (carPt1(1) - carPt2(1));
                    %Evaluating the distance (approx) along the road
                    dist3D = (slope^2 + 1) ^ 0.5 / obj.road.scaleFactor * log(carPt1(2)/carPt2(2));
                    
                    %Use the distance to evaluate the probability
                    %Distribution = Guassian (frameDiff * obj.road.roadVelMu,
                    %frameDiff^2 * obj.road.roadVelVar)
                    prob = obj.road.laneChangeProb * ...
                        normpdf(dist3D, frameDiff*obj.road.roadVelMu, frameDiff * obj.road.roadVelSigma);
                    return;
                end
                    
            else
                %Checking for time consistency
                if(carPt2(2) < carPt1(2))
                    %Debug message
                    fprintf('Time inconsistency found between the car positions\n');
                    prob = 0;
                    return;
                end

                %If cars are from the same lane (no turning)
                if(laneId1 == laneId2)
                    slope = (carPt1(2) - carPt2(2)) / (carPt1(1) - carPt2(1));
                    %Evaluating the distance (approx) along the road
                    dist3D = (slope^2 + 1) ^ 0.5 / obj.road.scaleFactor * log(carPt2(2)/carPt1(2));

                    %Use the distance to evaluate the probability
                    %Distribution = Guassian (frameDiff * obj.road.roadVelMu,
                    %frameDiff^2 * obj.road.roadVelVar)
                    prob = (1 - obj.road.laneChangeProb) * ...
                        normpdf(dist3D, frameDiff*obj.road.roadVelMu, frameDiff * obj.road.roadVelSigma);
                    return;
                else
                    %Car changing lanes (currently handles only one lane
                    %change between the given two frames)
                    
                    %Check if multiple lanes have been changed (currently,
                    %not handled)
                    if(abs(laneId1, laneId2) > 1)
                        fprintf('More than one car lane change, handles only one\n');
                        prob = 0;
                        return;
                    end
                    slope = (carPt1(2) - carPt2(2)) / (carPt1(1) - carPt2(1));
                    %Evaluating the distance (approx) along the road
                    dist3D = (slope^2 + 1) ^ 0.5 / obj.road.scaleFactor * log(carPt2(2)/carPt1(2));
                    
                    prob = obj.road.laneChangeProb * ...
                        normpdf(dist3D, frameDiff*obj.road.roadVelMu, frameDiff * obj.road.roadVelSigma);
                    return;
                end
            end
        end       
    end
end
