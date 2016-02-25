import sys, os, os.path as op
import json
import logging
import bpy
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/augmentation'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import atcity, setupLogging, setParamUnlessThere

''' Make all frame postprocessing and combination in RENDER_DIR '''

WORK_DIR = atcity('augmentation/blender/current-frame')
RENDER_NAME         = 'out.png'
CORRECTION_FILENAME = 'color-correction.json'


correction_path = op.join(WORK_DIR, CORRECTION_FILENAME)
if op.exists(correction_path):
    frame_info = json.load(open( correction_path ))

    # compensate for color changes throughout a video
    hsv_node = bpy.context.scene.node_tree.nodes['Hue-Saturation-Compensation']
    # print ('changed hue,sat from %.2f,%.2f' % \
    #                (hsv_node.color_hue, hsv_node.color_saturation))
    hsv_node.color_hue        += frame_info['dh']
    hsv_node.color_saturation += frame_info['ds']
    #hsv_node.color_value      += frame_info['dv']
    # print ('changed hue,sat to %.2f,%.2f' % \
    #                (hsv_node.color_hue, hsv_node.color_saturation))

# render and save
bpy.data.scenes['Scene'].render.filepath = atcity(op.join(WORK_DIR, RENDER_NAME))
bpy.ops.render.render (write_still=True) 


