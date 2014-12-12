% interface for probability for a car to move
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
            dist3D = obj.computeDistance3D(point1, point2);
            %dist3D = 1/obj.road.scaleFactor * log(double(point1(2)/point2(2)));

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
            dist3D = obj.computeDistance3D(point1, point2);
            %dist3D = 1/obj.road.scaleFactor * log(double(point1(2)/point2(2)));

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
            dist3D = obj.computeDistance3D(point1, point2);
            %dist3D = 1/obj.road.scaleFactor * log(double(point2(2)/point1(2)));

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
            dist3D = obj.computeDistance3D(point1, point2);
            %dist3D = 1/obj.road.scaleFactor * log(double(point2(2)/point1(2)));

            %fprintf('Changing lane : %f\n', dist3D);
            prob = obj.road.laneChangeProb * ...
                normpdf(dist3D, frameDiff*obj.road.roadVelMu, frameDiff * obj.road.roadVelSigma);
            return;
        end
    end
end