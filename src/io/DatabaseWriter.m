classdef DatabaseWriter < handle
    % Class to dump bboxes into a database
    % Essentially a wrapper for sqlite3, to get rid of those package
    % commands
    
    properties
        dbId; % Id for the database session
        
        carId; % Keeping track of number of cars added
        % attributes for writing matches
        matchId; % id given to set of matches for a car
    end
    
    methods
        % Constructor
        % Takes in a reference path from which the database is copied
        % Also, the output path
        function self = DatabaseWriter(dbPath, refPath)
            % Copying the db path from reference, deleting the tables
            copyfile(refPath, dbPath, 'f'); 
            self.dbId = sqlite3.open (dbPath);
            
            % clear the cars and matches tables
            sqlite3.execute(self.dbId, 'DELETE FROM cars');
            sqlite3.execute(self.dbId, 'DELETE FROM matches');
            
            % Initialize the count attributes
            self.carId = 0;
            self.matchId = 0;
        end
        
        % Write the bounding boxes into the database
        function saveBoxesToDatabase(self, bboxes, imagefile, carName)
            % Make sure the imagefile is in db
            query = 'SELECT COUNT(*) FROM images WHERE imagefile = ?';
            result = sqlite3.execute(self.dbId,query, imagefile);
            assert (result.count > 0);
            
            % Save the bounding boxes
            query = 'INSERT INTO cars(id, imagefile,name,x1,y1,width,height) VALUES (?,?,?,?,?,?)';
            for i = 1 : size(bboxes,1)
                bbox = bboxes(i,:);
                sqlite3.execute (self.dbId, query, self.carId, imagefile, carName, ...
                                bbox(1), bbox(2), bbox(3), bbox(4));
                            
                % Increment car id for each car added
                self.carId = self.carId;
            end
        end
        
        % Writing the matches to the database
        % We assume we are saving bounding rectangles for one single car
        % Will be called after the tracklet expires
        function saveMatchesToDatabase(self, videoPath, frameId, bboxes)
        % Usage:
        % DatabaseWriter.saveMatchesToDatabase(videoPath, frameId, bboxes);
        % 
        % Input:
        % videoPath = path to the video
        % frameId = the list of frameids in which the car is present
        % bboxes = the bounding box in the [x1, y1, width, height] format
        
            noMatches = length(frameId);
            % Verify data consistency
            assert(size(bboxes, 1) == noMatches);
            
            % Add cars along with adding matches
            carsQuery = 'INSERT INTO cars(id, imagefile,name,x1,y1,width,height) VALUES (?,?,?,?,?,?,?)';
            matchesQuery = 'INSERT INTO matches(match,carid) VALUES (?,?)';
            
            % Incrementing matches to include the current match
            self.matchId = self.matchId + 1;
            for i = 1:noMatches
                % Getting the pseudo image name
                imageName = fullfile(videoPath, sprintf('%06d', frameId(i)));
                
                % Adding cars
                sqlite3.execute (self.dbId, carsQuery, self.carId, imageName, 'vehicle', ...
                                bboxes(i,1), bboxes(i,2), bboxes(i,3), bboxes(i,4));
                            
                % Adding matches
                sqlite3.execute (self.dbId, matchesQuery, self.matchId, self.carId);
                
                self.carId = self.carId + 1;
            end
        end
        
        % Closing the db file
        function closeDatabase(self)
            if(~isempty(self.dbId))
                sqlite3.close(self.dbId);
            end
        end
    end
    
    % Static functions
    methods(Static)
        % Method to get the image listings in a database, given the
        % sql3lite handler for the database
        function imageFiles = getImageListing(dbId)
            query = 'SELECT imagefile FROM images';
            imageFiles = sqlite3.execute(dbId, query);
        end
        
        % Method to get mask file for a given image file, given the 
        function maskFile = getMaskFile(dbId)
            query = 'SELECT maskfile FROM images WHERE imagefile = ?';
            maskFile = sqlite3.execute(dbId, query, imagefile);
        end
    end
end

