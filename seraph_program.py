import random, time, datetime
from seraph_utils import *
from collections import deque
# from scipy import signal
# import numpy as np

import logging
logger = logging.getLogger(__name__)

class Program:

    def __init__(self, dancer, mode):
        self.dancer = dancer
        self.next_update_time = 0
        self.last_update_time = 0
        self.mode = mode
        self.p = {}

        logger.info('Program start: %s', mode)

        # if self.mode == 'game':
        #     self.init_game()
        #     self.update = self.update_game
        #     return

        if self.mode == 'peacock':
            self.init_peacock()
            self.update = self.update_peacock

        if self.mode == 'ghost':
            self.init_ghost()
            self.update = self.update_ghost

        if self.mode == 'slow_changes':
            self.init_slow_changes()
            self.update = self.update_slow_changes

        if self.mode == 'handsense':
            self.init_handsense()
            self.update = self.update_handsense

        if self.mode == 'sparkle':
            self.init_sparkle()
            self.update = self.update_sparkle

        if self.mode == 'ring':
            self.init_ring()
            self.update = self.update_ring

        if self.mode == 'checkers':
            self.init_checkers()
            self.update = self.update_checkers

        if self.mode == 'monochrome':
            self.init_monochrome()
            self.update = self.update_monochrome

        if self.mode == 'handglow':
            self.init_handglow()
            self.update = self.update_handglow

        if self.mode == 'chase':
            self.init_chase()
            self.update = self.update_chase

        if self.mode == 'starry':
            self.init_starry()
            self.update = self.update_starry

        if self.mode == 'clockring':
            self.init_clockring()
            self.update = self.update_clockring

    # PROGRAM: Slow_Changes
    # wanders full background hue through colors randomly
    def init_slow_changes(self):
        self.p['hue_velocity'] = [0] * self.dancer.num_rays
        # self.p['light_velocity'] = [0] * self.dancer.num_rays
        self.p['wanderer'] = Wanderer(1, 10)

    def update_slow_changes(self):
        interval = (time.time() - self.last_update_time) * 20.0
        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0/20

        self.p['wanderer'].update()
        for i in range(self.dancer.num_rays):
            # self.p['hue_velocity'][i] = 0
            # print interval,self.p['hue_velocity'][i],
            # self.p['hue_velocity'][i] += (0.01 * (random.random() - 0.5)) * interval
            # self.p['hue_velocity'][i] /= 1.1 * interval
            self.p['hue_velocity'][i] = self.p['wanderer'].pos_curr[0] * 0.001 * interval
            # print self.p['wanderer'].pos_curr
            #
            # self.p['light_velocity'][i] += (0.01 * (random.random() - 0.5)) * interval
            # self.p['light_velocity'][i] /= 1.1 * interval
            # print self.p['hue_velocity'][i]


        # Shift the base hue
        # self.dancer.rayset.shaders['full_color_H'].generate_parameters['value'] = \
        #    [self.p['hue_velocity'][i] + self.dancer.rayset.shaders['full_color_H'].generate_parameters['value'][i] for i in range(self.dancer.num_rays)]

        self.dancer.rayset.shaders['full_color_H'].generate_parameters['value'][i] = self.p['wanderer'].pos_curr[0] * 2

        # self.dancer.rayset.shaders['full_brightness'].generate_parameters['value'] = \
        #    [self.p['hue_velocity'][i] + self.dancer.rayset.shaders['full_brightness'].generate_parameters['value'][i] for i in range(self.dancer.num_rays)]
        # print self.p['hue_velocity']


    # PROGRAM: Handglow
    # increases luminance and saturation where the hands are & have been
    def init_handglow(self):
        self.p['shaders'] = {}
        self.p['shaders']['l'] = \
            self.dancer.rayset.create_shader('handglow', 'l', 'parameter_by_ray',
                                             {'value': [0] * self.dancer.num_rays},
                                             'multiply', list(range(self.dancer.num_rays)))
        self.p['num_points'] = 40
        self.p['hand_timelines'] = [deque([], self.p['num_points']) for i in range(self.dancer.num_rays)]

        # self.p['filter'] = signal.iirdesign(0.5, 0.6, 5, 40)
        # print 'filter', self.p['filter']

    def update_handglow(self):
        # print 1.0 / (time.time() - self.last_update_time)
        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0/15

        for ri in range(self.dancer.num_rays):
            # add point now
            self.p['hand_timelines'][ri].append([self.dancer.padset.val_current[ri], time.time()])

            if len(self.p['hand_timelines'][ri]) > 20:
                x = [entry[0] * 1 for entry in self.p['hand_timelines'][ri]]
                # y = signal.filtfilt(self.p['filter'][0], self.p['filter'][1], x)
                # if ri == 0:
                    # print np.absolute(np.fft.rfft(x))
                # value = np.absolute(y[len(y)-1])
                value = float(sum(x)) / len(self.p['hand_timelines'][ri]) + 0
                self.p['shaders']['l'].generate_parameters['value'][ri] = value
        print self.p['shaders']['l'].generate_parameters['value']


    # PROGRAM: Peacock
    # oscillates hue and brightness waves on rays excited by pads
    def init_peacock(self):
        self.p['start_time'] = time.time()
        self.p['excitements'] = [0] * self.dancer.padset.num_pins

        self.p['sprite_shaders'] = [self.dancer.rayset.create_shader('peacock_' + str(n), 'l', 'circularsprite',
                                   {'center': 1.0/self.dancer.padset.num_pins * n, 'value_base': 0, 'length':0.03}, 'add') for n in range(self.dancer.padset.num_pins)]


    def update_peacock(self):
        interval = (time.time() - self.last_update_time) * 20.0
        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0/20


        # add pad values to change excitement levels toward pads
        for i, pad in enumerate(self.dancer.padset.val_filtered):
            if pad * 1.0 > self.p['excitements'][i]:
                self.p['excitements'][i] = clamp_value(self.p['excitements'][i] + 0.02 * interval)

            if pad * 1.0 < self.p['excitements'][i]:
                self.p['excitements'][i] = clamp_value(self.p['excitements'][i] - 0.05 * interval)


        # update rays to excitement levels
        for pi in range(self.dancer.padset.num_pins):
            self.p['sprite_shaders'][pi].generate_parameters['value'] = self.p['excitements'][pi] / 2.0
        # logger.debug(self.p['excitements'])
        # logger.debug([shad.generate_parameters for shad in self.p['sprite_shaders']])



    def init_checkers(self):
        self.p['shader'] = self.dancer.rayset.checkers(range(self.dancer.num_rays))

    def update_checkers(self):
        pass

    # PROGRAM: Ghost
    # when idle, activates pads to ghost a user
    def init_ghost(self):
        self.p['hand_positions'] = [0, 5]
        self.p['hand_switch_time'] = time.time()

    def update_ghost(self):
        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0/4

        # if newly idle
        pad_values = self.dancer.padset.val_filtered
        if sum(pad_values) == 0 and time.time() > self.dancer.idle_timeout + self.dancer.last_pad_change_time:
            self.dancer.idle_mode = True
        else:
            self.dancer.idle_mode = False

        # if idle
        if self.dancer.idle_mode:
            if time.time() > self.p['hand_switch_time']:
                self.p['hand_switch_time'] = time.time() + random.random() * 3 + 0.5
                # self.p['hand_positions'] = [random.randrange(self.dancer.num_rays / 2), random.randrange(self.dancer.num_rays / 2) + self.dancer.num_rays / 2]
                self.p['hand_positions'] = [random.randrange(self.dancer.num_rays)]
                print 'ghost hands', self.p['hand_positions']

            for pos in range(self.dancer.num_rays):
                self.dancer.padset.pads[pos].value = (pos in self.p['hand_positions'])


    # PROGRAM: HandSense
    # marks where hands move with little single-frame flashes to help interaction guidance
    def init_handsense(self):
        self.next_update_time = 0  # always run
        self.p['sensor_values'] = [0] * self.dancer.padset.num_pins
        self.p['ray_timeout'] = [0] * self.dancer.padset.num_pins
        self.p['shader'] = self.dancer.rayset.create_shader('handsense', 'l', 'single_parameter', {}, 'add')
        self.p['shader'].generate_parameters = {'value': 0}

    def update_handsense(self):
        if self.p.get('flash_state', False): # flash only one frame, so turn off immediately
            # self.dancer.rayset.shaders['handsense'].active_rays = []
            self.p['shader'].generate_parameters = {'value': 0}
            self.p['flash_state'] = False

        if self.dancer.idle_mode:
            return

        pad_values = self.dancer.padset.get_value_filtered()
        # logger.debug('hand sensor value readin: %s', pad_values)
        # logger.debug('previous value: %s', self.p['sensor_values'])

        pad_changed = not(pad_values == self.p['sensor_values'])
        # logger.debug('pad changed: %s', pad_changed)

        if pad_changed:
            logger.debug('sensor changed')
            for ri in range(self.dancer.padset.num_pins):
                if pad_values[ri] and not self.p['sensor_values'][ri] and time.time() > self.p['ray_timeout'][ri]:
                    logger.debug('hand flash on sensor %s', ri)
                    # print 'flash!', ri

                    # newly active sensor, so flash ray
                    self.p['flash_state'] = True
                    self.p['ray_timeout'][ri] = time.time() + 0.5
                    self.p['shader'].generate_parameters = {'value': .04}
                    # self.dancer.rayset.shaders['handsense'].active_rays.append(ri)
                    # self.dancer.rayset.shaders['handsense'].active_indices = [random.randrange(self.dancer.rayset.ray_length) for a in range(6)]


            self.p['sensor_values'] = pad_values


                    # self.p['positions'] = [0.5] * self.p['count']
        # self.p['velocities'] = [0.0] * self.p['count']
        # self.p['accelerations'] = [0.0] * self.p['count']
        # self.p['jerks'] = [0.0] * self.p['count']
        # self.p['hue'] = 0.0

    # PROGRAM: Chase
    # display random ray with timer, if correct sensor hit during timer: flash all rays
    # if N in a row correct, do something big
    def init_chase(self):
        self.p['current_ray'] = None
        self.p['start_time'] = time.time()
        self.p['duration'] = 1.0
        self.p['end_time'] = time.time() + self.p['duration']
        self.p['wait_time'] = 2.0
        self.p['next_time'] = self.p['end_time'] + self.p['wait_time']
        self.p['progress'] = 0
        self.p['celebrate_active'] = False
        self.p['celebrate_end_time'] = 0
        self.p['celebrate_base_duration'] = 1.0

        self.p['active_shader_h'] = \
            self.dancer.rayset.create_shader('chase_active_h', 'h', 'sprite',
                                             {'value': 1.0, 'value_base': 0.5, 'center': 0.0, 'length': 0.1},
                                             'replace', [])
        self.p['active_shader_l'] = \
            self.dancer.rayset.create_shader('chase_active_l', 'l', 'sprite',
                                             {'value': 1.0, 'value_base': 0.0, 'center': 0.0, 'length': 0.1},
                                             'replace', [])

        self.p['celebrate_shader_h'] = \
            self.dancer.rayset.create_shader('chase_celebrate_h', 'h', 'single_parameter',
                                             {'value': 0.5}, 'replace', [])
        self.p['celebrate_shader_l'] = \
            self.dancer.rayset.create_shader('chase_celebrate_h', 'l', 'single_parameter',
                                             {'value': 1.0}, 'replace', [])

    def update_chase(self):
        t = time.time()

        # update celebration state
        if self.p['celebrate_active']:
            if t > self.p['celebrate_end_time']:
                self.p['celebrate_active'] = False

        # possibly activate a ray
        if t > self.p['next_time']:
            self.p['start_time'] = t
            self.p['end_time'] = t + self.p['duration']
            self.p['next_time'] = self.p['end_time'] + self.p['wait_time']
            self.p['current_ray'] = random.randint(self.dancer.num_rays)


        # have active ray, update
        if self.p['current_ray'] is not None:
            if t > self.p['end_time']:
                self.p['current_ray'] = None
                if self.p['progress'] > 0:
                    self.p['progress'] -= 1

            # move arc position, if active
            center = (t - self.p['start_time']) / self.p['duration']

            self.p['active_shader_h'].active_rays = [self.p['current_ray']]
            self.p['active_shader_l'].active_rays = [self.p['current_ray']]
            self.p['active_shader_h'].generate_parameters['center'] = center
            self.p['active_shader_l'].generate_parameters['center'] = center

            # check for hand position
            if self.dancer.padset.val_filtered[self.p['current_ray']]:
                self.p['current_ray'] = None
                self.p['active_shader_h'].active_rays = []
                self.p['active_shader_l'].active_rays = []
                self.p['progress'] += 1

                celebrate_rays = [self.p['current_ray']]
                celebrate_duration = self.p['celebrate_base_duration']

                # magnify effect based on progress
                if self.p['progress'] > 2:
                    celebrate_duration *= 2
                    for ri in [self.p['current_ray'] - 1, self.p['current_ray'] + 1]:
                        if ri > 0 and ri < self.dancer.num_rays:
                            celebrate_rays.append(ri)


                if self.p['progress'] > 4:
                    celebrate_duration *= 2
                    for ri in [self.p['current_ray'] - 2, self.p['current_ray'] + 2]:
                        if ri > 0 and ri < self.dancer.num_rays:
                            celebrate_rays.append(ri)


                if self.p['progress'] > 8:
                    celebrate_duration *= 2
                    celebrate_rays = list(range(self.dancer.num_rays))
                    self.p['progress'] = 0 # reset

                self.p['celebrate_shader_h'].active_rays = celebrate_rays
                self.p['celebrate_shader_l'].active_rays = celebrate_rays
                self.p['celebrate_end_time'] = t + celebrate_duration
                self.p['next_time'] = self.p['celebrate_end_time'] + self.p['wait_time']

    # PROGRAM: Ring
    # ring of color moves around the display changing radius
    def init_ring(self):
        self.p['count'] = 2
        self.p['shaders'] = []
        rays = range(self.dancer.num_rays)
        for wi in range(self.p['count']):
            shads = self.dancer.rayset.ring(rays, wi, (('l','multiply'), ('h','add')))
            shads['h'].generate_parameters['value_base'] = 0
            self.p['shaders'].append(shads)

        intervals = [4, 5, 6, 8, 10]
        self.p['wanderers'] = [Wanderer(3, intervals[i]) for i in range(self.p['count'])]

    def update_ring(self):
        for wi in range(self.p['count']):
            self.p['wanderers'][wi].update()
            for component in (('l', .4, 0.3), ('h', 0, 1.0)): # component, base, multiply
            # for component in (('h', 0, 1.0),):  # component, base, multiply # disable luminance

                parameters = self.p['shaders'][wi][component[0]].generate_parameters
                parameters['center'] = self.p['wanderers'][wi].pos_curr[0]
                parameters['length'] = 0.03 + clamp_value(self.p['wanderers'][wi].pos_curr[1] / 3.0)
                parameters['value'] = float(component[2]) * self.p['wanderers'][wi].pos_curr[2] + component[1]
                # print component, parameters

        # for i in range(self.p['count']):
            # if self.p['positions'][i] > ray_length / 2:
            #     self.p['accelerations'][i] -= random.random() * 0.001
            # else:
            #     self.p['accelerations'][i] += random.random() * 0.001

            # boundary = 0.2
            # self.p['jerks'][i] = random.gauss(0, .001)
            #
            # if self.p['positions'][i] < boundary:
            #     if self.p['velocities'][i] < 0:
            #         self.p['accelerations'][i] = 0.007
            #
            # if self.p['positions'][i] > 1.0 - boundary:
            #     if self.p['velocities'][i] > 0:
            #         self.p['accelerations'][i] = -0.007
            #
            # self.p['accelerations'][i] += self.p['jerks'][i]
            # self.p['accelerations'][i] *= 0.8
            # self.p['velocities'][i] += self.p['accelerations'][i]
            # self.p['velocities'][i] *= 0.8
            # self.p['positions'][i] += self.p['velocities'][i]
            # self.p['positions'][i] = clamp_value(self.p['positions'][i])
            # print self.p

        # print self.p['positions'], self.p['velocities'], self.p['accelerations'], self.p['jerks']



        # set([int(p * self.dancer.ray_length) for p in self.p['positions']])

        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0/100


    # PROGRAM: Clockring (hehe)
    # sprite at the time
    def init_clockring(self):
        self.p['count'] = 1
        self.p['shaders'] = []
        rays = range(self.dancer.num_rays)
        for wi in range(self.p['count']):
            shads = self.dancer.rayset.ring(rays, wi, (('l','add'),('h','add')))
            shads['l'].generate_parameters['value_base'] = 0
            shads['h'].generate_function = 'circularsprite'
            shads['l'].generate_function = 'circularsprite'
            self.p['shaders'].append(shads)

        self.p['sundial_time_offset'] = 0.5
        intervals = [10, 5, 6, 8, 10]
        self.p['wanderers'] = [Wanderer(3, intervals[i]) for i in range(self.p['count'])]

        self.p['distance_around_time'] = 0.04
        self.p['base_length'] = 0.05
        self.p['length_change_scale'] = 0.02

    def update_clockring(self):

        now = datetime.datetime.now()
        sundial_time = ((now.hour/24.0 + now.minute/(24*60.0) + now.second/(24.0*60*60)) + self.p['sundial_time_offset']) % 1.0
        # logger.debug('Sundial time 0-1: %s', sundial_time)

        for wi in range(self.p['count']):
            self.p['wanderers'][wi].update()
            for component in (('l', 0.1, 0.3),('h', 0, -1.0)): # component, base, multiply (for the value which gets shaded)
            # for component in (('h', 0, 1.0),):  # component, base, multiply # disable luminance
                parameters = self.p['shaders'][wi][component[0]].generate_parameters
                parameters['center'] = sundial_time + (self.p['wanderers'][wi].pos_curr[0] - 0.5) * self.p['distance_around_time']
                parameters['length'] = self.p['base_length'] + clamp_value(self.p['wanderers'][wi].pos_curr[1] * self.p['length_change_scale'])
                parameters['value'] = float(component[2]) * self.p['wanderers'][wi].pos_curr[2] + component[1]
                # logger.debug('component: %s params: %s wander: %s', component[0], parameters, self.p['wanderers'][wi].pos_curr)

        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0/100



    # PROGRAM: Monochrome
    # varies saturation of the whole display to change to B&W for fun
    # maybe go monochrome until a ray is touched by hand
    def init_monochrome(self):
        self.p['shader'] = self.dancer.rayset.monochrome()

    def update_monochrome(self):
        pass

    # PROGRAM: Sparkle
    def init_sparkle(self):
        self.p['location'] = [random.randint(0,self.dancer.num_rays - 1)]
        print 'sparkle', self.p['location']
        self.dancer.rayset.sparkle(self.p['location'])
        # self.dancer.rayset.shaders['sparkle'].active_indices = range(10, 20)
        self.dancer.rayset.shaders['sparkle'].generate_parameters['num_points'] = 1

        self.p['state'] = 'wait for match'

    def update_sparkle(self):
        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0/60

        if self.p['state'] == 'wait for match':
            pad_values = self.dancer.padset.val_filtered
            if pad_values[self.p['location'][0]]:
                self.dancer.rayset.shaders['sparkle'].generate_parameters['num_points'] = 4
                # self.dancer.rayset.shaders['sparkle'].active_indices = range(20)
                self.p['state'] = 'show match'
                self.p['show match timeout'] = time.time() + 0.3

        if self.p['state'] == 'show match' and self.p['show match timeout'] < time.time():
            self.p['state'] = 'wait for match'
            self.p['location'] = [random.randint(0,self.dancer.num_rays - 1)]
            self.dancer.rayset.shaders['sparkle'].active_rays = self.p['location']
            self.dancer.rayset.shaders['sparkle'].generate_parameters['num_points'] = 1
            # self.dancer.rayset.shaders['sparkle'].active_indices = range(10, 20)
            print 'sparkle', self.p['location']

        # print self.p['hue_velocity']


    # PROGRAM: Starry
    def init_starry(self):
        star_fill_fraction = 0.2
        self.p['num_stars'] = int(star_fill_fraction * self.dancer.ray_length)
        self.p['v_steady'] = 0.8
        self.p.update({'t_rise': 10.0, 't_steady': 10.0, 't_fall': 10.0, 't_shoot': 1.0})
        self.p['star_colors'] = [random.random() for a in range(self.p['num_stars'])]
        self.p['star_luminances'] = [random.random() for a in range(self.p['num_stars'])]
        self.p['star_widths'] = [int(random.random() * 3) for a in range(self.p['num_stars'])]
        self.p['star_nexttime'] = [random.randint(0, self.p['t_steady']) * 2 + time.time() for a in range(self.p['num_stars'])]
        self.p['star_modes'] = ['rising' for a in range(self.p['num_stars'])]
        self.p['star_locations'] = [random.randint(0, self.dancer.ray_length - 1) for a in range(self.p['num_stars'])]
        self.p['lum_wanderers'] = [Wanderer(1, .1) for a in range(self.p['num_stars'])]

        self.p['shader_l'] = self.dancer.rayset.create_shader('starry_l', 'l', 'parameter_by_index', {}, 'replace')
        self.p['shader_h'] = self.dancer.rayset.create_shader('starry_h', 'h', 'parameter_by_index', {}, 'add')
        self.p['shader_l'].generate_parameters = {'value': [0] * self.dancer.ray_length}
        self.p['shader_h'].generate_parameters = {'value': [0] * self.dancer.ray_length}


    def update_starry(self):
        lums = [0] * self.dancer.ray_length
        colors = [0] * self.dancer.ray_length
        for star in range(self.p['num_stars']):
            star_loc = self.p['star_locations'][star] # set all the star location values to 1
            mode = self.p['star_modes'][star]
            nexttime = self.p['star_nexttime'][star]
            color = self.p['star_colors'][star]
            # print star, mode

            if mode == 'rising':
                # print nexttime - time.time()
                lum = self.p['v_steady'] * (1 - (nexttime - time.time()) / self.p['t_rise'])
                # print lum
                if time.time() > nexttime:
                    self.p['star_modes'][star] = 'steady'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_steady'] + random.random() * 2

            elif mode == 'steady':
                lum = self.p['v_steady']
                if random.random() < 0.00001:
                    self.p['star_modes'][star] = 'shooting'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_shoot']
                elif time.time() > nexttime:
                    self.p['star_modes'][star] = 'falling'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_fall']

            elif mode == 'shooting':
                lum = self.p['v_steady']# * (nexttime - time.time()) / self.p['t_shoot']
                move = 1 if color * 100 % 2 > 1 else -1
                if (nexttime - time.time()) < 0.6 * self.p['t_shoot']:
                    move *= 2
                    lum *= 2
                if (nexttime - time.time()) < 0.1 * self.p['t_shoot']:
                    move *= 2
                    lum *= 2
                self.p['star_locations'][star] += move
                self.p['star_locations'][star] = int(self.p['star_locations'][star])
                if time.time() > nexttime:
                    self.p['star_locations'][star] = random.randint(0, self.dancer.ray_length - 1)
                    self.p['star_colors'][star] = random.random()
                    self.p['star_modes'][star] = 'rising'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_rise']

            elif mode == 'falling':
                lum = self.p['v_steady'] * (nexttime - time.time()) / self.p['t_fall']
                if time.time() > nexttime:
                    newloc = self.p['star_locations'][star]
                    while newloc in self.p['star_locations']:
                        newloc = random.randint(0, self.dancer.ray_length - 1)
                        # print newloc
                    self.p['star_locations'][star] = newloc
                    self.p['star_colors'][star] = random.random()
                    self.p['star_modes'][star] = 'rising'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_rise']
                    # print 'rise from falling', time.time(), self.p['star_nexttime'][star]

            if star_loc < 0 or star_loc >= self.dancer.ray_length:
                continue
            width = self.p['star_widths']
            # center =
            # for offset in range(1,width):

            # random flicker
            self.p['lum_wanderers'][star].update()
            lum *= self.p['star_luminances'][star] * (1 + self.p['lum_wanderers'][star].pos_curr[0] * .12 - .06)

            lums[star_loc] = lum
            colors[star_loc] = color
            # print lums[star_loc], self.p['lum_wanderers'][star].pos_curr[0]

        self.dancer.rayset.shaders['starry_l'].generate_parameters['value'] = lums
        self.dancer.rayset.shaders['starry_h'].generate_parameters['value'] = colors



    # PROGRAM: Warp
    # generates a color wave pattern that wanders between two wandering colors
    # then wanders velocity through that pattern like a warping space ship
    def init_warp(self):
        self.p['color_wanderer'] = Wanderer(2, 2.0)
        self.p['color_choice_wanderer'] = Wanderer(1, 0.5)
        self.p['velocity_wanderer'] = Wanderer(1, 3.0)

        self.p['pattern'] = [random.random()] * (self.dancer.ray_length * 10)
        self.p['offset'] = 0

        self.p['shader'] = self.dancer.rayset.create_shader('warp', 'h', 'parameter_by_index',
                                                            {'value': [0] * self.dancer.ray_length}, 'add')

    def update_warp(self):

        if self.p['velocity_wanderer'].pos_curr[0] > 0.5:
            # forward (index increase) motion
            self.p['offset'] += int(self.p['velocity_wanderer'].pos_curr[0] * 5)
            self.p['offset'] %= (len(self.p['pattern']) - self.dancer.ray_length)

        self.p['shader'].generate_parameters['value'] = [self.p['pattern'][self.p['offset'] + pi] for pi in range(self.dancer.ray_length)]

        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0/30


