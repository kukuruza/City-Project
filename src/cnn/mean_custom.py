import numpy
import sys
a = numpy.zeros((3,int(sys.argv[1]),int(sys.argv[2])))
#a = a*128
numpy.save(sys.argv[3],a)
