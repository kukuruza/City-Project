function [ splinePts ] = drawUniformSpline(controlPts, resolution)
    % Function to draw uniform cubic B-spline for the given set of control
    % points
    % The user can also control the resolution for the normalized parameter
    
    t = 0:resolution:1;
    B = 1/6 * [-1 3 -3 1; 3 -6 0 4; -3 3 3 1; 1 0 0 0];
    Bt = B * [t.^3; t.^2 ; t; ones(1, length(t))];
    
    noCurves = size(controlPts, 1)-3;
    noDims = size(controlPts, 2);
    splinePts = zeros(noCurves * length(t), noDims);
    
    for i = 1:noCurves
        splinePts((i-1)*length(t) + (1:length(t)), :) = ...
                                            (controlPts(i:i+3, :)' * Bt)';
    end
end

