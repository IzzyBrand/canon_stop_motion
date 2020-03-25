import os
import sys
import glob
import numpy as np
from canon import Canon
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from PIL import Image

class StopMotion:
    def __init__(self):
        self.change_scene('scene')
        print(self.N)
        self.canon = Canon()
        self.alpha = 0.95

    def print_header(self):
        print("""
            Use the keyboard. Type a command and then press enter.

            q - quit
            p — preview
            s - save a frame
            v - view previous photo
            d - delete previous photo
            n <name> - create a new scene. for example "n trip"

            Next image:\t{}
            """.format(self.get_image_name()))

    def get_image_number(self):
        files = glob.glob(self.scene + '/*jpg')
        if files:
            self.N = max(int(f.strip('.jpg')[-4:]) for f in files) + 1
        else:
            self.N = 0

    def get_image_name(self, scene=None, N=None):
        if scene is None:
            scene = self.scene
        if N is None:
            N = self.N
        return '{}/{:04d}.jpg'.format(scene, N)

    def get_image(self, scene, N):
        image_name = self.get_image_name(scene=scene, N=N)
        if os.path.isfile(image_name):
            return Image.open(image_name)
        else:
            return None

    def save_frame(self):
        target = self.get_image_name()
        self.canon.capture_image(target)
        self.N += 1

    def delete_frame(self):
        prev_image_name = self.get_image_name(N=self.N-1)
        if os.path.isfile(prev_image_name):
            raw = input('Are you sure you want to delete {}? [y/n]\n'.format(prev_image_name))
            if raw == "" or raw.lower()[0] != 'y':
                return
            os.remove(prev_image_name)
            self.N -= 1
            print("Deleted {}".format(prev_image_name))
        else:
            print('Could not find {}'.format(prev_image_name))

    def view_prev_frame(self):
        prev_image_name = self.get_image_name(self.scene, self.N-1)
        if os.path.isfile(prev_image_name):
            print('Displaying {}'.format(prev_image_name))
            Image.open(prev_image_name).show()
        else:
            print('Could not load {}'.format(prev_image_name))

    def get_transparency_preview(self):
        curr_img = self.canon.get_preview()
        prev_img = self.get_image(self.scene, self.N-1)

        if prev_img is None:
            preview = curr_img
        else:
            prev_img = np.asarray(prev_img.resize((curr_img.shape[1], curr_img.shape[0])))
            preview = (curr_img * self.alpha + prev_img * (1. - self.alpha)).astype(np.uint8)

        return preview

    def preview(self):
        if self.canon.setup_preview():
            print("""
                Opened preview. Use the keyboard.
                p - refresh preview
                up - increase transparency
                down - decrease transparency
                q - quit preview
                """)
            fig, ax = plt.subplots()

            def press(event):
                sys.stdout.flush()
                print(event.key)
                if event.key == 'p':
                    plt.imshow(self.get_transparency_preview())
                    fig.canvas.draw()
                elif event.key == 'up' or event.key == 'down':
                    self.alpha += 0.05 if event.key == 'up' else -0.05
                    self.alpha  = np.clip(self.alpha, 0., 1.)
                    print('Alpha: {}'.format(self.alpha))
                    plt.imshow(self.get_transparency_preview())
                    fig.canvas.draw()

            fig.canvas.mpl_connect('key_press_event', press)

            plt.imshow(self.get_transparency_preview())
            plt.show()

    def change_scene(self, new_scene_name):
        if os.path.isdir(new_scene_name):
            print('Changing scene to {}'.format(new_scene_name))
            self.scene = new_scene_name
            self.get_image_number()
        elif os.path.isfile(new_scene_name):
            print('{} already exists as a file'.format(new_scene_name))
            return
        else:
            os.mkdir(new_scene_name)
            print('Created new scene, {}'.format(new_scene_name))
            self.scene = new_scene_name
            self.N = 0

    def get_command(self):
        raw = input()
        first_letter = raw.lower()[0]

        if first_letter == 'q':
            print("exit")
            sys.exit(0)
        if first_letter == 'p':
            self.preview()
        elif first_letter == 's':
            self.save_frame()
        elif first_letter == 'v':
            self.view_prev_frame()
        elif first_letter == 'd':
            self.delete_frame()
        elif first_letter == 'n':
            words = raw.split()
            if len(words) > 1:
                new_scene_name = words[1]
            else:
                new_scene_name = input('Enter a scene name: ')
                if new_scene_name ==  '': return

            self.change_scene(new_scene_name)

    def loop(self):
        while True:
            self.print_header()
            self.get_command()


sm = StopMotion()
try:
    sm.loop()
except Exception as e:
    print(e)
    sm.canon.exit()