'''
    # PROGRAM: GAME (old)
    # def init_game(self):
    #     self.p['state'] = 'start'
    #     self.p['current_pad_target'] = self.make_target(None)
    #     # print(self.current_pad_target)
    #     # set_lights(self.current_pad_target)
    #
    #     # for ray in rayset.rays:
    #     #     ray.vibrate_brightness()
    #
    #     self.p['score'] = 0.5
    #
    #     self.p['beat_count'] = 0
    #     self.p['change_beat_count'] = 4
    #
    #     self.p['beat_period'] = 1 / (bpm / 60)
    #     self.p['previous_beat'] = time.time()
    #     self.p['next_beat'] = time.time() + self.p['beat_period']
    #
    # def update_game(self):
    #
    #     pad_values = [pad.value for pad in pads]
    #
    #     # Got the correct positions
    #     if pad_values == self.current_pad_target:
    #
    #         vol = clamp_value(1.0 - abs(self.p['next_beat'] - time.time()))
    #         sound_good.set_volume(vol)
    #         sound_good.play()
    #         # want to selectively update the beat so it doesn't happen when succeeding
    #         if time.time() - self.p['previous_beat'] > self.p['beat_period'] * 0.666: # nearly at the next beat point already
    #             self.previous_beat += self.beat_period * 2
    #         else: # just add a period on
    #             self.p['previous_beat'] += self.p['beat_period']
    #         self.change_target()
    #         self.change_score(1)
    #
    #     # beat now if we're past it
    #     if time.time() >= self.p['next_beat']:
    #         print 'beat interval', time.time() - self.p['previous_beat']
    #         self.p['previous_beat'] = copy.copy(self.p['next_beat'])
    #         self.p['next_beat'] += self.p['beat_period']
    #
    #         sound_norm.play()
    #
    #         # change targets every four beats
    #         self.p['beat_count'] += 1
    #         if self.p['beat_count'] % self.p['change_beat_count'] == 0:
    #             self.change_target()
    #             self.change_score(0)
    #
    # def change_score(self, change):
    #     self.p['score'] = (self.p['score'] + change) / 2
    #     strip.setBrightness(int(20 + 200 * self.score))
    #     print 'score', self.p['score']
    #
    # def change_target(self):
    #     self.p['current_pad_target'] = self.make_target(self.p['current_pad_target'])
    #     # set_lights(self.p['current_pad_target'])
    #
    #     # print(self.current_pad_target)
    #
    # def make_target(self, prev):
    #     out = prev
    #     while out == prev:
    #         # p = [random.randrange(self.dancer.num_rays / 2), random.randrange(self.dancer.num_rays / 2) + self.dancer.num_rays / 2]
    #         p = random.randrange(self.dancer.num_rays)
    #         print 'game target', p
    #         out = [False] * self.dancer.num_rays
    #         out[p] = True
    #         # out[p[0]] = True
    #         # out[p[1]] = True
    #         # out = [random.choice([True, False]) for i in range(self.dancer.num_rays)]
    #     return out

'''



