import os, os.path as op
from glob import glob
from time import sleep, time

from wand.image import Image, Color
from wand.display import display



def process_image (imagepath):
    '''Put a png image on top of background and save as jpg
    '''
    assert op.exists (imagepath)

    #crappy_camera = True

    with Image (filename=imagepath) as fg_img:
        sz = fg_img.size
        with Image(width=sz[0], height=sz[1], background=Color('gray')) as img:

            # overlay car on background
            img.composite_channel (channel='all_channels', image=fg_img, 
                                   operator='overlay', left=0, top=0)

            #if crappy_camera:

            #    # pixelate
            #    pixel = 3
            #    img.resize (width = sz[0]/pixel, height = sz[1]/pixel,
            #                filter = 'point', blur = 0)

            #    # add unsharp mask
            #    img.unsharp_mask (radius=20, sigma=3, amount=2, threshold=0.2)


            #    img.resize (width = sz[0], height = sz[1],
            #                filter = 'point', blur = 0)

            imagepath = imagepath[:-4] + '.jpg'
            img.save (filename=imagepath)


def process_all_png (imagedir, remove_original = False):
    '''Process all png images in the folder.
    If remove_original is True, remove png and keep jpg instead
    '''
    assert op.exists(imagedir)

    png_paths = glob(op.join(imagedir, '*.png'))
    for png_path in png_paths:
        process_image(png_path)
        if remove_original:
            print 'processing png file %s' % op.basename(png_path)
            assert op.exists(png_path)
            os.remove(png_path)


def monitor_folder (imagedir, timeout):
    '''Look at imagedir for until timeout (in sec.)
    Every second run process_all_png,
    '''
    start_time = time()
    process_all_png (imagedir, remove_original = True)

    while time() - start_time < timeout:
        sleep (1) # a sec.
        process_all_png (imagedir, remove_original = True)


# test this script
#monitor_folder (imagedir = '/Users/evg/projects/City-Project/src/augmentation',
#                timeout = 10)
