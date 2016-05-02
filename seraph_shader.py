import time, random, math
from seraph_utils import clamp_value

class ShaderData:
    def __init__(self, dancer):
        self.mix_function = None # adds the pattern to the rendered output
        self.pixel_component = None # which part of the pixel to change (HSLB)
        self.generate_function = None # makes the pattern
        self.generate_parameters = {} # params for pattern generation
        self.ray_length = dancer.ray_length
        self.num_rays = dancer.num_rays
        self.active_rays = list(range(self.num_rays))

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
        # print 'orig has rays', len(orig_vals)
        # print orig_vals
        # print shade_vals
        # print 'compo', self.data.pixel_component
        if self.data.mix_function == 'replace':
            for pi in range(self.data.ray_length):
                if shade_vals[pi] is not None:
                    # print ri_o, pi_o, ri_s, pi_s
                    orig_vals[pi][self.data.pixel_component] = shade_vals[pi]
                    # print 'ok'
            return orig_vals

        if self.data.mix_function == 'blend':
            for pi in range(self.data.ray_length):
                if shade_vals[pi] is not None:
                    # print self.data.render_rays, ri_o, pi_o, ri_s, pi_s
                    orig_vals[pi][self.data.pixel_component] = \
                        (shade_vals[pi] + orig_vals[pi][self.data.pixel_component]) / 2.0
                    # print 'ok'
            return orig_vals

        elif self.data.mix_function == 'multiply':
            # print orig_vals, shade_vals
            for pi in range(self.data.ray_length):
                if shade_vals[pi] is not None:
                    orig_vals[pi][self.data.pixel_component] *= shade_vals[pi]
            return orig_vals

        elif self.data.mix_function == 'add':
            # print orig_vals
            # print shade_vals
            for pi in range(self.data.ray_length):
                # print pi
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
                d = (abs(self.data.generate_parameters['center'] - (pi * shift_per_pixel)))
                out[pi] = self.data.generate_parameters['value_base'] + \
                             self.data.generate_parameters['value'] * \
                             clamp_value(1 - d / self.data.generate_parameters['length'])
            return out

        elif self.data.generate_function == 'checkers':
            out = [self.data.generate_parameters['value'] * (pi % 2.0) for pi in range(self.data.ray_length)] * self.data.ray_length
            print out
            return out

        #
        # elif self.data.generate_function == 'arc':
        #     fraction = min((time.time() - self.data.generate_parameters['start_time']) / self.data.dancer.full_arc_time, 1)
        #     stopindex = int(fraction * self.data.length)
        #
        #     return [[self.data.generate_parameters['value'] if index < stopindex else None for index in range(self.data.ray_length)] for ri in range(len(self.data.render_rays))]
        #
