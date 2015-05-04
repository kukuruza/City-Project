function dbCreate (db_path)

clear sqlite

sqlite3.open(db_path);

pause(1)

sqlite3.execute(['CREATE TABLE images' ...
                 '(imagefile TEXT PRIMARY KEY, ' ...
                 'src TEXT, ' ...
                 'width INTEGER, ' ...
                 'height INTEGER, ' ...
                 'ghostfile TEXT, ' ...
                 'maskfile TEXT, ' ...
                 'time TIMESTAMP NOT NULL ' ...
                 ');' ...
                 ]);
             
sqlite3.execute(['CREATE TABLE cars ' ...
                '(id INTEGER PRIMARY KEY, ' ...
                'imagefile INTEGER, ' ...
                'name TEXT, ' ...
                'x1 INTEGER, ' ...
                'y1 INTEGER, ' ...
                'width INTEGER, ' ...
                'height INTEGER, ' ...
                'offsetx INTEGER, ' ...
                'offsety INTEGER, ' ...
                'yaw REAL, ' ...
                'pitch REAL, ' ...
                'color TEXT' ...
                ');' ...
                ]);

sqlite3.execute(['CREATE TABLE IF NOT EXISTS polygons ' ...
                 '(id INTEGER PRIMARY KEY, ' ...
                 'carid TEXT, ' ...
                 'x INTEGER, ' ...
                 'y INTEGER ' ...
                 ');' ...
                 ]);

pause(2)
sqlite3.close();

pause(2)

% test it. If no error then ok
sqlite3.open(db_path);
sqlite3.execute('SELECT * FROM cars');
sqlite3.execute('SELECT * FROM images');
sqlite3.close();
            
