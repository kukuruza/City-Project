function [drawImage] = drawCarTransitions(carFrame1, carFrame2, binaryMatching, image)
    % Function to visualize the transitions of cars from one frame to the
    % next based on the binaryMatching matrix
    %
    % Usage: 
    % drawImage = drawCarTransitions(carFrame1, carFrame2, binaryMatching)
    %
    % Input :
    % carFrame1 : List of car objects in frame1
    % carFrame2 : List of car objects in frame2
    % binaryMatching : The binary matching matrix 
    % image: The image on which transitions are drawn
    %
    % Output:
    % drawImage : Output image
    
    drawImage = image;
    
    % Return if the number of cars in frames is zero
    if(length(carFrame1) == 0 || length(carFrame2) == 0)
        return;
    end
    
    % Choosing the color red
    color = [255, 0, 0];
    % Get the matched cars
    matches = find(binaryMatching == 1);
    
    % Extract the indices for each frame
    [f2Ind, f1Ind] = ind2sub(size(binaryMatching), matches);
    
    % For each car transition
    for i = 1:length(matches)
        box = carFrame1(f1Ind(i)).bbox;
        point1 = floor([box(1) + box(3)/2; box(2) + box(4)]);
        
        box = carFrame2(f2Ind(i)).bbox;
        point2 = floor([box(1) + box(3)/2; box(2) + box(4)]);

        % Minimum y value is from point1
        %if(point1(2) == min(point1(2), point2(2)
            
        
        % Drawing a line from one point to the another
        ySpan = min(point1(2), point2(2)) : max(point1(2), point2(2));
        
        if(point1(2) - point2(2) == 0)
            continue;
        end
        
        xSpan = point1(1) + (ySpan - point1(2)) * ...
                (point1(1) - point2(1))/ (point1(2) - point2(2));

        % Pruning xSpan and correspondingly ySpan
        toRemove = (xSpan < 1);
        xSpan(toRemove) = [];
        ySpan(toRemove) = [];
        
        % Marking the image with the straight lines for each
        % channel RGB
        for channel = 1:3
            indices = sub2ind(size(image), floor(ySpan), floor(xSpan), channel*ones(size(ySpan)));
            %if(sumindices == NaN)
              %  continue;
            %end
            drawImage(indices) = color(channel);
        end
    end 
end

