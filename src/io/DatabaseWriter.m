classdef DatabaseWriter < handle
    % Class to dump bboxes into a database
    % Essentially a wrapper for sqlite3, to get rid of those package
    % commands
    
    properties
        dbPath; % Path of the database
        dbId; % Id for the database session
        carId;  % Id for car
    end
    
    methods
        % Constructor
        % Takes in a reference path from which the database is copied
        % Also, the output path
        function self = DatabaseWriter(dbPath, refPath)
            self.dbPath = dbPath;
            
            % Copying the db path from reference, deleting the tables
            copyfile(refPath, dbPath, 'f'); 
            self.dbId = sqlite3.open (dbPath);
            sqlite3.execute(self.dbId, 'DELETE FROM cars');
            sqlite3.close(self.dbId);
            
            % Opening the db file for further writing
            self.dbId = sqlite3.open (dbPath);
        end
        
        % Write the bounding boxes into the database
        function saveBoxesToDatabase(self, bboxes, imageName)
            for i = 1 : size(bboxes,1)
                bbox = bboxes(i,:);
                query = 'INSERT INTO cars(id,imagefile,name,x1,y1,width,height) VALUES (?,?,?,?,?,?,?)';
                sqlite3.execute(self.dbId, query, self.carId, imageName, 'candidate', ...
                                    bbox(1), bbox(2), bbox(3), bbox(4));

                self.carId = self.carId + 1;
            end
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
    end
end

