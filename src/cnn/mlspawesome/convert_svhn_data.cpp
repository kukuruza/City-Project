//
// This script converts the SVHN dataset to the leveldb format used
// by caffe to perform classification.
// Usage:
//    convert_svhn_data input_folder output_db_file
// The SVHN dataset could be downloaded at
//    http://www.cs.toronto.edu/~kriz/cifar.html

#include <fstream>  // NOLINT(readability/streams)
#include <string>

#include "glog/logging.h"
#include "google/protobuf/text_format.h"
#include "leveldb/db.h"
#include "stdint.h"
#include "assert.h"

#include "caffe/proto/caffe.pb.h"

using std::string;

const int kSVHNSize = 54;
const int kSVHNImageNBytes = 8748;
const int kSVHNBatchSize = 8691;

void read_image(std::ifstream* file, int* label, char* buffer) {
  assert (sizeof(*label)== 4);
  *file >> *label;
  file->read(buffer, kSVHNImageNBytes);
  return;
}

void convert_dataset(const string& input_folder, const string& output_folder) {
  // Leveldb options
  leveldb::Options options;
  options.create_if_missing = true;
  options.error_if_exists = true;
  // Data buffer
  int label;
  char str_buffer[kSVHNImageNBytes];
  string value;
  caffe::Datum datum;
  datum.set_channels(3);
  datum.set_height(kSVHNSize);
  datum.set_width(kSVHNSize);

  LOG(INFO) << "Writing Training data";
  leveldb::DB* train_db;
  leveldb::Status status;
  status = leveldb::DB::Open(options, output_folder + "/svhn_train_d1_leveldb",
      &train_db);
  CHECK(status.ok()) << "Failed to open leveldb.";
  LOG(INFO) << "Training Batch ";
  snprintf(str_buffer, kSVHNImageNBytes, "/svhn_train_d1.bin");
  std::ifstream data_file((input_folder + str_buffer).c_str(),
      std::ios::in | std::ios::binary);
  CHECK(data_file) << "Unable to open train file";
  for (int itemid = 0; itemid < kSVHNBatchSize; ++itemid) {
    read_image(&data_file, &label, str_buffer);
    datum.set_label(label);
    datum.set_data(str_buffer, kSVHNImageNBytes);
    datum.SerializeToString(&value);
    snprintf(str_buffer, kSVHNImageNBytes, "%05d",
        kSVHNBatchSize + itemid);
    train_db->Put(leveldb::WriteOptions(), string(str_buffer), value);
  }
  

  LOG(INFO) << "Writing Testing data";
  leveldb::DB* test_db;
  CHECK(leveldb::DB::Open(options, output_folder + "/svhn_test_d1_leveldb",
      &test_db).ok()) << "Failed to open leveldb.";
  // Open files
  std::ifstream data_file1((input_folder + "/svhn_test_d1.bin").c_str(),
      std::ios::in | std::ios::binary);
  CHECK(data_file1) << "Unable to open test file.";
  for (int itemid = 0; itemid < kSVHNBatchSize; ++itemid) {
    read_image(&data_file1, &label, str_buffer);
    datum.set_label(label);
    datum.set_data(str_buffer, kSVHNImageNBytes);
    datum.SerializeToString(&value);
    snprintf(str_buffer, kSVHNImageNBytes, "%05d", itemid);
    test_db->Put(leveldb::WriteOptions(), string(str_buffer), value);
  }

  delete train_db;
  delete test_db;
}

int main(int argc, char** argv) {
  if (argc != 3) {
    printf("This script converts the SVHN dataset to the leveldb format used\n"
           "by caffe to perform classification.\n"
           "Usage:\n"
           "    convert_svhn_data input_folder output_folder\n"
           "Where the input folder should contain the binary batch files.\n"
           "The SVHN dataset could be downloaded at\n"
           "    http://www.cs.toronto.edu/~kriz/cifar.html\n"
           "You should gunzip them after downloading.\n");
  } else {
    google::InitGoogleLogging(argv[0]);
    convert_dataset(string(argv[1]), string(argv[2]));
  }
  return 0;
}
