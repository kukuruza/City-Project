function [bestVP] = ransacVanishPoint(lines, image, offset)
    % Function RANSAC the vanishing point using the correction angle
    imSize = size(image);
    noLines = size(lines, 1);
    
    % Computing the unit vectors for all the line segments
    dirVecs = [lines(:, 1) - lines(:, 2), lines(:, 3) - lines(:, 4)];
    dirVecs = bsxfun(@rdivide, dirVecs , hypot(dirVecs(:, 1), dirVecs(:, 2)));
    centers =[mean(lines(:, [1 2]), 2), mean(lines(:, [3 4]), 2)];
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Debugging the centers
    debug = false;
    if(debug)
        figure(1); hold off
            imshow(image)
        figure(1); hold on
            plot(centers(:, 1), offset + centers(:, 2), 'o', 'lineWidth', 2);
            plot(lines(:, [1 2])', offset + lines(:, [3 4])')
    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    % Generating the equations of the line
    lineEq = zeros(noLines, 3);
    for j = 1:noLines
        %lineEq(j , :) = cross([houghLines(j).point1, 1], [houghLines(j).point2, 1]);
        lineEq(j , :) = cross([lines(j, [1 3]), 1], [lines(j, [2 4]), 1]);
    end
    
    % Generate candidate VP points
    [xInd, yInd] = meshgrid(1:noLines, 1:noLines);
    inds = [nonzeros(triu(xInd, 1)), nonzeros(triu(yInd, 1))];
    
    % Intersections
    intersects = cross(lineEq(inds(:, 1), :), lineEq(inds(:, 2), :));
    candidates = [intersects(:, 1) ./ intersects(:, 3), ...
                            intersects(:, 2) ./ intersects(:, 3)];
    
%     withinImg = (candidates(:, 1) > 0) & (candidates(:, 1) < imSize(2)) & ...
%                (candidates(:, 2) > 0) & (candidates(:, 2) < imSize(1));
    
    withinImg = abs(candidates(:, 1)) < imSize(2) & ...
                abs(candidates(:, 2)) < imSize(1);
            
    vPts = candidates(withinImg, :);
    %vPts = candidates;
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Selecting the best vanishing point from candidates based on the
    % amount of rotation caused in the line segments
    noVPts = size(vPts, 1);
    penalty = zeros(noVPts, 1);
    consensus = zeros(noVPts, 1);
    angleThreshold = 5;
    
    for i = 1:noVPts
        % Finding the angular displacement
        locVector = bsxfun(@minus, centers, vPts(i, :));
        dotProduct = abs(sum(locVector .* dirVecs, 2))...
                                ./ hypot(locVector(:, 1), locVector(:, 2));
        dotProduct(dotProduct > 1) = 1.0;
        angles = acosd(dotProduct);
        
        penalty(i) = sum(angles);
        
        % Performing a consensus step
        agreement =  angles < angleThreshold;
        consensus(i) = sum(agreement);
        %fprintf('%f %f\n', consensus(i), max(consensus(1:(i-1))));
        
        % Recording the consensus
        if(i == 1)
            bestConsensus = agreement;
        elseif (consensus(i) > max(consensus(1:(i-1))))
            bestConsensus = agreement;
        end
    end
    
    % Maximum consensus
    [maxCons, ~] = max(consensus);
    maxInds = consensus == maxCons;
    
    % Mean of the average
    bestVP = mean(vPts(maxInds, :), 1);
    % Adding the offset
    bestVP = bestVP + [0, offset];
    
    %%%%%%%%%%%%%%%  Debugging %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Debugging the penalty
    debug = false;
    if(debug)
        figure(1); hold all
        %plot(penalty)
        plot(consensus);
        hold off
    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Debugging the candidate vanishing points
    debug = false;
    maxConsensus = max(consensus);
    if(debug)
        figure(1); hold off
        imshow(image)
        figure(1); hold on
        
        for i = 1:length(vPts)
            plot(vPts(i, 1), vPts(i, 2), 'o', 'LineWidth', ...
                                5 * consensus(i) / maxConsensus);
        end
        
        %plot(vPts(:, 1), vPts(:, 2), 'o', 'LineWidth', 2);
        plot(vPts(maxInds, 1), vPts(maxInds, 2), 'o', 'LineWidth', 2);
        plot(lines(:, [1 2])', offset + lines(:, [3 4])')
        %plot(lines(:, [1 2])', offset + lines(:, [3 4])')
        axis 'tight' 
    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Debugging the candidate vanishing points
    debug = true;
    if(debug)
        figure(1); hold off
        imshow(image)
        figure(1); hold on
        
%         for i = 1:length(vPts)
%             plot(vPts(i, 1), vPts(i, 2), 'o', 'LineWidth', ...
%                                 5 * consensus(i) / maxConsensus);
%         end
        
        %plot(vPts(:, 1), vPts(:, 2), 'o', 'LineWidth', 2);
        plot(bestVP(1), bestVP(2), 'o', 'LineWidth', 2);
        %plot(vPts(maxInds, 1), vPts(maxInds, 2), 'o', 'LineWidth', 2);
        plot(lines(bestConsensus, [1 2])', ...
                   offset + lines(bestConsensus, [3 4])', 'LineWidth', 2)
        %plot(lines(:, [1 2])', offset + lines(:, [3 4])')
        axis 'tight'
    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Best fit
    %[~, minInd] = min(penalty);
    %bestVP= vPts(minInd, :);
    %figure(1); plot(penalty)
    %noLines
    
    %figure(2); hold off, imshow(image)
    %figure(1); hold on, plot(allLines(:, [1 2])', allLines(:, [3 4])')
    %figure(2); hold on, plot(vPts(minInd, 1), vPts(minInd, 2), 'x', 'LineWidth', 10)
    %figure(2); plot(bestVPs(:, 1), bestVPs(:, 2), 'x')
    %bestVP = vPts(minInd, :);
    %figure(1); plot(penalty)
end

