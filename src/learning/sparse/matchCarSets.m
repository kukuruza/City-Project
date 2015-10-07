function matches = matchCarSets (cars1, cars2, threshold)
% Given cars1 and cars2, return matches between them N x [i1, i2]
% Two cars are defined matched if their UoI is small.

% Naive algorithm -- assume there is only 1 good match if any for a bbox.

matches = [];

for i1 = 1 : length(cars1)
    car1 = cars1(i1);
    best_score = 0;
    best_i2 = [];
    for i2 = 1 : length(cars2)
        car2 = cars2(i2);
        score = getUoI (bbox2roi(car1.bbox), bbox2roi(car2.bbox));
        %fprintf ('%d %d %f\n', i1, i2, score);
        if score > best_score
            best_score = score;
            best_i2 = i2;
        end
    end
    if best_score > threshold
        matches = [matches; [i1, best_i2, best_score]];
    end
end
        