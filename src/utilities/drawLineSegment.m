function[drawImage] = drawLineSegment(image, point1, point2, color)
    % Script that draws the line segment between two specified points both 
    % assumed to be on the image
    %
    % Usage:
    % drawImage = drawLineSegment(image, point1, point2)
    % 
    % Input: 
    % image - the image on which the line segment is to be drawn
    % point1, point2 - ends of the line segment
    % color(default red) - color of the line segment

    % Initialising with defaults
    if(nargin < 4)
        color = uint8([255, 0, 0]);
    end

    xDiff = abs(point1(1) - point2(1));
    yDiff = abs(point1(2) - point2(2));
    % Drawing based on x-coordinate
    if(xDiff > yDiff)
        xSpan = min(point1(1), point2(1)) : max(point1(1), point2(1));
        ySpan = point1(2) + (xSpan - point1(1)) * ...
                (point1(2) - point2(2))/ (point1(1) - point2(1));

        % Pruning xSpan and correspondingly ySpan
        toRemove = (ySpan < 1);
    else
    % Drawing based on y-coordinate
        ySpan = min(point1(2), point2(2)) : max(point1(2), point2(2));
        xSpan = point1(1) + (ySpan - point1(2)) * ...
                (point1(1) - point2(1))/ (point1(2) - point2(2));

        % Pruning xSpan and correspondingly ySpan
        toRemove = (xSpan < 1);
    end
    
    % Pruning xSpan and correspondingly ySpan
    xSpan(toRemove) = [];
    ySpan(toRemove) = [];
    
    % Marking the image with the straight lines for each
    % channel RGB
    drawImage = image;
    
    for channel = 1:3
        indices = sub2ind(size(image), floor(ySpan), floor(xSpan),...
                                                channel*ones(size(ySpan)));
        drawImage(indices) = color(channel);
    end
end
