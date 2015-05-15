
#This script runs a forward pass on the Convolutional Neural Network model to test data
#Predicted label is written to file. Besides that, probability of each label can be obtained from out['prob'].
#Here 'prob' is the name for SoftMax layer
#The script failed to load caffe module. The problem was solved by running from $CAFFE_ROOT/python folder
import caffe
import sys

#Create Net. Param 1: same network as train, but data layer takes test data Param 2: model snapshot at any iteration
net = caffe.Net('~/src/caffe-rc2/examples/city/city_quick_solver.prototxt', sys.argv[1])
out = net.forward()
f = open('/home/ubuntu/pred'+sys.argv[1]+'.csv','w')
f.write('Id,Category\n')
nlabel = 1
for x in range(0,len(out['prob'])):
	probs = out['prob'][x].tolist()
	line = str(nlabel)+','+str(probs.index(max(probs)) + 1)
	f.write(line)
	if nlabel < 15000:
	 f.write('\n')
	nlabel += 1
f.close()
