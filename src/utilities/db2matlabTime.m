function vect = db2matlabTime (t)
% apparently it was probably easier to store datetime as string in matlab
    vect = datevec(datenum(t));
    