#include <cstring>
#include <cstdlib>
#include <vector>
#include <string>
#include <iostream>
#include <stdio.h>
#include <assert.h>
#include "caffe/caffe.hpp"
#include "caffe/util/io.hpp"
#include "caffe/blob.hpp"

#include "tclap/CmdLine.h"

using namespace caffe;
using namespace std;
using namespace TCLAP;

int main(int argc, char** argv)
{
    CmdLine cmd ("Deployment of database on disk with trained caffe model.");

    ValueArg<string> cmdInModel ("", "model", "trained .caffemodel file", true, "", "path", cmd);
    ValueArg<string> cmdInNet ("", "net", "deployment net .prototxt file", true, "", "path", cmd);
    ValueArg<string> cmdOut ("", "output", ".txt file with predicted labels", false, "/dev/null", "path", cmd);
    SwitchArg cmdCPU ("", "cpu", "use cpu", cmd);

    // parse input
    cmd.parse(argc, argv);
    bool useCPU = cmdCPU.getValue();
    string inModelPath = cmdInModel.getValue();
    string inNetPath = cmdInNet.getValue();
    string outPath = cmdOut.getValue();

    // setting CPU or GPU
    if (useCPU)
    {
        LOG(INFO) << "Using CPU";
        Caffe::set_mode(Caffe::CPU);
    }
    else
    {
        Caffe::set_mode(Caffe::GPU);
        int device_id = 0;   // always zero now.
        Caffe::SetDevice(device_id);
        LOG(INFO) << "Using GPU #" << device_id;
    }
        
    // load net
    Net<float> net (inNetPath.c_str(), caffe::TEST);

    // Load pre-trained net (binary proto)
    net.CopyTrainedLayersFrom (inModelPath.c_str());

    float loss = 0.0;
    vector<Blob<float>*> results = net.ForwardPrefilled(&loss);
    LOG(INFO) << "Result size: "<< results.size();

    // Log how many blobs were loaded
    LOG(INFO) << "Blob size: "<< net.input_blobs().size();


    // Get probabilities
    const boost::shared_ptr<Blob<float> >& probLayer = net.blob_by_name("prob");
    const float* probs_out = probLayer->cpu_data();
    // Get argmax results
    const boost::shared_ptr<Blob<float> >& argmaxLayer = net.blob_by_name("output");
    const float* argmaxs = argmaxLayer->cpu_data();
    // Get accuracy
//    const boost::shared_ptr<Blob<float> >& accuracyLayer = net.blob_by_name("accuracy");
//    const float* accuracies = accuracyLayer->cpu_data();

    ofstream ofs (outPath.c_str());
    
    // Display results
    LOG(INFO) << "---------------------------------------------------------------";
    for (int i = 0; i < argmaxLayer->num(); i++) 
    {
        ofs << i << " " 
            << argmaxs[i*argmaxLayer->height() + 0] << " "
            << probs_out[i*probLayer->height() + 0] << endl;
        LOG(INFO) << "Pattern:" << i 
            << " class:" << argmaxs[i*argmaxLayer->height() + 0]
//            << " accuracy:" << accuracies[i*argmaxLayer->height() + 0]
            << " prob=" << probs_out[i*probLayer->height() + 0];
    }

    ofs.close();

    return 0;
}
