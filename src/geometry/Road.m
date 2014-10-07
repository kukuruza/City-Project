classdef Road < handle
    %ROAD : Hold information for the road
    %   Road the following properties:
    %   Cell of lanes ()
    %  
    
    properties
        %Attributes for the road
        lanes;       %cell of lanes objects 
        vanishPt;    %Vanishing point for 
    
        %Assumed velocity for the road (need some source, probably estimate
        %it using detections)
        roadVelMu =  40; % Mean
        roadVelVar = 5; % Variance

        %Height of the camera (need some source)
        camHeightMu = 6;
        camHeightVar = 0;

        %Height of the car (sedan for now, need some source)
        carHeightMu = 1.46; %metres
        carHeightVar = 0.2; %metres

    end
    
    methods
        %% Constructor
        function[obj] = Road(matFile)
            %Initialization for the road object using manually marked
            %points available in the matfile
            %Initializations
            load(matFile);
            obj.lanes = cell(0, 1);
            obj.vanishPt = [0; 0];
            
            for i = 1:noLanes
               leftExt = [xPts((3*(i-1)+1):(3*i))'; yPts((3*(i-1)+1):(3*i))'];
               rightExt = [xPts((3*i+1):(3*(i+1)))'; yPts((3*i+1):(3*(i+1)))'];
               newLane = Lane(leftExt, rightExt, 'in');  
               obj.addLane(newLane);
            end

            obj.setVanishPoint();
        end
        
        %Overload of constructor, not functional in matlab
        %function[obj] = Road(roadLanes, vanPoint)
        %    obj.lanes = roadLanes;
        %    obj.vanishPt = vanPoint;
        %end
        
        %% Adding new lanes
        function[] = addLane(obj, newLane)
            %Sequentially adding lanes
            %Checking if lane already exists
            %(later)
            obj.lanes{length(obj.lanes) + 1} = newLane;
        end

        %% Setting the vanishing point
        function[] = setVanishPoint(obj)
           obj.vanishPt = obj.findVanishPoint(); 
        end
        
        %% Finding the vanishing point
        function[vanPoint] = findVanishPoint(obj)
            %Currently from marked lanes, can be automated using existing work
            %available for vanish point detection (for later)
            %Collecting all the lines to solve for their concurrency point
            %Lanes are assumed to be parallel in 3D world
            parLines = zeros(2, size(obj.lanes, 1)+1);
            
            for i = 1:size(obj.lanes, 1)
               parLines(:, i) = obj.lanes{i}.leftEq; 
            end
            parLines(:, end) = obj.lanes{end}.rightEq; 
            
            %Evaluating the vanishing point
            vanPoint = (polyfit(-1*parLines(1,:), parLines(2, :), 1))';
        end
        
        %% Debugging methods
        function[markedImg] = drawLanesOnImage(obj, image)
            markerInserter = vision.MarkerInserter('Size', 1, 'BorderColor','Custom','CustomBorderColor', uint8([0 0 255]));
            markerPts = [];
            for i = 1:length(obj.lanes)
               xLine = 1:size(image, 1);
               xLine = xLine';
               yLine = obj.lanes{i}.rightEq(1) * xLine + obj.lanes{i}.rightEq(2);
               markerPts = [markerPts; uint8(xLine) uint8(yLine)]; 
               yLine = obj.lanes{i}.leftEq(1) * xLine + obj.lanes{i}.leftEq(2);
               markerPts = [markerPts; uint8(xLine) uint8(yLine)]; 
            end
            %Marking the lanes
            markedImg = step(markerInserter, image, markerPts);
            %Marking the vanishing point with red
            markerInserter = vision.MarkerInserter('Size', 4, 'BorderColor','Custom','CustomBorderColor', uint8([255 0 0]));
            markedImg = step(markerInserter, markedImg, uint8(obj.vanishPt')); 
        end
    end
end