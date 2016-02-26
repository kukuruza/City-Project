function lines = readList (filepath)
% read a list of strings from a file. Empty lines are removed

EolCharacter = 10;

% count the number of lines
txt = fileread(filepath);
numLines = sum (txt == EolCharacter) + 1;


fid = fopen(filepath);

% read line by line
lines = cell (numLines, 1);
for i = 1 : 100000000
    if feof(fid), break, end
    line = fgets(fid);
    line (line == EolCharacter) = [];
    if isempty(line) || line(1) == '#', continue, end
    lines{i} = line;
end

fclose(fid);

% remove empty lines
lines = lines (~cellfun(@isempty, lines));
