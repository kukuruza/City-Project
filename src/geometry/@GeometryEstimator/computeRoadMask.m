% Computing the road mask, to be used for segmenting the road
function computeRoadMask(obj)
    % Identifying the car lanes for the given image and given lanes
    % Costly and naive way to do things - needs improvization
    obj.roadMask = zeros(obj.imageSize);
    %tic
    newRoadMask = zeros(obj.imageSize);
    % Explicitely calculating the road lanes
    % Calculating the intercepts for the lan
    for yPt = floor(obj.road.vanishPt(2)):obj.imageSize(1)
        % Checking the intercepts for all the lanes
        intercpts = [];

        % Computing the interesection for first left lane
        xIntrpt = (yPt - obj.road.lanes{1}.leftEq(2)) /  obj.road.lanes{1}.leftEq(1);
        intercpts = [intercpts; xIntrpt];

        %Computing the intersections for right line segments
        for i = 1:length(obj.road.lanes)
            xIntrpt = (yPt - obj.road.lanes{i}.rightEq(2)) /  obj.road.lanes{i}.rightEq(1);
            intercpts = [intercpts; xIntrpt];
        end

        % Making the intercepts indices
        intercpts = floor(intercpts);

        % Assigning the corresponding points
        for i = 1:length(intercpts)-1
            % Move to the next lane if current lane isnt in the
            % frame yet
            if(intercpts(i+1) < 1)
                continue;
            end

            % Break the process if the current lane exists the
            % frame
            if(intercpts(i) > obj.imageSize(2))
                break;
            end
            %[i intercpts(i) intercpts(i+1) max(intercpts(i), 1) min(intercpts(i+1), obj.imageSize(2))]

            if(strcmp(obj.road.lanes{i}.direction, 'in') || strcmp(obj.road.lanes{i}.direction, 'out'))
                newRoadMask(yPt, max(intercpts(i), 1) : min(intercpts(i+1), obj.imageSize(2))) = i; 
            end
        end
    end
    obj.roadMask = newRoadMask;
    %toc

    % Brute-force way
    %for i = 1:obj.imageSize(1)
    %   for j = 1:obj.imageSize(2)
    %       obj.roadMask(i, j) = obj.road.detectCarLane([j, i]);
    %   end
    %end
    %toc
end
