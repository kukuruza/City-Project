To try db dataset reader:
```
python src/segmentation/readData.py \
  --db_file augmentation/video/cam572/Feb23-09h-Oct15/test20.db 
  --use_fraction 0.5
```

To deploy a trained network
```
python src/segmentation/deploy.py \
  --in_model_path $HOME/src/tensorflow-fcn/vgg16.npy \
  --image_path    $HOME/src/tensorflow-fcn/test_data/tabby_cat.png
```

To train a network
```
python src/segmentation/train.py \
  --init_model_path $HOME/src/tensorflow-fcn/vgg16.npy \
  --train_db_file   augmentation/video/cam572/Feb23-09h-Oct15/train.db \
  --test_db_file    augmentation/video/cam572/Feb23-09h-Oct15/test.db \
  --out_dir         data/segmentation/models
```
