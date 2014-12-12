% Generating the probability matrix given the cars in one frame; cars in another frame
% according to the geometric constraints
function probMatrix = generateProbMatrix(obj, carsFrame1, carsFrame2)
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

    % Initializing the probability matrix
    probMatrix = zeros(length(carsFrame2), length(carsFrame1));

    if isempty(carsFrame1) || isempty(carsFrame2)
        % it's not a degeneracy, it's normal  // Evgeny
        %fprintf('Degeneracy in generating probability matrix, frame 1 has no cars\n');
        return;
    end

    % Difference in second between two time frames
    timeDiff = etime(carsFrame2(1).timeStamp, carsFrame1(1).timeStamp);

    % If difference in time stamps is less than a threshold (almost
    % same), we return empty matrix
    if(timeDiff < 1e-2)
        fprintf('Degeneracy in generating probability matrix, timediff is zero\n');
        return;
    end
    %timeDiff = 1;

    % Get the lanes for all the cars
    %sortedCars = cell(2, length(obj.road.lanes));
    %for i = 1:length(carsFrame1)
    %    curCarLane = obj.readCarLane(carsFrame1(i));
    %    sortedCars{1, curCarLane} = [sortedCars{1, curCarLane}, carsFrame1(i)];
    %end
    %for i = 1:length(carsFrame2)
    %    curCarLane = obj.readCarLane(carsFrame2(i));
    %    sortedCars{2, curCarLane} = [sortedCars{2, curCarLane}, carsFrame2(i)];
    %end

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