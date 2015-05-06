function safeCopyFile (in, out)
% make a copy of a file after making the back up of the original
    if exist(out)
        warning ('saveCopyFile: will back up existing output file');
        copyfile(out, [out '.backup']);
    end
    copyfile (in, out);
end