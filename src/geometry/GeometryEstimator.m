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
            
            % Reading the mat file that contains the manually marked points
            % Creating the road object from the mat
            obj.road = Road(camPropertyFile);
            obj.imageSize = [size(initImage, 1), size(initImage, 2)];
            
            % Identifying the car lanes for the given image and given lanes
            % Costly and naive way to do things - needs improvization
            obj.roadMask = zeros(obj.imageSize);
            for i = 1:obj.imageSize(1)
                for j = 1:obj.imageSize(2)
                    obj.roadMask(i, j) = obj.road.detectCarLane([j, i]);
                end
            end

            % Creating map of expected car sizes at different locations on
            % the image - should also include the orientation extension
            % because of the orientations
            [~, mask] = meshgrid(1:obj.imageSize(2), 1:obj.imageSize(1));
            
            %Need to normalize the image co-ordinates using f 
            % Alternatively, we calibrate using the average lane width and
            % calculate the scale factor accordingly
            mask = max(double(mask - obj.road.vanishPt(2)) * obj.road.scaleFactor * obj.road.carHeightMu, zeros(obj.imageSize));
            
            % Ignoring points outside the roadMask
            mask = mask .* (obj.roadMask ~= 0);
            obj.cameraRoadMap = 2 * mask;
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
            assert (isa(carOrPoint1, 'Car') || isvector(carOrPoint1));
            assert (isa(carOrPoint2, 'Car') || isvector(carOrPoint2));
            assert (isscalar(frameDiff));
            verbose = false;
            
            % Checking if the given argument is an object / double
            if(isobject(carOrPoint1))
                point1 = floor([carOrPoint1.bbox(1) + carOrPoint1.bbox(3)/2 ; carOrPoint1.bbox(2) + carOrPoint1.bbox(4)]);
            else
                point1 = floor(carOrPoint1);
            end
            
            if(isobject(carOrPoint2))
                point2 = floor([carOrPoint2.bbox(1) + carOrPoint2.bbox(3)/2 ; carOrPoint2.bbox(2) + carOrPoint2.bbox(4)]);
            else
                point2 = floor(carOrPoint2);
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
            
            %If one of the car is on the 'none' lane (parking /
            %divider), return zero
            if(strcmp(lane1.direction, 'none') || strcmp(lane2.direction, 'none'))
               %Debug messages
                if(verbose)
                    fprintf('Specified transition not permitted as one of car is on none lane..\n');
                end
                prob = 0;
                return;
            end
            
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
                    %if(abs(point1(1) - point2(1)) > 5)
                    %if(point1(1) ~= point2(1))
                    %if(0)
                    %    slope = double((point1(2) - point2(2)) / (point1(1) - point2(1)));
                    
                        %Evaluating the distance (approx) along the road
                    %    dist3D = ((slope^2 + 1) ^ 0.5) / obj.road.scaleFactor * log(double(point1(2)/point2(2)));
                    %else
                        %Vertical line
                    %    dist3D = 1/obj.road.scaleFactor * log(double(point1(2)/point2(2)));
                    %end
                    
                    %We care only about the distance along the road
                    dist3D = 1/obj.road.scaleFactor * log(double(point1(2)/point2(2)));
                    
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
                    %if(abs(point1(1) - point2(1)) > 5)
                    %if(point1(1) ~= point2(1))
                    %if(0)
                    %    slope = double((point1(2) - point2(2)) / (point1(1) - point2(1)));
                    
                        %Evaluating the distance (approx) along the road
                        %[slope (slope^f2+1)]% class(slope) class(slope^2 + 1)]% (slope ^ 2+ 1) ^ 0.5]
                    %    dist3D = (double(slope^2 + 1) ^ 0.5) / obj.road.scaleFactor * log(double(point1(2)/point2(2)));
                    %else
                    %    %Vertical line
                    %    dist3D = 1/obj.road.scaleFactor * log(double(point1(2)/point2(2)));
                    %end
                    
                    %We care only about the distance along the road
                    dist3D = 1/obj.road.scaleFactor * log(double(point1(2)/point2(2)));
                   
                    %Debugging
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
                    %if(point1(1) ~= point2(1))
                    %if(abs(point1(1) - point2(1)) > 5)
                    %if(0)
                    %    slope = double((point1(2) - point2(2)) / (point1(1) - point2(1)));
                    
                        %Evaluating the distance (approx) along the road
                    %    dist3D = ((slope^2 + 1) ^ 0.5) / obj.road.scaleFactor * log(double(point2(2)/point1(2)));
                    %else
                        %Vertical line
                    %    dist3D = 1/obj.road.scaleFactor * log(double(point2(2)/point1(2)));
                    %end
                    
                    %We care only about the distance along the road
                    dist3D = 1/obj.road.scaleFactor * log(double(point2(2)/point1(2)));
                
                    %Debug message
                    if(verbose)
                        fprintf('Car 1: (%d, %d) %d \nCar 2: (%d %d) %d\nDistance: %f\n', ...
                            point1(1), point1(2), laneId1, ...
                            point2(1), point2(2), laneId2, ...
                            dist3D);
                    end
                
                    %Debugging
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
                    %if(point1(1) ~= point2(1))
                    %if(abs(point1(1) - point2(1)) > 5)
                    %if(0)
                    %    slope = double((point1(2) - point2(2)) / (point1(1) - point2(1)));
                    
                        %Evaluating the distance (approx) along the road
                    %    dist3D = ((slope^2 + 1) ^ 0.5) / obj.road.scaleFactor * log(double(point2(2)/point1(2)));
                    %else
                        %Vertical line
                    %    dist3D = 1/obj.road.scaleFactor * log(double(point2(2)/point1(2)));
                    %end
                    
                    %We care only about the distance along the road
                    dist3D = 1/obj.road.scaleFactor * log(double(point2(2)/point1(2)));
                    
                    %fprintf('Changing lane : %f\n', dist3D);
                    prob = obj.road.laneChangeProb * ...
                        normpdf(dist3D, frameDiff*obj.road.roadVelMu, frameDiff * obj.road.roadVelSigma);
                    return;
                end
            end
        end
        
        %% Function to read the car lane using pre-computed roadMask
        function laneId = readCarLane(obj, carObj)
            %Input : carObj - A car object with valid bbox
            %Output : laneId - returns the id of the lane on which the car
            %is present
            
            carPoint = [carObj.bbox(1) + carObj.bbox(3)/2 ; carObj.bbox(2) + carObj.bbox(4)];
            laneId = obj.roadMask(carPoint(2), carPoint(1));
        end
        
        %% Generating the probability matrix given the cars in one frame; cars in another frame
        % according to the geometric constraints
        function[probMatrix] = generateProbMatrix(obj, carsFrame1, carsFrame2)
            % Generating the probability matrix given the cars in one frame
            % and cars in another, so that geometry is not violated
            % Input : 
            % CarsFrame1 = Cell of Car objects in frame1
            % CarsFrame2 = Cell of Car objects in frame2
            % 
            % Output:
            % probMatrix = Matrix of probability values for pairs of cars
            %
            
            % Assuming all the cars in frame 1 have same time stamp;
            % similarly for cars in frame 2
            
            if(isempty(carsFrame1))
                fprintf('Error in generating probability matrix, frame 1 has no cars\n');
                probMatrix = NaN;
                return;
            end
            
            if(isempty(carsFrame2))
                fprintf('Error in generating probability matrix, frame 2 has no cars\n');
                probMatrix = NaN;
                return;
            end
            
            % Initializing the probability matrix
            probMatrix = zeros(length(carsFrame2), length(carsFrame1));
            
            % Difference in second between two time frames
            % timeDiff = etime(carsFrame2(1).timeStamp, carsFrame1(1).timeStamp);
            timeDiff = 1;
            
            % Get the lanes for all the cars
            sortedCars = cell(2, length(obj.road.lanes));
            for i = 1:length(carsFrame1)
                curCarLane = obj.readCarLane(carsFrame1(i));
                sortedCars{1, curCarLane} = [sortedCars{1, curCarLane}, carsFrame1(i)];
            end
            for i = 1:length(carsFrame2)
                curCarLane = obj.readCarLane(carsFrame2(i));
                sortedCars{2, curCarLane} = [sortedCars{2, curCarLane}, carsFrame2(i)];
            end
            
            % Evaluate the mutual probabilities between the cars in two
            % frames
            for i = 1:length(carsFrame1)
                for j = 1:length(carsFrame2)
                    probMatrix(j, i) = obj.getMutualProb(carsFrame1(i), carsFrame2(j), timeDiff);
                end
            end
               
            % Now check for consistency between cars on the same lane in
            % both the frames
            % Reset the probability to zero if violation is found
            % Nearest car is most likely to be closer match (assumption)
            % (Can be made better by comparing how other cars move)
            
            
            
        end

        %% Interface to update the speed of the lanes based on approximate matching matrix
        function updateSpeed(obj, carsFrame1, carsFrame2, matchingMat)
            
        end
        %% DEBUGGING FUNCTIONS
        % Get the probability map of next transition given a point /
        % position of the car and overlaying for visualization
        function[probMap, overlaidImg] = generateProbMap(obj, carOrPoint, frameDiff, image)
            
            probMap = zeros(obj.imageSize(1), obj.imageSize(2));
            % Checking if its a point or a car
            if(isobject(carOrPoint))
                point = [carOrPoint.bbox(1) + carOrPoint.bbox(3)/2 ; carOrPoint.bbox(2) + carOrPoint.bbox(4)];
            else
                point = carOrPoint;
            end
            
            % Indices for which roadMap exists    
            ptsOnRoad = find(obj.roadMask ~= 0);
            for i = 1:length(ptsOnRoad)
                [r, c] = ind2sub(obj.imageSize, ptsOnRoad(i));
                probMap(ptsOnRoad(i)) = obj.getMutualProb(point, [c, r], frameDiff);
            end
            
            %Debugging
            %fprintf('Number of arguments %d \n', nargin);
            if(nargin < 4)
                overlaidImg = zeros(obj.imageSize);
                return
            end
            %Overlaying the probability map over the image
            %Normalizing to [0, 1] to [0, 255];
            probMapNorm = probMap / max(probMap(:));
            rgbMap = label2rgb(gray2ind(probMapNorm, 255), jet(255));
            
            %Creating mask for overlaying and ignoring small valued
            %probabilities
            mask = (probMapNorm < 10^-5);
            mask = mask(:, :, [1 1 1]);
            
            %overlaidImg(mask) =  image(mask);
            %overlaidImg(~mask) = rgbMap(~mask);
            overlaidImg = uint8(mask) .* image + uint8(~mask) .* rgbMap;
            
            %Marking the origin point 
            markerInserter = vision.MarkerInserter('Size', 5, 'BorderColor','Custom','CustomBorderColor', uint8([0 0 255]));
            overlaidImg = step(markerInserter, overlaidImg, uint32(point));
        end
        
        
    end
end
