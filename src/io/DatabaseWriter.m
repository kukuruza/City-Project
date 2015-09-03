classdef DatabaseWriter < handle
    % Class to dump bboxes into a database
    % Essentially a wrapper for sqlite3, to get rid of those package
    % commands
    
    properties
        dbPath; % Path of the database
        dbId; % Id for the database session
        carId = 1;  % Id for car
        imageId = 1; % Id for image
        setId; % Id for the set
    end
    
    methods
        % Constructor
        % Takes in a reference path from which the database is copied
        % Also, the output path
        function self = DatabaseWriter(dbPath, refPath, imageSetPath)
            self.dbPath = dbPath;
            
            % Copying the db path from reference, deleting the tables
            copyfile(refPath, dbPath, 'f'); 
            self.dbId = sqlite3.open (dbPath);
            
            % clear the cars table
            sqlite3.execute(self.dbId, 'DELETE FROM cars');
            
            % Clear the images table
            sqlite3.execute(self.dbId, 'DELETE FROM images');
            
            sqlite3.close(self.dbId);
            
            % Opening the db file for further writing
            self.dbId = sqlite3.open (dbPath);
            
            % Search for the set id
            self.setId = self.getSetId(imageSetPath);
        end
        
        % Write the bounding boxes into the database
        function saveBoxesToDatabase(self, bboxes, frameId, imSize)
            % First save the frame
            query = 'INSERT INTO images(imageid, setid, setentry, width, height) VALUES (?,?,?,?,?)';
            sqlite3.execute(self.dbId, query, self.imageId, self.setId, frameId, ...
                                    imSize(1), imSize(2));
            
            % Now save the bounding boxes
            for i = 1 : size(bboxes,1)
                bbox = bboxes(i,:);
                query = 'INSERT INTO cars(id,imageid,name,x1,y1,width,height) VALUES (?,?,?,?,?,?,?)';
                sqlite3.execute(self.dbId, query, self.carId, self.imageId, ...
                                    'candidate', ...
                                    bbox(1), bbox(2), bbox(3), bbox(4));

                self.carId = self.carId + 1;
            end
            
            % Increment the image
            self.imageId = self.imageId + 1;
        end
        
        % Opening the db file
        function openDatabase(self)
            if(~isempty(self.dbPath) && isempty(self.dbId))
                self.dbId = sqlite3.open(self.dbPath);
            end
        end
        
        % Closing the db file
        function closeDatabase(self)
            if(~isempty(self.dbId))
                sqlite3.close(self.dbId);
            end
        end
        
        % Finding the set id of the current frame
        function[setId] = getSetId(self, imageSetPath)
            query = 'SELECT setid FROM sets WHERE imageset = ?';
            result = sqlite3.execute(self.dbId, query, imageSetPath);
            setId = result.setid;
        end
    end
end

