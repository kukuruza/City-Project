dir_path="$CITY_DATA_PATH/learning/violajones/byname_24x18/"

cd $dir_path

bg_in_path="$CITY_DATA_PATH/clustering/neg_car_circle/negatives_for_all/*.jpg"
bg_out_name="bg-3.txt"

echo $bg_in_path
echo $bg_out_name
ls -1 $bg_in_path > $bg_out_name

name="car-train"
w=24
h=18
#opencv_createsamples -vec $name.vec -info $name.dat -num 350 -bgcolor 128 -w $w -h $h

model_name="model-car-3"
mkdir $model_name
mem=1000
opencv_traincascade -data $model_name -vec $name.vec -bg $bg_out_name -numPos 380 -numNeg 1000 -w $w -h $h -precalcValBufSize $mem -precalcIdxBufSize $mem
