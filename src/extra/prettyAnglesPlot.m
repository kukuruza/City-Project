A = dlmread('/Users/evg/projects/City-Project/etc/tmp.csv');
scatter(A(:,1), A(:,2), 15, A(:,3));
xlim([-180, 180])

