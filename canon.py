import io
import logging
import os
import numpy as np
import sys

from matplotlib import pyplot as plt
from PIL import Image

import gphoto2 as gp

class Canon:
    def __init__(self):
        self.setup()

    def setup(self):
        logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
        callback_obj = gp.check_result(gp.use_python_logging())
        self.camera = gp.check_result(gp.gp_camera_new())
        gp.check_result(gp.gp_camera_init(self.camera))
        # required configuration will depend on camera type!
        print('Checking camera config')
        # get configuration tree
        self.config = gp.check_result(gp.gp_camera_get_config(self.camera))

    def setup_preview(self):
        # find the image format config item
        # camera dependent - 'imageformat' is 'imagequality' on some
        OK, image_format = gp.gp_widget_get_child_by_name(self.config, 'imageformat')
        if OK >= gp.GP_OK:
            # get current setting
            value = gp.check_result(gp.gp_widget_get_value(image_format))
            # make sure it's not raw
            if 'raw' in value.lower():
                print('Cannot preview raw images')
                return False
        # find the capture size class config item
        # need to set this on my Canon 350d to get preview to work at all
        OK, capture_size_class = gp.gp_widget_get_child_by_name(
            self.config, 'capturesizeclass')
        if OK >= gp.GP_OK:
            # set value
            value = gp.check_result(gp.gp_widget_get_choice(capture_size_class, 2))
            gp.check_result(gp.gp_widget_set_value(capture_size_class, value))
            # set config
            gp.check_result(gp.gp_camera_set_config(self.camera, self.config))

        return True

    def get_preview(self, steps=5):
        # TODO(izzy): this is hacky AF. for some reason there's a buffer and we have 
        # to capture several preview frame before we're at the front of the buffer.
        for _ in range(steps):
            camera_file = gp.check_result(gp.gp_camera_capture_preview(self.camera))
            file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))

            image = Image.open(io.BytesIO(file_data))

        return np.asarray(image)

    def capture_image(self, target=None):


        print('Capturing image')
        file_path = self.camera.capture(gp.GP_CAPTURE_IMAGE)
        print('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))

        if target is None:
            target = os.path.join('tmp', file_path.name)

        print('Copying image to', target)
        camera_file = self.camera.file_get(
            file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
        camera_file.save(target)


    def exit(self):
        gp.check_result(gp.gp_camera_exit(self.camera))


def press(event):
    print('press', event.key)
    sys.stdout.flush()
    if event.key == 'p':
        img = self.canon.get_preview()
        plt.imshow(img)
        fig.canvas.draw()

if __name__ == '__main__':
    canon = Canon()
    if canon.setup_preview():
        fig, ax = plt.subplots()
        fig.canvas.mpl_connect('key_press_event', press)
        img = canon.get_preview()
        plt.imshow(img)
        plt.show()
        # for _ in range(100):
        #     img = canon.get_preview()
        #     plt.imshow(img)
        #     plt.show()

    # canon.capture_image()
    canon.exit()
