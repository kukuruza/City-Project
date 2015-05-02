function s = matlab2pyTime (t)
% change matlab format [Y M D H M S.micros] to 'YYYY-MM-DD HH:MM:SS.micros'
    assert (isvector(t) && length(t) == 6);
    s = sprintf ('%04d-%02d-%02d %02d:%02d:%09.6f', t);
end