CC=g++

INCLUDE = -I /home/awesomemlsp/src/caffe-rc2/include \
			    -I ${HOME}/src/caffe-rc2/src \
			    -I ${HOME}/src/caffe-rc2 \
                            -I ${HOME}/src/caffe-rc2/.build_release/src \
			    -I/usr/local/cuda-7.0/include \
			    -I ${HOME}/local/include

LIBRARY = -L/usr/lib/x86_64-linux-gnu/ -lprotobuf \
					-L/usr/lib/x86_64-linux-gnu/ -lglog \
					-L/usr/local/cuda-7.0/lib64/ -lcudart -lcublas -lcurand \
					-L/usr/local/lib/ -lopencv_core -lopencv_imgproc -lopencv_highgui \
					-L ${HOME}/src/caffe-rc2/build/lib/ -lcaffe

all:
	mkdir -p $(CITY_PATH)/build/cnn
	$(CC) $(INCLUDE) predict.cpp -o $(CITY_PATH)/build/cnn/predict $(LIBRARY)
	$(CC) $(INCLUDE) extract_features.cpp -o $(CITY_PATH)/build/cnn/extract_features $(LIBRARY)
	$(CC) $(INCLUDE) extract_features_text.cpp -o $(CITY_PATH)/build/cnn/extract_features_text $(LIBRARY)
	
