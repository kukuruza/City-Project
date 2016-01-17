import sys, os, os.path as op
import bpy

''' Make all frame postprocessing and combination in RENDER_DIR '''

def atcity(path):
    return op.join(os.getenv('CITY_DATA_PATH'), path)

RENDER_DIR = atcity('augmentation/render/current-frame')
OUT_FILENAME = 'out.png'

# render
bpy.data.scenes['Scene'].render.filepath = op.join(RENDER_DIR, OUT_FILENAME)
bpy.ops.render.render (write_still=True) 
