City-Project
============

Analyze traffic given a set of optical cameras in urban areas


### Referring to data
The goal is to allow to use the same code at different machines. The global variable `CITY_DATA_PATH` is set individually by everyone according to the locations of data on their computers. It is set in file `rootPathsSetup.m`, which is not in Git.

```Matlab
% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% change ../.. to the relative path of the file
run '../../rootPathsSetup.m';

% then when necessary, refer to the data location as
myDirectory = 'myDir/mySubdir';
myDataPath = [CITY_DATA_PATH myDirectory];
```

### Naming conventions

```Matlab
point = [y x]
bbox  = [x1 y1 width height]
roi   = [y1 x1 y2 x2]
```

### Recommendations for function interface and parsing of input
This is a minimal example

```Matlab
% varargin - are just other options, they can be skipped
function result = func (important1, varargin) 
    parser = inputParser;
    addRequired(parser, 'important1', @(x) isa(x, 'ClassName'));
    addParameter(parser, 'option1', -1, @isscalar);
    parse (parser, important1, varargin{:});
    parsed = parser.Results;

    % retrive the parsed values
    import1 = parsed.important1;
    opt1 = parsed.option1;
end
```
