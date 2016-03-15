import sys, os, os.path as op
import json
import logging
import bpy
from learning.helperSetup import atcity, setupLogging, setParamUnlessThere

''' Make all frame postprocessing and combination in RENDER_DIR '''

WORK_RENDER_DIR = atcity('augmentation/blender/current-frame')
RENDER_NAME         = 'out.png'
CORRECTION_FILENAME = 'color-correction.json'

WORK_DIR = '%s-%d' % (WORK_RENDER_DIR, os.getppid())
WORK_DIR_SUFFIX = '-%d' % os.getppid()

correction_path = op.join(WORK_DIR, CORRECTION_FILENAME)


image_node = bpy.context.scene.node_tree.nodes['Image-Background'].image
path = image_node.filepath
index = path.find('current-frame') + len('current-frame')
image_node.filepath = path[:index] + WORK_DIR_SUFFIX + path[index:]

image_node = bpy.context.scene.node_tree.nodes['Image-Cars-Only'].image
path = image_node.filepath
index = path.find('current-frame') + len('current-frame')
image_node.filepath = path[:index] + WORK_DIR_SUFFIX + path[index:]

image_node = bpy.context.scene.node_tree.nodes['Image-Normal'].image
path = image_node.filepath
index = path.find('current-frame') + len('current-frame')
image_node.filepath = path[:index] + WORK_DIR_SUFFIX + path[index:]


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
# TODO: should delete bpy.data.scenes['Scene'].render.filepath ??
bpy.data.scenes['Scene'].render.filepath = atcity(op.join(WORK_DIR, RENDER_NAME))
bpy.ops.render.render (write_still=True) 


