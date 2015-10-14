function s = matlabDatetime2dbTime (t)
% change matlab datetime format to our 'YYYY-MM-DD HH:MM:SS.micros'

    parser = inputParser;
    addRequired (parser, 't', @(x) isa(x, 'datetime'));
    parse (parser, t);

    s = datestr(t, 'yyyy-mm-dd HH:MM:SS.FFF000');
end