# UTILITY: Wanderer
# a point varying between 0,1 in several dimensions
# has natural movement attributes
class Wanderer:
    def __init__(self, dim, time_interval):
        self.reset(dim, time_interval)
        self.new_next()

    def reset(self, dim, time_interval):
        self.dim = dim
        self.time_interval = time_interval
        self.pos = [[random.random() for d in range(dim)] for point in range(3)]
        self.time = [time.time() + 0, time.time() + 1, time.time() + 2]
        self.c = [0] * 3
        self.pos_curr = self.pos[0]

        # print self.c
        # print self.pos
        # print self.time
        # print 'go'

    def new_next(self):
        self.pos[0] = self.pos[1]
        self.pos[1] = self.pos[2]
        self.pos[2] = [0.1 + 0.8 * random.random() for d in range(self.dim)]
        
        self.time[0] = self.time[1]
        self.time[1] = self.time[2]
        self.time[2] = self.time_interval * (0.5 + random.random()) + self.time[1]

        self.c[0] = self.pos[0]
        self.c[1] = [(self.pos[1][d] - self.pos[0][d]) * 1.0 / (self.time[1] - self.time[0]) for d in range(self.dim)]
        self.c[2] = [((self.pos[2][d] - self.pos[1][d]) * 1.0 / (self.time[2] - self.time[1])
                      - self.c[1][d]) * 1.0 / (self.time[2] - self.time[1])
                     for d in range(self.dim)]

    def update(self):
        # print self.pos_curr, self.pos_next, self.pos_prev
        if time.time() > self.time[1]:
            if time.time() - self.time[1] > 10: # NTP update occurred and the time diff is huge
                self.reset(self.dim, self.time_interval)
            self.new_next()

        self.pos_curr = [self.c[0][d]
                         + self.c[1][d] * (time.time() - self.time[0])
                         + self.c[2][d] * (time.time() - self.time[0]) * (time.time() - self.time[1])
                         for d in range(self.dim)]

        # if sum([self.pos_curr[d] < 0 for d in range(self.dim)]) > 0:
        #     print self.pos_curr
        #     print self.pos
        #     print self.c
        #     print [self.time[a] - time.time() for a in range(3)]
        #     print