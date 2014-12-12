function updateSpeed(obj, carsFrame1, carsFrame2, matchingMat, geomMatrix)
    % Function to update the speed of the lanes using approximate
    % matching available
    % TODO: Import the timeStamp attribute to get exact timing

    % If either of the list is empty, do nothing
    if(isempty(carsFrame1) || isempty(carsFrame2) == 0)
        return;
    end

    % Assuming atleast one car in each of the frames
    % Difference in second between two time frames
    timeDiff = etime(carsFrame2(1).timeStamp, carsFrame1(1).timeStamp);


    % Indices of geometrically valid car transitions
    possTransitions = find(geomMatrix > 0);
    [f2Id, f1Id] = ind2sub(size(geomMatrix), possTransitions);

    % Evaluating the possible speeds for all the pairs of matching
    noChecks = length(f1Id);
    speeds = zeros(noChecks, 1);

    % Getting possible speeds
    for i = 1:noChecks
        % Extracting the points on road for the car
        box1 = carsFrame1(f1Id(i)).bbox;
        box2 = carsFrame2(f2Id(i)).bbox;

        car1Pt = [box1(1) + box1(3)/2, box1(2) + box1(4)];
        car2Pt = [box2(1) + box2(3)/2, box2(2) + box2(4)];

        % Computing the distance, in effect the speed by dividing
        % by timeDiff
        speeds(i) = obj.computeDistance3D(car1Pt, car2Pt) / timeDiff;
    end

    % Updating the speeds based on the probabilities obtained from
    % matching matrix
    weightedSpeed = sum(speeds .* matchingMat(possTransitions))/sum(matchingMat(possTransitions));

    % Printing message
    %fprintf('\nCompleted the speed update\nMeanSpeed : %f , %f\nPriorSpeed: %f\n',...
    %        weightedSpeed, mean(speeds), obj.road.roadVelMu);
    fprintf('\nSpeed updation complete!\nSpeed Change : %f => %f\n', ...
            obj.road.roadVelMu, weightedSpeed); 

    obj.road.roadVelMu = weightedSpeed;
end