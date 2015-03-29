classdef Stabilizer < handle
    %STABILIZER Summary of this class goes here
    %   Detailed explanation goes here
    
    properties (Hidden)
        % Parameter for finding the feature points
        ptThresh = 0.1;
        refFrame;
        refFeatures;
        refPts;
    end
    
    methods
        % Constructor
        % Takes in the original reference frame
        function obj = Stabilizer(refFrame)
            % Setting the reference frame, extracting features for it
            % Used to stabilize the remaining frames
            obj.setReferenceFrame(refFrame);
        end
       
        % Main function of the module, to stabilize the incoming image with
        % respect to a reference
        function [stableFrame, homography] = stabilizeFrame(obj, curFrame)
            curGray = rgb2gray(curFrame);
   
            curPts = detectFASTFeatures(curGray, 'MinContrast', obj.ptThresh);
            % Extract FREAK descriptors for the corners
            [curFeatures, curPts] = extractFeatures(curGray, curPts);

            % Matching the features
            indexPairs = matchFeatures(obj.refFeatures, curFeatures);
            refInliers = obj.refPts(indexPairs(:, 1), :);
            curInliers = curPts(indexPairs(:, 2), :);

            % Using homography to get the inlier points on the ground
            [~, homography] = ransacPlane2D(refInliers.Location', ...
                                                    curInliers.Location');
            stableFrame = warpH(curFrame, double(homography), size(curFrame));
        end
        
        % Adjusting the parameter
        function adjustFeatureParameter(obj, threshold)
            obj.ptThresh = threshold;
        end
        
        % Registering the different reference frame
        function setReferenceFrame(obj, refFrame)
            refGray = rgb2gray(refFrame);
            obj.refPts = detectFASTFeatures(refGray, 'MinContrast', obj.ptThresh);
            [obj.refFeatures, obj.refPts] = ...
                                        extractFeatures(refGray, obj.refPts);
        end 
    end
end