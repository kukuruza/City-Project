function cars = mergeCars (cars, varargin)
%MERGECARS combines cars from different detectors
% Algorithm is similar to the non-maximum suppression.
%
% Input:
%     cars - a vector of objects of type car
% Parameters:
%     'overlap', 0.3 - overlap that is enough for merging
%

parser = inputParser;
addRequired (parser, 'cars', @(x) isa(x, 'Car') && isvector(x));
addParameter(parser, 'overlap', 0.8, @isscalar);
parse (parser, cars, varargin{:});
parsed = parser.Results;

N = length(cars);

% simple case
if N == 0, return, end

% get all boxes and scores
roi = zeros(N,4);
scores = zeros(N,1);
for i = 1 : N
    roi(i,:) = cars(i).getROI();
    scores(i) = cars(i).score;
end

x1 = roi(:,1);
y1 = roi(:,2);
x2 = roi(:,3);
y2 = roi(:,4);
 
% area of each box
areas = (x2-x1+1) .* (y2-y1+1);

[~, I] = sort(scores);
 
pick = scores*0;
counter = 1;
while ~isempty(I)
  
  last = length(I);
  i = I(last);  
  pick(counter) = i;
  counter = counter + 1;
  
  xx1 = max(x1(i), x1(I(1:last-1)));
  yy1 = max(y1(i), y1(I(1:last-1)));
  xx2 = min(x2(i), x2(I(1:last-1)));
  yy2 = min(y2(i), y2(I(1:last-1)));
  
  w = max(0.0, xx2-xx1+1);
  h = max(0.0, yy2-yy1+1);
  
  o = w.*h ./ areas(I(1:last-1));
  
  I([last; find(o > parsed.overlap)]) = [];
end
 
pick = pick(1:(counter-1));

cars = cars(pick);