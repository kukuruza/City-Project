

% data preparation
% The format of training and testing data file is:
% <label> <index1>:<value1> <index2>:<value2> ...


labels = ones(6579, 1);
features_sparse = sparse(PosCase);
libsvmwrite('aaa', labels, features_sparse);
load('NegCase.mat')
labels2 = zeros(4000, 1);
features_sparse2 = sparse(NegCase);
libsvmwrite('bbb', labels2, features_sparse2);
l3 = [labels; labels2];
f3 = [features_sparse; features_sparse2];
libsvmwrite('Data', l3, f3);
[label_vector, instance_matrix] = libsvmread('Data');

% cross_validaation
model = train(label_vector, instance_matrix, ['-v 10']);
[predicted_label, accuracy] = predict(testing_label_vector, testing_instance_matrix, model, [ 'liblinear_options');
% try different kernel
model = train(label_vector, instance_matrix, ['-v 10']);