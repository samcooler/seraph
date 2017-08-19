import bibliopixel
from bibliopixel.drivers.SPI import APA102
from bibliopixel.drivers.SimPixel import SimPixel
from bibliopixel.layout import Strip
from bibliopixel import colors
from copy import copy

# import RPi.GPIO as GPIO
from collections import OrderedDict
from colorsys import hls_to_rgb
from seraph_utils import *
from seraph_shader import Shader, ShaderData
import time, random
from multiprocessing import Pipe, Process

import logging
logger = logging.getLogger(__name__)

def pix_to_letter(p):
    if p['h'] % 1.0 < 0.33:
        hc = '\033[91m'
    elif p['h'] % 1.0 < 0.66:
        hc = '\033[92m'
    else:
        hc = '\033[94m'

    # if p['l'] > 0.2:
    lc = unichr(9608)

    return hc + lc + '\033[0m'


def display_pixel_matrix(pm):
    # print(chr(27) + "[2J")
    out = ''
    for ri in range(len(pm)):
        for pi in range(len(pm[ri])):
            out += pix_to_letter(pm[ri][pi])
        out += '\n'
    # print out


class RaySet:
    def __init__(self, dancer):
        self.dancer = dancer
        self.ray_length = dancer.ray_length
        self.ray_offsets = dancer.ray_offsets
        # self.ray_orientations = self.dancer.ray_orientations
        self.all_rays = range(self.dancer.num_rays)
        self.raw_arrays = []
        # self.write_to_strip_worker_pipe = []

        if not self.dancer.debug_mode:
            if self.dancer.simPixel_mode:
                self.strips = [Strip(SimPixel(self.dancer.pixels_per_channel)) for i in range(self.dancer.num_channels)]
            else:
                self.strips = [Strip(APA102.APA102(self.dancer.pixels_per_channel, interface='PYDEV', spi_speed=self.dancer.spi_rate, gamma=bibliopixel.gamma.APA102), self.dancer.threaded_strip_update) for i in range(self.dancer.num_channels)]

            for ci in range(self.dancer.num_channels):

                self.raw_arrays.append(bytearray(3 * self.dancer.pixels_per_channel))

                # for pi in range(self.dancer.pixels_per_channel):
                #     self.raw_arrays[ci][pi * 4] = 0xFF

                # GPIO.setup(self.dancer.channel_pins[ci], GPIO.OUT)
                # GPIO.output(self.dancer.channel_pins[ci], True)

                # self.strips[ci].begin()
                # self.strips[ci].setBrightness(255)
                # self.strips[ci].clear()

        self.pixel_matrix = [[self.new_pixel() for j in range(self.ray_length)] for i in range(self.dancer.num_rays)]

        # self.pixel_to_strip_map = []
        # for ci in range(self.dancer.num_channels):
        #     for ri in range(self.dancer.channel_rays[ci]):

        #         ray_vals = []
        #         for index in range(self.ray_length):
        #             if not self.ray_orientations[ri]:
        #                 pi = index + self.ray_offsets[ri]
        #             else:
        #                 pi = self.ray_offsets[ri] + self.ray_length - index
        #             ray_vals.append(pi)
        #         self.pixel_to_strip_map[ci].append(tuple(ray_vals))
        # self.pixel_to_strip_map = tuple(self.pixel_to_strip_map)

        self.shaders = OrderedDict()

        # self.start_write_to_strip_worker()

        if self.dancer.render_multithreaded:
            self.render_workers = []
            self.render_pipes = []
            self.render_workers_rays = []
            self.start_render_workers()

        # self.set_all_random_full_color_H()

    def new_pixel(self):
        return {'h': 0.0, 's': 0.5, 'l': 0.0}

    def render(self):
        if not self.dancer.render_multithreaded:
            # logger.debug('Shaders to render: %s', self.shaders.keys())

            new_pixel_matrix = [[self.new_pixel() for j in range(self.ray_length)] for i in range(self.dancer.num_rays)]
            for name, data in self.shaders.items():
                shad = Shader(data)
                new_pixel_matrix = shad.effect(new_pixel_matrix)

            self.pixel_matrix = new_pixel_matrix

        else:

            # send shaders
            # logger.debug('sending data to shaders %s', self.shaders)
            for wi in range(self.dancer.num_rays):
                self.render_pipes[wi][0].send(self.shaders)

            # receive pixels
            new_pixel_matrix = [None] * self.dancer.num_rays
            for wi in range(self.dancer.num_rays):
                # print 'rx from worker', wi
                new_pixel_ray = self.render_pipes[wi][0].recv()

                # assemble pixels into full matrix
                # print 'rays by worker',wi,self.render_workers_rays
                new_pixel_matrix[wi] = new_pixel_ray

            self.pixel_matrix = new_pixel_matrix
            # display_pixel_matrix(self.pixel_matrix)


    def start_render_workers(self):
        for p in range(self.dancer.num_rays):
            pipe = Pipe()
            self.render_pipes.append(pipe)

            worker = Process(target=self.render_worker, args=(pipe[1], p))
            self.render_workers.append(worker)

            worker.start()

    def render_worker(self, conn, ray_index):

        while True:
            msg = conn.recv()
            # print 'worker received', msg
            if msg == 'end':
                break
            else:
                new_pixel_ray = [self.new_pixel() for j in range(self.ray_length)]
                for name, data in msg.items():
                    # print 'shader', name
                    shad = Shader(data)
                    new_pixel_ray = shad.effect(new_pixel_ray, ray_index)
                # print 'worker sending'
                conn.send(new_pixel_ray)

        conn.close()

    # def start_write_to_strip_worker(self):
    #     pipe = Pipe()
    #     self.write_to_strip_worker_pipe = pipe
    #
    #     worker = Process(target=self.write_to_strip_worker, args=pipe)
    #     # self.render_workers.append(worker)
    #
    #     worker.start()


    # def write_to_strip_worker(self, conn):
    #
    #     while True:
    #         msg = conn.recv()
    #         if msg == 'end':
    #             break
    #         else:
    #             for name, data in msg.items():
    #                 # pixel_matrix
    #                 ri = 0
    #                 si = 0
    #                 raw_arrays = data
    #                 for index in range(self.ray_length):
    #                     if self.pixel_matrix[ri][index]['l'] < .001: # skip drawing dark pixels
    #                         rgb = [0,0,0]
    #                     else:
    #                         rgb = map(clamp_value, hls_to_rgb(self.pixel_matrix[ri][index]['h'] % 1.0, self.pixel_matrix[ri][index]['l'], self.pixel_matrix[ri][index]['s']))
    #                     # logger.debug(rgb)
    #                     # offset = self.pixel_to_strip_map[ci][ri][index] * 4 + 1
    #                     pixel = self.dancer.ray_length + self.dancer.ray_offsets[ri] + index
    #                     offset = pixel * 4 + 1
    #                     # print pixel
    #                     raw_arrays[si][offset] = int(rgb[2] * 255)
    #                     raw_arrays[si][offset + 1] = int(rgb[1] * 255)
    #                     raw_arrays[si][offset + 2] = int(rgb[0] * 255)
    #                 # print 'worker sending'
    #                 conn.send('done')
    #
    #                 self.strips[si].show(raw_arrays[si])


    def write_to_strip(self):

        # logger.debug(self.write_to_strip_worker_pipe)
        # self.write_to_strip_worker_pipe.send(self.raw_arrays)

        for si in range(self.dancer.num_channels):

            # print si
            for ch_ri, ri in enumerate(self.dancer.channel_rays[si]):
                # print 'ray', ch_ri, ri
                for index in range(self.ray_length):
                    if self.pixel_matrix[ri][index]['l'] < .001: # skip drawing dark pixels
                        rgb = [0,0,0]
                    else:

                        rgb = [int(255*clamp_value(v)) for v in hls_to_rgb(self.pixel_matrix[ri][index]['h'] % 1.0, self.pixel_matrix[ri][index]['l'], self.pixel_matrix[ri][index]['s'])]
                        # hsv = (int((self.pixel_matrix[ri][index]['h'] % 1.0)*255),
                        #      int(self.pixel_matrix[ri][index]['s']*255),
                        #      int(self.pixel_matrix[ri][index]['l']*255))
                        # rgb = colors.hsv2rgb(hsv)
                        # logger.debug('%s', rgb)
                    # logger.debug(self.pixel_matrix[ri][index])
                    # logger.debug(rgb)
                    # offset = self.pixel_to_strip_map[ci][ri][index] * 4 + 1
                    pixel = ch_ri * self.dancer.ray_length + self.dancer.ray_offsets[ri] + index
                    offset = pixel * 3
                    # print pixel
                    # logger.debug('%s %s %s', si, offset, pixel)
                    self.raw_arrays[si][offset] = rgb[2]
                    self.raw_arrays[si][offset + 1] = rgb[1]
                    self.raw_arrays[si][offset + 2] = rgb[0]

            # # set channel select pins, False is enable
            # for ch in range(self.dancer.num_channels):
            #     if ch == si:
            #         GPIO.output(self.dancer.channel_pins[ch], False)
            #     else:
            #         GPIO.output(self.dancer.channel_pins[ch], True)
            # time.sleep(0.1)

            # self.strips[si].setBrightness(255)
            # self.strips[si].show(self.raw_arrays[si])
            self.strips[si].setBuffer(self.raw_arrays[si])
            self.strips[si].update()

    # functions (create and modify shaders)
    # def set_lights(ray_values):
    #     # print 'set lights', ray_values
    #     for ray, val in zip(self.rays, ray_values):
    #         if val:
    #             col = 0.0
    #         else:
    #             col = 0.4
    #         ray.full_color(col)

    def set_all_random_full_color_H(self):
        self.full_color(range(self.dancer.num_rays), 0, 1.0)
        shad = self.shaders['full_color_H']
        shad.generate_function = 'parameter_by_ray'
        shad.generate_parameters['value'] = [random.random() for i in range(self.dancer.num_rays)]
        return shad

    # base effects
    def full_color(self, rays, hue, sat=1.0):
        shad = self.shaders.get('full_color_H', ShaderData(self.dancer))
        shad.active_rays = rays
        shad.active_indices = range(self.ray_length)
        shad.pixel_component = 'h'
        shad.mix_function = 'replace'
        shad.generate_function = 'single_parameter'
        shad.generate_parameters = {'value': hue}
        shad.length = self.ray_length
        self.shaders['full_color_H'] = shad

        shad_s = self.shaders.get('full_color_S', ShaderData(self.dancer))
        shad_s.active_rays = rays
        shad_s.active_indices = range(self.ray_length)
        shad_s.pixel_component = 's'
        shad_s.mix_function = 'replace'
        shad_s.generate_function = 'single_parameter'
        shad_s.generate_parameters = {'value': sat}
        shad_s.length = self.ray_length
        self.shaders['full_color_S'] = shad_s

        if 'arc_color' in self.shaders:
            del self.shaders['arc_color']
        return [shad,shad_s]

    def full_brightness(self, brightness):
        shad = self.create_shader('full_L', 'l', 'single_parameter', {'value': brightness}, 'add')

        return shad

    def arc_color(self, rays, hue):
        shad = ShaderData(self.dancer)
        shad.active_rays = rays
        shad.active_indices = range(self.ray_length)
        shad.pixel_component = 'h'
        shad.mix_function = 'replace'
        shad.generate_function = 'arc'
        shad.length = self.ray_length
        shad.generate_parameters = {'value': hue, 'start_time': time.time()}
        self.shaders['arc_color'] = shad
        return shad

    def vibrate_brightness(self, rays, t_frequency = 2, s_frequency = 0.7, starttime = 0, amplitude = 1.0, mean = 1.0):
        shad = self.shaders.get('vibrate_brightness', ShaderData(self.dancer))
        shad.active_rays = rays
        shad.active_indices = range(self.ray_length)
        shad.pixel_component = 'l'
        shad.mix_function = 'multiply'
        shad.generate_function = 'sine_wave'
        shad.length = self.ray_length
        shad.generate_parameters = {'start_time': (starttime,) * len(rays), 't_frequency': (t_frequency,) * len(rays),
                                    'amplitude': (amplitude,) * len(rays), 's_frequency': (s_frequency,) * len(rays),
                                    'mean': (mean,) * len(rays)}
        self.shaders['vibrate_brightness'] = shad
        return shad

    def vibrate_hue(self, rays, t_frequency = 1, s_frequency = 1, starttime = 0, amplitude = 0.4, mean = 0):
        shad = self.shaders.get('vibrate_hue', ShaderData(self.dancer))
        shad.active_rays = rays
        shad.active_indices = range(self.ray_length)
        shad.pixel_component = 'h'
        shad.mix_function = 'add'
        shad.generate_function = 'sine_wave'
        shad.length = self.ray_length
        shad.generate_parameters = {'start_time': (starttime,) * len(rays), 't_frequency': (t_frequency,) * len(rays),
                                    'amplitude': (amplitude,) * len(rays), 's_frequency': (s_frequency,) * len(rays),
                                    'mean': (mean,) * len(rays)}
        self.shaders['vibrate_hue'] = shad
        return shad

    def sparkle(self, rays):
        shad = self.shaders.get('sparkle', ShaderData(self.dancer))
        shad.active_rays = rays
        shad.active_indices = range(self.ray_length)
        shad.pixel_component = 'l'
        shad.mix_function = 'add'
        shad.generate_function = 'random_points'
        shad.length = self.ray_length
        shad.generate_parameters = {'num_points': 2, 'value': 1}
        self.shaders['sparkle'] = shad
        return shad

    def ring(self, rays, id='', component_list=(('h', 'add'),)):
        shaders = {}
        for component in component_list:
            name = 'ring'+str(id)+component[0]
            shad = self.shaders.get(name, ShaderData(self.dancer))
            shad.active_rays = rays
            shad.active_indices = range(self.ray_length)
            shad.pixel_component = component[0]
            shad.mix_function = component[1]
            shad.generate_function = 'sprite'
            shad.generate_parameters = {'value': 1.0, 'value_base': 0.5, 'center': 0.5, 'length': 0.1, 'falloff_rate': 0.5}
            shad.length = self.ray_length
            self.shaders[name] = shad
            shaders[component[0]] = shad
        return shaders

    def checkers(self, rays=None, id=''):

        shad = self.shaders.get('checkers'+str(id), ShaderData(self.dancer))
        shad.active_rays = rays if rays else self.all_rays
        shad.active_indices = range(self.ray_length)
        shad.pixel_component = 'l'
        shad.mix_function = 'add'
        shad.generate_function = 'checkers'
        shad.generate_parameters = {'value': -0.5, 's_frequency': 10}
        shad.length = self.ray_length
        self.shaders['ring'+str(id)] = shad
        return shad

    def monochrome(self, rays=None, id=''):
        shad = self.shaders.get('monochrome'+str(id), ShaderData(self.dancer))
        shad.active_rays = rays if rays else self.all_rays
        shad.active_indices = range(self.ray_length)
        shad.pixel_component = 's'
        shad.mix_function = 'replace'
        shad.generate_function = 'single_parameter'
        shad.generate_parameters = {'value': 0.2}
        shad.length = self.ray_length
        self.shaders['ring'+str(id)] = shad
        return shad

    def create_shader(self, name, p_c, g_f, g_p, m_f, rays=None):
        shad = self.shaders.get(name, ShaderData(self.dancer))

        shad.active_rays = rays if rays else self.all_rays
        shad.pixel_component = p_c
        shad.mix_function = m_f
        shad.generate_function = g_f
        shad.generate_parameters = copy(generate_parameter_defaults.get(g_f, {}))
        shad.generate_parameters.update(g_p)
        shad.length = self.ray_length
        shad.name = name
        self.shaders[name] = shad
        return shad

generate_parameter_defaults = {'sprite': {'value': 1.0, 'value_base': 0.5, 'center': 0.5, 'length': 0.1},
                               'circularsprite': {'value': 1.0, 'value_base': 0, 'center': 0.5, 'length': 0.1, 'falloff_rate': 0.5},
                               'single_parameter': {'value': 1.0},
                               'sine_wave': {},
                               'arc': {'value': 1.0, 'start_time': 0.0, 'end_time': 1.0},
                               'checkers': {'value': -0.5, 's_frequency': 10}}

