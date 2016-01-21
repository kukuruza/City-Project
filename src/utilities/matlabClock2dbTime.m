function s = matlabClock2dbTime (t)
% change matlab format [Y M D H M S.micros] to 'YYYY-MM-DD HH:MM:SS.mic'
    assert (isvector(t) && length(t) == 6);
    s = sprintf ('%04d-%02d-%02d %02d:%02d:%09.3f', t);
end