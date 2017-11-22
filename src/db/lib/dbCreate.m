function c = dbCreate (db_path)

clear sqlite

if exist(db_path, 'file')
    delete(db_path);
end
if ~exist(fileparts(db_path), 'dir')
    mkdir(fileparts(db_path));
end

fprintf ('will create db file at: %s.\n', db_path);
c = sqlite3.open(db_path);

sqlite3.execute(c, ['CREATE TABLE images' ...
                 '(imagefile TEXT PRIMARY KEY, ' ...
                 'src TEXT, ' ...
                 'width INTEGER, ' ...
                 'height INTEGER, ' ...
                 'ghostfile TEXT, ' ...
                 'maskfile TEXT, ' ...
                 'time TIMESTAMP NOT NULL ' ...
                 ');' ...
                 ]);
             
sqlite3.execute(c, ['CREATE TABLE cars ' ...
                '(id INTEGER PRIMARY KEY, ' ...
                'imagefile INTEGER, ' ...
                'name TEXT, ' ...
                'x1 INTEGER, ' ...
                'y1 INTEGER, ' ...
                'width INTEGER, ' ...
                'height INTEGER, ' ...
                'score REAL, ' ...
                'yaw REAL, ' ...
                'pitch REAL, ' ...
                'color TEXT' ...
                ');' ...
                ]);

sqlite3.execute(c, ['CREATE TABLE IF NOT EXISTS matches ' ...
                 '(id INTEGER PRIMARY KEY, ' ...
                 'match INTEGER, ' ...
                 'carid INTEGER' ...
                 ');']);
            
% sqlite3.execute(['CREATE TABLE IF NOT EXISTS polygons ' ...
%                  '(id INTEGER PRIMARY KEY, ' ...
%                  'carid TEXT, ' ...
%                  'x INTEGER, ' ...
%                  'y INTEGER ' ...
%                  ');' ...
%                  ]);
 
% test it. If no error then ok
sqlite3.execute(c, 'SELECT * FROM cars');
sqlite3.execute(c, 'SELECT * FROM images');
            