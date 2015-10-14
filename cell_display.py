from dotstar import Adafruit_DotStar
import RPi.GPIO as GPIO
from collections import OrderedDict
from colorsys import hls_to_rgb
from seraph_utils import *
from seraph_shader import Shader, ShaderData
import time, random
from multiprocessing import Pipe, Process

class CellDisplay:
    def __init__(self, dancer):
        self.dancer = dancer
        self.lobe_lenths = dancer.ray_length
        self.lobe_centers = dancer.ray_offsets

        self.raw_arrays = []

        if not self.dancer.debug_mode:
            self.strips = [Adafruit_DotStar(self.dancer.spi_rate) for i in range(self.dancer.num_channels)]

            for ci in range(self.dancer.num_channels):

                self.raw_arrays.append(bytearray(4 * self.dancer.pixels_per_channel))

                for pi in range(self.dancer.pixels_per_channel):
                    self.raw_arrays[ci][pi * 4] = 0xFF

                GPIO.setup(self.dancer.channel_pins[ci], GPIO.OUT)
                GPIO.output(self.dancer.channel_pins[ci], True)

                self.strips[ci].begin()
                self.strips[ci].setBrightness(255)
                self.strips[ci].clear()

        self.pixel_matrix = [self.new_pixel() for j in range(self)]

    def new_pixel(self):
        return {'h': 0.5, 's': 0.5, 'l': 0.5}

    def render(self):
        if not self.dancer.render_multithreaded:
            new_pixel_matrix = [self.new_pixel() for j in range(self.ray_length)]
            # print '******new render'
            for name, data in self.shaders.items():
                shad = Shader(data)
                new_pixel_matrix = shad.effect(new_pixel_matrix)
                # print name, data.pixel_component, data.generate_parameters

            self.pixel_matrix = new_pixel_matrix
            # display_pixel_matrix(self.pixel_matrix)

    def write_to_strip(self):

        # GPIO.setup(self.dancer.channel_pins[0], GPIO.OUT)
        # GPIO.setup(self.dancer.channel_pins[1], GPIO.OUT)
        # GPIO.output(self.dancer.channel_pins[1], False)
        # GPIO.output(self.dancer.channel_pins[0], True)

        for si in range(self.dancer.num_channels):

            # print si
            for ch_ri, ri in enumerate(self.dancer.channel_rays[si]):
                # print 'ray', ch_ri, ri
                for index in range(self.ray_length):
                    rgb = map(clamp_value, hls_to_rgb(self.pixel_matrix[ri][index]['h'] % 1.0, self.pixel_matrix[ri][index]['l'], self.pixel_matrix[ri][index]['s']))
                    # offset = self.pixel_to_strip_map[ci][ri][index] * 4 + 1
                    pixel = ch_ri * self.dancer.ray_length + self.dancer.ray_offsets[ri] + index
                    offset = pixel * 4 + 1
                    # print pixel
                    self.raw_arrays[si][offset] = int(rgb[2] * 255)
                    self.raw_arrays[si][offset + 1] = int(rgb[1] * 255)
                    self.raw_arrays[si][offset + 2] = int(rgb[0] * 255)

            # set channel select pins, False is enable
            for ch in range(self.dancer.num_channels):
                if ch == si:
                    GPIO.output(self.dancer.channel_pins[ch], False)
                else:
                    GPIO.output(self.dancer.channel_pins[ch], True)
            # time.sleep(0.1)

            self.strips[si].show(self.raw_arrays[si])

    # functions (create and modify shaders)
    # def set_lights(ray_values):
    #     print 'set lights', ray_values
    #     for ray, val in zip(self.rays, ray_values):
    #         if val:
    #             col = 0.0
    #         else:
    #             col = 0.4
    #         ray.full_color(col)


    def create_shader(self, name, p_c, g_f, g_p, m_f, rays=None):
        shad = self.shaders.get(name, ShaderData(self.dancer))

        shad.active_rays = rays if rays else self.all_rays
        shad.pixel_component = p_c
        shad.mix_function = m_f
        shad.generate_function = g_f
        shad.generate_parameters = generate_parameter_defaults.get(g_f, {})
        shad.generate_parameters.update(g_p)
        shad.length = self.ray_length
        self.shaders[name] = shad
        return shad


generate_parameter_defaults = {'sprite': {'value': 1.0, 'value_base': 0.5, 'center': 0.5, 'length': 0.1},
                               'single_parameter': {'value': 1.0},
                               'sine_wave': {},
                               'arc': {'value': 1.0, 'start_time': 0.0, 'end_time': 1.0},
                               'checkers': {'value': -0.5, 's_frequency': 10}}
