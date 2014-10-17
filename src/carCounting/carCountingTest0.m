function [newCarNumber Match] = carCountingTest0(image, cars)

carapps = cars;
seenCarapps = cars;
ProbCol = zeros(length(carapps), length(seenCarapps));
ProbHOG = zeros(length(carapps), length(seenCarapps));
ProbWeighted = zeros(length(carapps), length(seenCarapps));
ProbGeo = ...
[
 1 0.23 0.73 0.29 0.83 0.62 0.81 0.56; ...
 0.45 1 0.28 0.72 0.29 0.81 0.29 0.19; ...
 0.27 0.63 1 0.83 0.48 0.28 0.19 0.47; ...
 0.72 0.62 0.28 1 0.48 0.38 0.72 0.49; ...
 0.21 0.39 0.27 0.83 1 0.39 0.73 0.62; ...
 0.29 0.21 0.39 0.47 0.49 1 0.29 0.84; ...
 0.89 0.23 0.14 0.83 0.36 0.67 1 0.29; ...
 0.67 0.58 0.34 0.45 0.12 0.23 0.78 1;
];
% ProbGeo = GeometryEstimator.mutualProb (carapps, ML.seenCarapps, 1);
for i = 1 : length(carapps)
    carapp = carapps{i};      % all the cars in new frame
    for j = 1 : length(seenCarapps)
        seenCarapp = seenCarapps{j};   % all the cars in former frame
        [ProbCol(i,j), ProbHOG(i,j)] = AppProbTest(carapp, seenCarapp);
        ProbWeighted(i,j) = 0.5*ProbGeo(i,j) + 0.3*ProbCol(i,j) + 0.2*ProbHOG(i,j);
    end
end
Match = zeros(size(ProbWeighted));
for k = 1: length(carapps)
    [maxProb, index] = max(ProbWeighted(k,:));
    if(maxProb>0.8)
        Match(k,index) = 1;
    else
        Match(k,index) = 0;
    end
end
CountMatch = sum(sum(Match));
newCarNumber = length(carapps) - CountMatch;

end