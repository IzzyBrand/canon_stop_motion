import os
import sys
import glob
import numpy as np
import subprocess
from canon import Canon
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from PIL import Image

class StopMotion:
    def __init__(self):
        self.change_scene('scene')
        print(self.N)
        try:
            self.canon = Canon()
            self.canon.setup_preview()
        except Exception as e:
            print(e)
            print('Failed to connect to camera!')
            self.canon = None
        self.alpha = 0.70
        self.frame_rate = 12

    def start_preview(self):
        self.fig, _ = plt.subplots()
        self.fig.canvas.mpl_connect('key_press_event', self.get_command)
        self.preview()
        plt.show()
        self.canon.exit()

    def print_header(self):
        print("""
            Use the keyboard. Type a command.

            q - quit
            p - preview
            f - tave a frame
            v - view previous photo
            d - delete previous photo. Go to terminal to confirm
            r - render the photos into a video
            n - create a new scene. Go to terminal to enter name.

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
        plt.imshow(self.get_transparency_preview())
        self.fig.canvas.draw()

    def change_alpha(self, key):
        self.alpha += 0.05 if key == 'up' else -0.05
        self.alpha  = np.clip(self.alpha, 0., 1.)
        print('Alpha: {}'.format(self.alpha))
            
    def change_scene(self, new_scene_name=None):
        if new_scene_name is None:
            new_scene_name = input('Enter a scene name: ')
            if new_scene_name ==  '': return

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

    def render(self):
        command = ['ffmpeg',
                   '-i', '{}/%04d.jpg'.format(self.scene),
                   '-c:v', 'libx264',
                   '-vf', 'fps={},format=yuv420p'.format(self.frame_rate),
                   '{}/out.mp4'.format(self.scene)]
        subprocess.Popen(command)

    def get_command(self, event):
        self.print_header()
        sys.stdout.flush()

        if event.key == 'p':
            pass
        elif event.key == 'f':
            self.save_frame()
            return # we don't want to refresh preview
        elif event.key == 'v':
            self.view_prev_frame()
            return # we don't want to refresh preview
        elif event.key == 'd':
            self.delete_frame()
        elif event.key == 'r':
            self.render()
            # we don't want to refresh preview
        elif event.key == 'up' or event.key == 'down':
            self.change_alpha(event.key)
        elif event.key == 'n':
            self.change_scene()
        else:
            return

        self.preview()


    def loop(self):
        while True:
            self.print_header()
            self.get_command()


sm = StopMotion()
try:
    sm.start_preview()
except Exception as e:
    print(e)
    sm.canon.exit()

