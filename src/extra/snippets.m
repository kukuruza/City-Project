% file snippet for renaming necessary files from a dir

myDir = [inDir 'frames/'];
list = dir (myDir);
for i = 1 : length(list)
    [~, name, ext] = fileparts(list(i).name);
    if isempty(name) || name(1) == '.', continue, end;
    if name(4) == '-'
        name2 = ['f0' name(2:end)];
        movefile ([myDir name ext], [myDir name2 ext]);
    end
end

