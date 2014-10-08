classdef Lane
    %LANE : contains details of the lane
    %   Detailed explanation goes here
    %   Each lane is assumed straight for now, with attributes denoting 
    %   endpoints (optional) or equation on image plane
    
    properties
        rightPts; %Right extreme points (possibly three or more)
        leftPts; %Left extreme points for the lane
        rightEq; %Equation of the right extreme
        leftEq; %Equation of the left extreme
        
        direction; %Direction is manually assigned either in/out
    end
    
    methods
        %Constructors for the lane class
        function[obj] = Lane(rPts, lPts, roadDir)
            obj.rightPts = rPts;
            obj.leftPts = lPts;
            obj.direction = roadDir;
            
            %Finding the equation
            obj.rightEq = (polyfit(obj.rightPts(1,:), obj.rightPts(2,:), 1))';
            obj.leftEq = (polyfit(obj.leftPts(1,:), obj.leftPts(2,:), 1))';
        end
        
        %Overload of constructor, not functional in matlab
        %function[obj] = Lane(rEq, lEq, roadDir)
        %    obj.rightEq = rEq;
        %    obj.leftEq = lEq;
        %    obj.direction = roadDir;  
        %end
    end
end

