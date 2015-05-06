City-Project
============

Analyze traffic given a set of optical cameras in urban areas


## Conventions

#### Referring to data
The goal is to allow to use the same code on different machines. The environmentals variables `CITY_PATH` and `CITY_DATA_PATH` are set individually by everyone according to the locations of git repo and data on their computers. For example, on Unix (Linux and OS X) they can be set in file `~/.bash_profile`.

```Matlab
% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to path
cd (fileparts(mfilename('fullpath')));        % change dir to this script 

% then when necessary, refer to the data location as
myDirectory = 'myDir/mySubdir';
myDataPath = [CITY_DATA_PATH myDirectory];
```

#### Meaning of common variables

```Matlab
point = [y x]
bbox  = [x1 y1 width height]
roi   = [y1 x1 y2 x2]
```

#### Recommendations for function interface and parsing of input
`inputParser` standard Matlab class is recommended (http://www.mathworks.com/help/matlab/ref/inputparser-class.html). `addParameter` is preferred to `addOptional`. Here is a minimal example

```Matlab
% varargin - are just other options, they can be skipped by a user
function result = func (important1, varargin) 
    parser = inputParser;
    addRequired(parser, 'important1', @(x) isa(x, 'ClassName'));
    addParameter(parser, 'option1', -1, @isscalar);
    parse (parser, important1, varargin{:});
    parsed = parser.Results;

    % retrieve the parsed values
    import1 = parsed.important1;
    opt1 = parsed.option1;
end
```

#### Names of files

__Tests vs Examples.__ Matlab unit tests http://www.mathworks.com/help/matlab/matlab-unit-test-framework.html?refresh=true should have names `MyClassTest.m`. Examples that illustrate how a unit works, and may also be used for testing should have name `MyClassDemo.m`.

__Scripts, Classes, functions.__ Names of scripts and classes should be capitalized, names of functions should start with lower-case.


