function manuallyFilterDb (db_in_file, varargin)

parser = inputParser;
addRequired(parser,  'db_out_file', @ischar);
addParameter(parser, 'db_in_file', '', @ischar);
addParameter(parser, 'assignName', '', @ischar);
addParameter(parser, 'verbose', 0, @isscalar);
parse (parser, db_in_file, varargin{:});
parsed = parser.Results;
verbose = parsed.verbose;

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;

sqlite3.open([CITY_DATA_PATH db_file]);
image_entries = sqlite3.execute('SELECT * FROM images');


i = 1;
while i <= length(image_entries)
    image_entry = image_entries(i);
    
    %query_str = 'SELECT * FROM cars WHERE imagename = ' + image_entry.imagefile;
    %car_entries = sqlite3.execute(query_str);
    
    ghost = imread ([CITY_DATA_PATH image_entry.imagefile]);
    imshow(ghost)
    
    

