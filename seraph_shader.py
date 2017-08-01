import time, random, math
from seraph_utils import clamp_value

import logging
logger = logging.getLogger(__name__)

class ShaderData:
    def __init__(self, dancer):
        self.mix_function = None # adds the pattern to the rendered output
        self.pixel_component = None # which part of the pixel to change (HSLB)
        self.generate_function = None # makes the pattern
        self.generate_parameters = {} # params for pattern generation
        self.ray_length = dancer.ray_length
        self.num_rays = dancer.num_rays
        self.active_rays = list(range(self.num_rays))

    def __str__(self):
        return str(self.generate_parameters) + ' ' + self.generate_function + ' ' + self.pixel_component + ' ' + str(self.mix_function)

class Shader:
    def __init__(self, data):
        self.data = data
        sine_range = data.ray_length
        # self.sine_table = [math.sin(float(x)/sine_range * 2 * math.pi) for x in range(sine_range)]

    def effect(self, pixel_matrix, ray_index=None):
        if ray_index is None:
            for ri in range(self.data.num_rays):
                pixel_matrix[ri] = self.mix(pixel_matrix[ri], self.generate(ri))
            return pixel_matrix
        else:
            return self.mix(pixel_matrix, self.generate(ray_index))
        # print 'effect', index, pixel, self.data.generate_function, self.data.generate_parameters

    ##########################
    ##########################
    ##########################
    # mix functions
    # iterate by row index and pixel index, for original values (0...5) and shade values (1,3,etc)

    def mix(self, orig_vals, shade_vals):
        # logger.debug('Mixing pixel %s to %s', orig_vals, shade_vals)
        if self.data.mix_function == 'replace':
            for pi in range(self.data.ray_length):
                if shade_vals[pi] is not None:
                    orig_vals[pi][self.data.pixel_component] = shade_vals[pi]
            return orig_vals

        if self.data.mix_function == 'blend':
            for pi in range(self.data.ray_length):
                if shade_vals[pi] is not None:
                    orig_vals[pi][self.data.pixel_component] = \
                        (shade_vals[pi] + orig_vals[pi][self.data.pixel_component]) / 2.0
            return orig_vals

        elif self.data.mix_function == 'multiply':
            for pi in range(self.data.ray_length):
                if shade_vals[pi] is not None:
                    orig_vals[pi][self.data.pixel_component] *= shade_vals[pi]
            return orig_vals

        elif self.data.mix_function == 'add':
            for pi in range(self.data.ray_length):
                if shade_vals[pi] is not None:
                    orig_vals[pi][self.data.pixel_component] += shade_vals[pi]
            return orig_vals

    ##########################
    ##########################
    ##########################
    # generate functions
    # return minimally-sized arrays to match the rays and indices listed in parameters
    def generate(self, ray_index):

        if ray_index not in self.data.active_rays:
            return [None] * self.data.ray_length

        if self.data.generate_function == 'single_parameter':
            return [self.data.generate_parameters['value']] * self.data.ray_length

        elif self.data.generate_function == 'parameter_by_ray':
            return [self.data.generate_parameters['value'][ray_index]] * self.data.ray_length

        elif self.data.generate_function == 'parameter_by_index':
            return self.data.generate_parameters['value']

        elif self.data.generate_function == 'random_points':
            out = [None] * self.data.ray_length
            for i in range(self.data.generate_parameters['num_points']):
                index = random.randrange(self.data.ray_length)
                out[index] = self.data.generate_parameters.get('value', 1)
            return out

        # elif self.data.generate_function == 'gradient':
        #     if self.data.generate_parameters['dimension'] == 1:
        #         m = self.data.generate_parameters['value'] / self.data.dancer.num_rays
        #         return [[ri * m] * self.data.length for ri in range(self.data.dancer.num_rays)]
        #     else:
        #         m = self.data.generate_parameters['value'] / self.data.length
        #         return [[index * m for index in range(self.data.length)] for ri in range(self.data.dancer.num_rays)]

        elif self.data.generate_function == 'sine_wave':
            # print self.data.generate_parameters
            out = [0] * self.data.ray_length
            if self.data.generate_parameters['amplitude'][ray_index] < 0.01: # if no significant wave on this ray
                out = [self.data.generate_parameters['mean'][ray_index]] * self.data.ray_length
            else:
                phase_add = int(((time.time() - self.data.generate_parameters['start_time'][ray_index]) % 1.0) * self.data.ray_length * self.data.generate_parameters['t_frequency'][ray_index])
                amp = 0.5 * self.data.generate_parameters['amplitude'][ray_index]
                # print amp
                for index in range(self.data.ray_length):
                    # print int((ray_length - index) * self.data.generate_parameters['s_frequency'][ri] + phase_add)
                    out[index] = self.data.generate_parameters['mean'][ray_index] + \
                        amp * self.sine_table[(int((self.data.ray_length - index) * self.data.generate_parameters['s_frequency'][ray_index]) + phase_add) % self.data.ray_length]

            return out

        elif self.data.generate_function == 'sprite':
            # anti-aliased sprite
            # print self.data.generate_parameters
            out = [0] * self.data.ray_length
            shift_per_pixel = 1.0 / self.data.ray_length
            for pi in range(self.data.ray_length):
                distance_from_center = (abs(self.data.generate_parameters['center'] - (pi * shift_per_pixel)))
                out[pi] = self.data.generate_parameters['value_base'] + \
                     self.data.generate_parameters['value'] * \
                     clamp_value(1 - distance_from_center / self.data.generate_parameters['length']) # this is fade to the side
            return out


        elif self.data.generate_function == 'circularsprite':
            # anti-aliased sprite
            out = [0 + self.data.generate_parameters['value_base']] * self.data.ray_length
            shift_per_pixel = 1.0 / self.data.ray_length

            self.data.generate_parameters['center'] = self.data.generate_parameters['center'] % 1.0
            half_length = 0.5 * self.data.generate_parameters['length']
            start = math.floor((self.data.generate_parameters['center'] - half_length) * self.data.ray_length)
            end = math.ceil((self.data.generate_parameters['center'] + half_length) * self.data.ray_length)
            # logger.debug('start: %s, end: %s, half_length: %s', start, end, half_length)
            for pi in range(start, end):
                pixel_index = pi % self.data.ray_length
                # logger.debug(pixel_index)
                position_center_diff = pixel_index * shift_per_pixel - self.data.generate_parameters['center']
                distance_from_center = min((abs(position_center_diff), abs(position_center_diff + 1), abs(position_center_diff - 1)))
                if self.data.generate_parameters['falloff_rate'] == 0:
                    if distance_from_center <= half_length:
                        out[pixel_index] += self.data.generate_parameters['value'] # hard falloff
                else:
                    value = clamp_value(1 - distance_from_center / half_length) # decrease with distance
                    out[pixel_index] += value * 0.5 * self.data.generate_parameters['value'] # this is fade to the side, linearly

                # logger.debug([pi, position, distance_from_center])
            return out

        elif self.data.generate_function == 'checkers':
            out = [self.data.generate_parameters['value'] * (pi % 2.0) for pi in range(self.data.ray_length)] * self.data.ray_length
            # print out
            return out

