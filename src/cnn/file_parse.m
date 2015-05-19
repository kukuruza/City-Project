names = importdata('names11.txt');
%names = names(1:end-2);
labels = importdata('test11.txt',' ');
labels = labels(:,2:3);
labels_cell = num2cell(labels);
fileID = fopen('out.txt','w');
formatSpec = '%s %d %0.7f \n';
out = [names labels_cell];
[nrows,ncols] = size(out);
for row = 1:nrows
    fprintf(fileID,formatSpec,out{row,:});
end