% Function draws next position (assuming 1s) based on the speed
function drawImage = drawNextPosition(obj, carFrames, image)
    % Input :
    % carFrames : Cars in this current frame
    % image : The current frame on which the cars were detected
    %
    %
    % Output : 
    % drawImage : Current frame with circles drawn at car locations
    %               and circles drawn to indicate their next
    %               position

    drawImage = image;
    color = [255, 0, 0];
    % For each car in the particular frame
    for i = 1:length(carFrames)
        box = carFrames(i).bbox;
        point = [box(1) + box(3)/2; box(2) + box(4)];

        % Getting the next position of the car (assuming 1s)
        % Lane is going out, hence estimating the correction
        % orientation of next point

        carLane = obj.roadMask(floor(point(2)), floor(point(1)));
        % If carLane detection is zero i.e. invalid detection; 
        % Do nothing about it
        if(carLane < 1)
            continue;
        end
        carLaneDirection = obj.road.lanes{carLane}.direction;

        if(strcmp(carLaneDirection, 'out'))
            nextPt = (point(2) - obj.road.vanishPt(2))*exp(obj.road.roadVelMu * obj.road.scaleFactor) ...
                    + obj.road.vanishPt(2);   
        else
            nextPt = (point(2) - obj.road.vanishPt(2))/exp(obj.road.roadVelMu * obj.road.scaleFactor) ...
                    + obj.road.vanishPt(2);
        end

        % Limiting the max value and min value
        if nextPt > size(image, 1)
            nextPt = size(image, 1);
        end

        %radius = abs(point(2) - nextPt);
        % Drawing a line from the current point to the
        % predicted point
        ySpan = floor(min(nextPt, point(2))) : floor(max(nextPt, point(2)));

        xSpan = point(1) + (ySpan - point(2)) * ...
                (obj.road.vanishPt(1) - point(1))/(obj.road.vanishPt(2) - point(2));

        % Pruning xSpan and correspondingly ySpan
        toRemove = (xSpan < 1);
        xSpan(toRemove) = [];
        ySpan(toRemove) = [];

        % Marking the image with the straight lines for each
        % channel RGB

        for channel = 1:3
            indices = sub2ind(size(image), floor(ySpan), floor(xSpan), channel*ones(size(ySpan)));
            drawImage(indices) = color(channel);
        end

        % Marking the circle at the current point
        % radius
        % markerInserter = vision.MarkerInserter('Size', ceil(radius), 'BorderColor','Custom','CustomBorderColor', uint8([0 0 255]));
        % drawImage = step(markerInserter, drawImage, uint32(point));
        % Draw
    end 
end   