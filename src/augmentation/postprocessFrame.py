import os, os.path as op
from glob import glob
from time import sleep, time

from wand.image import Image, Color
from wand.display import display



def process_frame (background_path, carsonly_path, shadows_path, 
                   out_path, ghost_path = None):
    '''Put a png foreground on top of background and save as jpg
    '''
    assert op.exists (background_path)
    assert op.exists (carsonly_path)
    assert op.exists (shadows_path)

    with Image (filename=background_path) as back_img:
        img = Image(back_img)
        with Image (filename=carsonly_path) as cars_img:
            with Image (filename=shadows_path) as shadows_img:
                assert img.size == cars_img.size
                assert img.size == shadows_img.size
                sz = img.size

                # add unsharp mask
                cars_img.unsharp_mask (radius=20, sigma=3, amount=2, threshold=0.2)

                # overlay cars+shadows onto background
                img.composite_channel (channel='all_channels', 
                                       image=shadows_img, 
                                       operator='multiply', left=0, top=0)

                # put cars only onto background
                img.composite_channel (channel='all_channels', 
                                       image=cars_img, 
                                       operator='atop', left=0, top=0)

                img.save (filename=out_path)

        # get the ghost image
        img.evaluate      (operator='multiply', value=0.5)
        img.evaluate      (operator='add', value=0.5)
        #back_img.evaluate (operator='multiply', value=0.5)
        #img.composite_channel (channel='all_channels', 
        #                       image=back_img, 
        #                       operator='difference', left=0, top=0)

        if ghost_path:
            img.save (filename=ghost_path)




# test this script
if __name__ == "__main__":
    background_path = '/Users/evg/Desktop/3Dmodel/1back.png'
    carsonly_path = '/Users/evg/Desktop/3Dmodel/renders/render-cars-only.png'
    shadows_path = '/Users/evg/Desktop/3Dmodel/renders/render-shadows.png'
    out_path = '/Users/evg/Desktop/3Dmodel/renders/out.jpg'
    ghost_path = '/Users/evg/Desktop/3Dmodel/renders/ghost.jpg'
    process_frame (background_path, carsonly_path, shadows_path, out_path, ghost_path)
