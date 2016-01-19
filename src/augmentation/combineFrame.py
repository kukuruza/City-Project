import sys, os, os.path as op
import bpy

''' Make all frame postprocessing and combination in RENDER_DIR '''

RENDER_PATH = op.join(os.getenv('CITY_DATA_PATH'), 'augmentation/render/current-frame/out.png')

bpy.data.scenes['Scene'].render.filepath = RENDER_PATH
bpy.ops.render.render (write_still=True) 
