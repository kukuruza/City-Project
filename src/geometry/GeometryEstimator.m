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
        % Extended functionality to calculate the probabilities for either
        % between pairs of points/cars or between a point and a car
        function prob = getMutualProb (obj, carOrPoint1, carOrPoint2, frameDiff)
            %assert (isa(car1, 'Car') && isa(car2, 'Car'));
            assert (isscalar(frameDiff));
            verbose = false;
            
            % Checking if the given argument is an object / double
            if(isobject(carOrPoint1))
                point1 = floor([carOrPoint1.bbox(1) + carOrPoint1.bbox(3)/2 ; carOrPoint1.bbox(2) + carOrPoint1.bbox(4)/2]);
            else
                point1 = carOrPoint1;
            end
            
            if(isobject(carOrPoint2))
                point2 = floor([carOrPoint2.bbox(1) + carOrPoint2.bbox(3)/2 ; carOrPoint2.bbox(2) + carOrPoint2.bbox(4)/2]);
            else
                point2 = carOrPoint2;
            end
            
            %Reading car lanes from the mask
            laneId1 = obj.roadMask(point1(2), point1(1));
            laneId2 = obj.roadMask(point2(2), point2(1));
            
            %[laneId1, lane1] = obj.road.getCarLane(car1);
            %[laneId2, lane2] = obj.road.getCarLane(car2);
            
            %Invalid car locations return zero probability (might need to
            %improve this for robustness) 
            if(laneId1 == 0 || laneId2 == 0)
                %Debug messages
                if(verbose)
                    fprintf('One of the cars probably is not on the road, please re-check probabilities...\n');
                end
                prob = 0;
                return;
            end
            
            lane1 = obj.road.lanes{laneId1};
            lane2 = obj.road.lanes{laneId2};
            
            %Invalid transitions
            %Direction doesnt match
            if(strcmp(lane1.direction, lane2.direction) ~= 1)
                %Debug messages
                if(verbose)
                    fprintf('Specified transition not permitted..\n');
                end
                prob = 0;
                return;
            end
            
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            % Direction of initial lane of car is in
            if(strcmp(lane1.direction, 'in'))
                %Checking for time consistency
                if(point2(2) > point1(2))
                    %Debug message
                    if(verbose)
                        fprintf('Time inconsistency found between the car positions\n');
                    end
                    prob = 0;
                    return;
                end

                %If cars are from the same lane (no turning)
                if(laneId1 == laneId2)
                    %Slope evaluated using points - point1 and point2
                    if(point1(1) ~= point2(1))
                        slope = double((point1(2) - point2(2)) / (point1(1) - point2(1)));
                    
                        %Evaluating the distance (approx) along the road
                        dist3D = ((slope^2 + 1) ^ 0.5) / obj.road.scaleFactor * log(double(point1(2)/point2(2)));
                    else
                        %Vertical line
                        dist3D = 1/obj.road.scaleFactor * log(double(point1(2)/point2(2)));
                    end
                    
                    %Use the distance to evaluate the probability
                    %Distribution = Guassian (frameDiff * obj.road.roadVelMu,
                    %frameDiff^2 * obj.road.roadVelVar)
                    %fprintf('No lane change (in) : %f\n', dist3D);
                    prob = (1 - obj.road.laneChangeProb) * ...
                        normpdf(dist3D, frameDiff*obj.road.roadVelMu, frameDiff * obj.road.roadVelSigma);
                    return;
                else
                    %Car changing lanes (currently handles only one lane
                    %change between the given two frames)
                    if(abs(laneId1 - laneId2) > 1)
                        if(verbose)
                            fprintf('More than one car lane change, handles only one\n');
                        end
                        prob = 0;
                        return;
                    end
                    
                    %Slope evaluated using points - point1 and point2
                    if(point1(1) ~= point2(1))
                        slope = double((point1(2) - point2(2)) / (point1(1) - point2(1)));
                    
                        %Evaluating the distance (approx) along the road
                        %[slope (slope^f2+1)]% class(slope) class(slope^2 + 1)]% (slope ^ 2+ 1) ^ 0.5]
                        dist3D = (double(slope^2 + 1) ^ 0.5) / obj.road.scaleFactor * log(double(point1(2)/point2(2)));
                    else
                        %Vertical line
                        dist3D = 1/obj.road.scaleFactor * log(double(point1(2)/point2(2)));
                    end
                    
                    %slope = (point1(2) - point2(2)) / (point1(1) - point2(1));
                    %Evaluating the distance (approx) along the road
                    %dist3D = (slope^2 + 1) ^ 0.5 / obj.road.scaleFactor * log(point1(2)/point2(2));
                    
                    
                    %fprintf('Lane change (in) : %f\n', dist3D);
                    %Use the distance to evaluate the probability
                    %Distribution = Guassian (frameDiff * obj.road.roadVelMu,
                    %frameDiff^2 * obj.road.roadVelVar)
                    prob = obj.road.laneChangeProb * ...
                        normpdf(dist3D, frameDiff*obj.road.roadVelMu, frameDiff * obj.road.roadVelSigma);
                    return;
                end
                    
            else
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            
                %Current lane of the car is out
                %Checking for time consistency
                if(point2(2) < point1(2))
                    %Debug message
                    if(verbose)
                        fprintf('Time inconsistency found between the car positions\n');
                    end
                    prob = 0;
                    return;
                end

                %If cars are from the same lane (no turning)
                if(laneId1 == laneId2)
                    %Slope evaluated using points - point1 and point2
                    if(point1(1) ~= point2(1))
                        slope = double((point1(2) - point2(2)) / (point1(1) - point2(1)));
                    
                        %Evaluating the distance (approx) along the road
                        dist3D = ((slope^2 + 1) ^ 0.5) / obj.road.scaleFactor * log(double(point2(2)/point1(2)));
                    else
                        %Vertical line
                        dist3D = 1/obj.road.scaleFactor * log(double(point2(2)/point1(2)));
                    end
                    
                    %slope = (point1(2) - point2(2)) / (point1(1) - point2(1));
                    %Evaluating the distance (approx) along the road
                    %dist3D = (slope^2 + 1) ^ 0.5 / obj.road.scaleFactor * log(point2(2)/point1(2));

                    %fprintf('No lane change (out) : %f\n', dist3D);
                    
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
                    if(abs(laneId1 - laneId2) > 1)
                        if(verbose)
                            fprintf('More than one car lane change, handles only one\n');
                        end
                        prob = 0;
                        return;
                    end

                    %Slope evaluated using points - point1 and point2
                    if(point1(1) ~= point2(1))
                        slope = double((point1(2) - point2(2)) / (point1(1) - point2(1)));
                    
                        %Evaluating the distance (approx) along the road
                        dist3D = ((slope^2 + 1) ^ 0.5) / obj.road.scaleFactor * log(double(point2(2)/point1(2)));
                    else
                        %Vertical line
                        dist3D = 1/obj.road.scaleFactor * log(double(point2(2)/point1(2)));
                    end
                    
                    %slope = (point1(2) - point2(2)) / (point1(1) - point2(1));
                    %Evaluating the distance (approx) along the road
                    %dist3D = (slope^2 + 1) ^ 0.5 / obj.road.scaleFactor * log(point2(2)/point1(2));
                    
                    %fprintf('Changing lane : %f\n', dist3D);
                    prob = obj.road.laneChangeProb * ...
                        normpdf(dist3D, frameDiff*obj.road.roadVelMu, frameDiff * obj.road.roadVelSigma);
                    return;
                end
            end
        end
        
        %% Get the probability map of next transition given a point / position of the car
        function probMap = generateProbMap(obj, carOrPoint, frameDiff)
            probMap = zeros(obj.imageSize(1), obj.imageSize(2));
            
            % Checking if its a point or a car
            if(isobject(carOrPoint))
                point = [carOrPoint.bbox(1) + carOrPoint.bbox(3)/2 ; carOrPoint.bbox(2) + carOrPoint.bbox(4)/2];
            else
                point = carOrPoint;
            end
            
            % Indices for which roadMap exists    
            ptsOnRoad = find(obj.roadMask ~= 0);
            for i = 1:length(ptsOnRoad)
                [r, c] = ind2sub(obj.imageSize, ptsOnRoad(i));
                probMap([ptsOnRoad(i)]) = obj.getMutualProb(point, [c, r], frameDiff);
            end
        end
    end
end
