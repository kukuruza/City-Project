blender_path="/Applications/blender.app/Contents/MacOS/blender"

traffic_template=$CITY_DATA_PATH/augmentation/traffic/traffic-fr*.json
render_dir=$CITY_DATA_PATH/augmentation/render
render_current_dir=$render_dir/current-frame

# for each traffic json file
for traffic_frame in $traffic_template; do

    # copy frame json to file to traffic-current.json
    traffic_dirname=$(dirname $traffic_frame)
    cp $traffic_frame $traffic_dirname/traffic-current-frame.json

    # run blender on it
    $blender_path --background --python $CITY_PATH/src/augmentation/renderScene.py

    # give the rendered dir a unique name 
    #   (traffic_frame name has pattern traffic-frXXXXXX.json)
    name=$(basename $traffic_frame)
    mv $render_current_dir $render_dir/render-${name:10:6}
done