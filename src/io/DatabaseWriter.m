classdef DatabaseWriter < handle
    % Class to dump bboxes into a database
    % Essentially a wrapper for sqlite3, to get rid of those package
    % commands
    
    properties
        dbId; % Id for the database session
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
        end
        
        % Write the bounding boxes into the database
        function saveBoxesToDatabase(self, bboxes, imagefile, carName)
            % Make sure the imagefile is in db
            query = 'SELECT COUNT(*) FROM images WHERE imagefile = ?';
            result = sqlite3.execute(self.dbId,query, imagefile);
            assert (result.count > 0);
            
            % Save the bounding boxes
            for i = 1 : size(bboxes,1)
                bbox = bboxes(i,:);
                query = 'INSERT INTO cars(imagefile,name,x1,y1,width,height) VALUES (?,?,?,?,?,?)';
                sqlite3.execute (self.dbId, query, imagefile, carName, ...
                                 bbox(1), bbox(2), bbox(3), bbox(4));
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

