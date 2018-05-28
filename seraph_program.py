import random, time, datetime
from copy import copy
from seraph_utils import *
from collections import deque
# from scipy import signal
# import numpy as np

import logging

logger = logging.getLogger(__name__)


class Program:
    def __init__(self, dancer, mode, options={}):
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

        if self.mode == 'seekers':
            self.init_seekers(options)
            self.update = self.update_seekers

        if self.mode == 'keyboard_input':
            self.init_keyboard_input()
            self.update = self.update_keyboard_input

        if self.mode == 'serial_input':
            self.init_serial_input()
            self.update = self.update_serial_input

    # PROGRAM: serial_input
    # for debugging and implementation

    def init_serial_input(self):
        self.p['last_input'] = [];

    def update_serial_input(self):
        logger.debug('getting serial input')

        try:
            ser_bytes = self.dancer.serial.readline()
        except:
            return

        message = ser_bytes
        if len(message) == 0:
            return
        message = message.decode('ascii').split()
        if message[0] != '3':
            return

        message = [int(num, 16) for num in message]

        self.p['last_input'] = message[2:5]

        print(self.p['last_input'])

    


    # PROGRAM: keyboard_input
    # for debugging and implementation
    def init_keyboard_input(self):
        self.p['last_input'] = ''

    def update_keyboard_input(self):
        print('before input')
        self.p['last_input'] = input('hello: ')
        print(self.p['last_input'])
        print('after input')

    # PROGRAM: Slow_Changes
    # wanders full background hue through colors randomly
    def init_slow_changes(self):
        self.p['wanderer'] = Wanderer(1, 80)
        self.p['shader'] = self.dancer.rayset.create_shader('full_color_H', 'h', 'single_parameter', {}, 'add')

    def update_slow_changes(self):
        # logger.debug('interval: %s', 1.0/(time.time() - self.last_update_time))
        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0
        self.p['wanderer'].update()

        self.dancer.rayset.shaders['full_color_H'].generate_parameters['value'] = self.p['wanderer'].pos_curr[0] * 2
        # logger.debug('hue: %s', self.p['wanderer'].pos_curr[0])


    # PROGRAM: Peacock
    # oscillates hue and brightness waves on rays excited by pads
    def init_peacock(self):
        self.p['start_time'] = time.time()
        self.p['excitement'] = [0] * self.dancer.padset.num_pins
        self.p['excitement_accumulation'] = [0] * self.dancer.padset.num_pins
        self.p['sprite_shaders_l'] = []
        self.p['sprite_shaders_h'] = []
        self.p['use_jump_on'] = True
        self.p['base_hues'] = generate_distributed_values(self.dancer.padset.num_pins, 0.2)

        self.p['sprite_center_locations'] = [(1.0 / self.dancer.padset.num_pins * n + self.dancer.pad_sensor_offset) % 1.0 for n in range(self.dancer.padset.num_pins)]
        # sprite_lengths = [.03 + .04 * (n / self.dancer.padset.num_pins) for n in range(self.dancer.padset.num_pins)]
        for n in range(self.dancer.padset.num_pins):
            shad = self.dancer.rayset.create_shader('peacock_' + str(n) + '_l', 'l', 'circularsprite',
                                                    {'center': self.p['sprite_center_locations'][n], 'value_base': 0, 'length': .1},
                                                    'add')
            self.p['sprite_shaders_l'].append(shad)

            shad = self.dancer.rayset.create_shader('peacock_' + str(n) + '_h', 'h', 'circularsprite',
                                                    {'center': self.p['sprite_center_locations'][n], 'value_base': 0, 'length': .1},
                                                    'blend')
            self.p['sprite_shaders_h'].append(shad)

        interval = 2
        self.p['wanderers'] = [Wanderer(3, interval) for i in range(self.dancer.padset.num_pins)]

        # sensor position testing stimulus
        # self.p['distance_around_time'] = 0.00
        # self.p['base_length'] = 0.01
        # self.p['length_change_scale'] = 0.0

        self.p['distance_around_time'] = 0.01
        self.p['base_length'] = 0.04
        self.p['length_change_scale'] = 0.1
        self.p['excitement_decay_rate'] = 0.1
        self.p['excitement_max_limit'] = 4

    def update_peacock(self):
        interval = time.time() - self.last_update_time
        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0 / 30
        
        #logger.debug(self.p['excitement_accumulation'])

        # add pad values to change excitement levels toward pads
        #logger.debug(self.dancer.padset.val_filtered)
        for i, pad in enumerate(self.dancer.padset.val_filtered):

            if self.p['use_jump_on'] and pad and self.p['excitement'][i] < .03:
                self.p['excitement'][i] = 0.2  # jump to 1 from off

            if pad * 1.0 > self.p['excitement'][i]:
                self.p['excitement'][i] = clamp_value(self.p['excitement'][i] + 1.2 * interval)
                self.p['excitement_accumulation'][i] += interval * .3

            if pad * 1.0 < self.p['excitement'][i]:
                self.p['excitement'][i] = clamp_value(self.p['excitement'][i] - 0.6 * interval)

            if self.p['excitement_accumulation'][i] > self.p['excitement_max_limit']:
                self.p['excitement_accumulation'][i] = copy(self.p['excitement_max_limit'])

            self.p['excitement_accumulation'][i] -= self.p['excitement_decay_rate'] * interval

            # change width and position with wanderer
            self.p['wanderers'][i].update()
            for component in ('l', 'h'):  # component, base, multiply (for the value which gets shaded)
                parameters = self.p['sprite_shaders_'+component][i].generate_parameters
                parameters['center'] = self.p['sprite_center_locations'][i] + (self.p['wanderers'][i].pos_curr[0] - 0.5) * self.p[
                    'distance_around_time']
                parameters['length'] = self.p['base_length'] + clamp_value(
                    self.p['wanderers'][i].pos_curr[1] * self.p['length_change_scale'])
                # parameters['value'] = float(component[2]) * self.p['wanderers'][si].pos_curr[2] + component[1]
                # logger.debug('component: %s params: %s wander: %s', component[0], parameters, self.p['wanderers'][wi].pos_curr)

            # update sprites to excitement levels
            self.p['sprite_shaders_l'][i].generate_parameters['value'] = self.p['excitement'][i] * .8
            self.p['sprite_shaders_h'][i].generate_parameters['value'] = self.p['base_hues'][i]
                                                                         
            #logger.debug(self.p['sprite_shaders_h'][i].generate_parameters['value'])

    # PROGRAM: Seekers
    # little creatures with bodies move about in reaction to hands
    # sprites move around the ring toward hands or the sun

    def init_seekers(self, options={}):
        self.p['count'] = 9
        colors = generate_distributed_values(self.p['count'], .1)
        self.p['seekers'] = [self.Seeker(self.dancer, a, self.p['count'], colors[a]) for a in range(self.p['count'])]
        
        if options.get('random_motion', False):
            self.p['random_motion'] = True


    def update_seekers(self):
        pad_values = self.dancer.padset.val_filtered

        for seeker in self.p['seekers']:
            seeker.update(pad_values)

    class Seeker:

        def __init__(self, dancer, index, count, color):
            self.dancer = dancer
            self.index = index

            self.hue = color
            self.hue_velocity_shift = 0.01
            self.luminance_base = 0.5
            self.velocity_luminance_increment = 4
            self.hand_attitude = 1 if index / count > 0.3 else -1

            self.length = .05 # + .01 * random.random()

            self.velocity = 0
            self.acceleration = 0
            self.force = 0
            self.position = random.random()
            self.luminance = 0

            self.mass = .02 + random.random() * .1
            self.force_increment = .25
            self.drag_value = 0.3
            self.hue_shift_increment = 0.3


            self.desired_position = 0
            self.previous_pad_values = []
            self.last_physics_update_time = time.time()
            self.last_goal_update_time = time.time()

            shad_l = self.dancer.rayset.create_shader(index * 1000 + 1, 'l', 'circularsprite',
                                                      {'value_base': 0, 'value': self.luminance,
                                                       'length': self.length,
                                                       'center': self.position}, 'add')
            shad_h = self.dancer.rayset.create_shader(index * 1000 + 2, 'h', 'circularsprite',
                                                      {'value_base': 0, 'value': 0,
                                                       'length': self.length,
                                                       'center': self.position}, 'add')
            self.shaders = {'h': shad_h, 'l': shad_l}

        def update(self, pad_values):
            interval = time.time() - self.last_physics_update_time

            if pad_values != self.previous_pad_values or self.last_goal_update_time + 10 < time.time():
                self.desired_position = self.calculate_desired_position(pad_values)
                self.last_goal_update_time = time.time()
            self.previous_pad_values = copy(pad_values)

            # find closest direction to desired position
            position_goal_diff = self.desired_position - self.position
            distances = (abs(position_goal_diff), abs(position_goal_diff + 1), abs(position_goal_diff - 1))
            min_distance_index = min(range(len(distances)), key=distances.__getitem__)
            # logger.debug('seeker %s min_distance_index %s', self.index, min_distance_index)
            force_magnitude = min([abs(position_goal_diff) * 2, 0.5])

            self.force = self.force_increment
            if min_distance_index == 0:
                if position_goal_diff > 0:
                    self.force *= force_magnitude
                else:
                    self.force *= -force_magnitude
            elif min_distance_index == 1:
                self.force *= force_magnitude
            elif min_distance_index == 2:
                self.force *= -force_magnitude

            self.hue_velocity_shift = self.hue_shift_increment * self.acceleration * sign(self.velocity)

            self.luminance = abs(self.velocity) * self.velocity_luminance_increment + self.luminance_base
            # if abs(self.velocity) < self.velocity_luminance_threshold and abs(self.acceleration) < self.velocity_luminance_threshold:
            #     self.luminance = self.luminance_low
            # else:
            #     self.luminance = self.luminance_high

            self.force *= random.random() - .2  # randomly jiggle force vector, sometimes even flip it
            # logger.debug('seeker %s pos: %s desired: %s force: %s vel: %s', self.index, self.position, self.desired_position, self.force, self.velocity)

            self.update_physics(interval)

            self.update_shaders()

            # logger.debug('Seeker %s lum: %s', self.index, self.shaders['l'].generate_parameters['value'])

        def update_shaders(self):
            self.shaders['l'].generate_parameters['center'] = self.position
            self.shaders['h'].generate_parameters['center'] = self.position
            self.shaders['h'].generate_parameters['value'] = self.hue + self.hue_velocity_shift
            self.shaders['l'].generate_parameters['value'] = self.luminance

        def update_physics(self, interval):
            self.acceleration = self.force / self.mass * interval
            self.velocity += self.acceleration * interval
            self.velocity -= self.drag_value * self.velocity * interval
            self.position += self.velocity * interval
            self.position %= 1.0

            self.last_physics_update_time = time.time()

        def calculate_desired_position(self, pad_values):
        
            desired_position = random.random()
            
			
            # do vector#  sum of angles
#             if not any(pad_values):
#                 now = datetime.datetime.now()
#                 sundial_position = ((now.hour / 24.0 + now.minute / (24 * 60.0) + now.second / (24.0 * 60 * 60)) +
#                                     self.dancer.sundial_time_offset) % 1.0
#                 desired_position = sundial_position
#                 # logger.debug('seeker %s setting solar desired position %s', self.index, desired_position)
#             else:
# 
#                 desired_position = self.dancer.padset.get_mean_hand_position()
# 
#                 if self.hand_attitude < 0:
#                     desired_position = (desired_position + 0.5) % 1
            logger.debug('seeker %s setting new random desired position %s', self.index, desired_position)

            return desired_position



    # PROGRAM: Starry
    def init_starry(self):
        self.p['hide_from_hands'] = False

        star_fill_fraction = 0.03
        self.p['enable_shooting'] = True
        self.p['flicker_amount_l'] = 0.08
        self.p['flicker_amount_h'] = 0.03
        self.p['l_steady'] = 0.22
        self.p.update({'t_rise': 10, 't_steady': 30, 't_fall': 10, 't_shoot': 2, 't_hide': 4, 't_stayhidden': 180})

        self.p['num_stars'] = int(star_fill_fraction * self.dancer.ray_length)
        self.p['star_colors_original'] = [random.random() for a in range(self.p['num_stars'])]
        self.p['star_colors_display'] = [0.0 for a in range(self.p['num_stars'])]
        self.p['star_luminances'] = [copy(self.p['l_steady']) for a in range(self.p['num_stars'])]
        # self.p['star_widths'] = [int(random.random() * 3) for a in range(self.p['num_stars'])]
        self.p['star_nexttime'] = [self.p['t_rise'] + time.time() for a in range(self.p['num_stars'])]
        self.p['star_modes'] = ['rising' for a in range(self.p['num_stars'])]
        self.p['star_locations'] = [random.randint(0, self.dancer.ray_length - 1) for a in
                                    range(self.p['num_stars'])]
        self.p['star_sensor_indices'] = [self.map_location_to_sensor(loc) for loc in self.p['star_locations']]
        self.p['wanderers'] = [Wanderer(2, .1) for a in range(self.p['num_stars'])]
        self.last_update_time = time.time()

        self.p['shader_l'] = self.dancer.rayset.create_shader('starry_l', 'l', 'parameter_by_index', {}, 'add')
        self.p['shader_h'] = self.dancer.rayset.create_shader('starry_h', 'h', 'parameter_by_index', {}, 'add')
        self.p['shader_l'].generate_parameters = {'value': [None] * self.dancer.ray_length}
        self.p['shader_h'].generate_parameters = {'value': [None] * self.dancer.ray_length}

        logger.info('Program Starry initialize, star count: %s, shooting: %s, hiding: %s',
                    self.p['num_stars'], self.p['enable_shooting'], self.p['hide_from_hands'])

    def map_location_to_sensor(self, loc):
        return math.floor(self.dancer.padset.num_pins * ((loc / self.dancer.ray_length
                                                          - self.dancer.pad_sensor_offset
                                                          + 1 / (2 * self.dancer.padset.num_pins)
                                                          + (random.random() - .5) * .05)
                                                         % 1.0))

    def update_starry(self):
        interval = time.time() - self.last_update_time
        self.last_update_time = time.time()

        luminances = [None] * self.dancer.ray_length
        colors = [None] * self.dancer.ray_length
        pad_values = self.dancer.padset.get_value_current()
        for star in range(self.p['num_stars']):

            star_loc = self.p['star_locations'][star]  # set all the star location values to 1
            mode = self.p['star_modes'][star]
            nexttime = self.p['star_nexttime'][star]
            self.p['wanderers'][star].update()

            # if mode == 'steady':
            if self.p['hide_from_hands']:
                # logger.debug(sensor_index)
                if pad_values[self.p['star_sensor_indices'][star]]:
                    self.p['star_modes'][star] = 'hiding'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_hide']
                    # logger.debug('star %s hiding from pad %s', star, self.p['star_sensor_indices'][star])

            if mode == 'rising':
                self.p['star_luminances'][star] += interval / self.p['t_rise']
                # lum = self.p['l_steady'] * (1 - (nexttime - time.time()) / self.p['t_rise'])
                if self.p['star_luminances'][star] > self.p['l_steady']:
                    self.p['star_modes'][star] = 'steady'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_steady'] * (0.5 + random.random())
                    self.p['star_luminances'][star] = self.p['l_steady']
                    # logger.debug('star %s going steady', star)

            elif mode == 'steady':
                mu = (1 + (self.p['wanderers'][star].pos_curr[0] - .5) * self.p['flicker_amount_h'])
                self.p['star_luminances'][star] = mu * self.p['l_steady']

                ad = (self.p['wanderers'][star].pos_curr[1] - .5) * self.p['flicker_amount_l']
                self.p['star_colors_display'][star] = ad + self.p['star_colors_original'][star] % 1
                # logger.debug('mult L: %s, add H: %s', mu, ad)

                if self.p['enable_shooting'] and random.random() < 0.00002:
                    self.p['star_modes'][star] = 'shooting'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_shoot']
                elif time.time() > nexttime:
                    self.p['star_modes'][star] = 'falling'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_fall']
                    # logger.debug('star %s falling from steady', star)

            elif mode == 'shooting':
                move = 1 if self.p['star_luminances'][star] * 100 % 2 > 1 else -1
                if (nexttime - time.time()) < 0.6 * self.p['t_shoot']:
                    move *= 2
                    self.p['star_luminances'][star] *= 2
                if (nexttime - time.time()) < 0.1 * self.p['t_shoot']:
                    move *= 2
                    self.p['star_luminances'][star] *= 2
                self.p['star_locations'][star] += move
                self.p['star_locations'][star] = int(self.p['star_locations'][star])
                if time.time() > nexttime:
                    self.p['star_locations'][star] = random.randint(0, self.dancer.ray_length - 1)
                    self.p['star_modes'][star] = 'rising'
                    self.p['star_luminances'][star] = 0
                    # self.p['star_nexttime'][star] = time.time() + self.p['t_rise']

            elif mode == 'falling':
                self.p['star_luminances'][star] -= interval / self.p['t_fall']

                if self.p['star_luminances'][star] <= 0:
                    newloc = self.p['star_locations'][star]
                    while newloc in self.p['star_locations']:
                        newloc = random.randint(0, self.dancer.ray_length - 1)
                        # print newloc
                    self.p['star_locations'][star] = newloc
                    self.p['star_modes'][star] = 'rising'
                    # self.p['star_nexttime'][star] = time.time() + self.p['t_rise']
                    # print 'rise from falling', time.time(), self.p['star_nexttime'][star]
                    # logger.debug('star %s rising next', star)

            elif mode == 'hiding':
                self.p['star_luminances'][star] -= interval / self.p['t_hide']

                if self.p['star_luminances'][star] <= 0:
                    self.p['star_modes'][star] = 'hidden'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_stayhidden'] * (
                    1 + random.random() * .5 - 0.25)
                    # logger.debug('star %s staying hidden', star)

            elif mode == 'hidden':
                self.p['star_luminances'][star] = 0
                self.p['star_colors_display'][star] = None
                if time.time() > nexttime:
                    self.p['star_modes'][star] = 'rising'
                    self.p['star_nexttime'][star] = time.time() + self.p['t_rise']
                    # logger.debug('star %s coming out of hiding', star)

            star_loc %= self.dancer.ray_length
            # width = self.p['star_widths']
            # center =
            # for offset in range(1,width):


            # if lum > 0.7:
            #     logger.debug('%s %s %s', star, lum, self.p['star_modes'][star])
            luminances[star_loc] = self.p['star_luminances'][star]
            colors[star_loc] = self.p['star_colors_display'][star]
            # print lums[star_loc], self.p['lum_wanderers'][star].pos_curr[0]

        self.dancer.rayset.shaders['starry_l'].generate_parameters['value'] = luminances
        self.dancer.rayset.shaders['starry_h'].generate_parameters['value'] = colors

    # PROGRAM: Clockring (hehe)
    # sprite at the time
    def init_clockring(self):
        self.p['shaders'] = {}
        self.p['shaders']['l'] = self.dancer.rayset.create_shader('clock_l', 'l', 'circularsprite', {}, 'add')
        self.p['shaders']['h'] = self.dancer.rayset.create_shader('clock_h', 'h', 'circularsprite', {}, 'blend')

        interval = 5
        self.p['wanderer'] = Wanderer(3, interval)

        self.p['distance_around_time'] = 0.1
        self.p['base_length'] = 0.07
        self.p['length_change_scale'] = 0.2

        self.p['state'] = 'visible'  # 'hidden', 'rising', 'falling'
        self.p['luminance_visible'] = 0.3
        self.p['current_luminance'] = copy(self.p['luminance_visible'])
        self.p['luminance_change_per_second'] = 0.1
        self.p['hide_duration'] = 30

    def update_clockring(self):
        interval = time.time() - self.last_update_time
        self.last_update_time = time.time()

        now = datetime.datetime.now()
        sundial_time = ((now.hour / 24.0 + now.minute / (24 * 60.0) + now.second / (24.0 * 60 * 60)) +
                        self.dancer.sundial_time_offset) % 1.0
        sundial_time += 0.5 # make anti-clockring
        sundial_time %= 1
        # logger.debug('Sundial time 0-1: %s', sundial_time)

        self.p['wanderer'].update()

        # hand sensor hiding state machine
        if self.p['state'] == 'visible':
            self.p['current_luminance'] = copy(self.p['luminance_visible'])
            if any(self.dancer.padset.get_value_current()):
                self.p['state'] = 'falling'

        elif self.p['state'] == 'hidden':
            self.p['current_luminance'] = 0
            if any(self.dancer.padset.get_value_current()):
                self.p['hide_end_time'] = time.time() + self.p['hide_duration']
            if time.time() > self.p['hide_end_time']:
                self.p['state'] = 'rising'

        elif self.p['state'] == 'rising':
            self.p['current_luminance'] += interval * self.p['luminance_change_per_second']
            if self.p['current_luminance'] >= self.p['luminance_visible']:
                self.p['current_luminance'] = copy(self.p['luminance_visible'])
                self.p['state'] = 'visible'

        elif self.p['state'] == 'falling':
            self.p['current_luminance'] -= interval * self.p['luminance_change_per_second']
            if self.p['current_luminance'] <= 0:
                self.p['current_luminance'] = 0
                self.p['state'] = 'hidden'
                self.p['hide_end_time'] = time.time() + self.p['hide_duration']

        # generate components based on wanderer values
        for component in (('l', self.p['current_luminance'], self.p['current_luminance']), ('h', 0, -4.0)):  # component, base, multiply (for the value which gets shaded)
            # for component in (('h', 0, 1.0),):  # component, base, multiply # disable luminance
            parameters = self.p['shaders'][component[0]].generate_parameters
            parameters['center'] = sundial_time + (self.p['wanderer'].pos_curr[0] - 0.5) * self.p[
                'distance_around_time']
            parameters['length'] = self.p['base_length'] + clamp_value(
                self.p['wanderer'].pos_curr[1] * self.p['length_change_scale'])
            parameters['value'] = float(component[2]) * self.p['wanderer'].pos_curr[2] + component[1]
            # logger.debug('component: %s params: %s wander: %s', component[0], parameters, self.p['wanderers'][wi].pos_curr)

        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + .02


    # PROGRAM: Monochrome
    # varies saturation of the whole display to change to B&W for fun
    # maybe go monochrome until a ray is touched by hand
    def init_monochrome(self):
        self.p['shader'] = self.dancer.rayset.monochrome()

    def update_monochrome(self):
        pass



    def init_checkers(self):
        self.p['shader'] = self.dancer.rayset.checkers(range(self.dancer.num_rays))

    def update_checkers(self):
        pass

    # PROGRAM: Ghost
    # when idle, activates pads to ghost a user
    def init_ghost(self):
        self.p['hand_positions'] = [0,1,2,3,4,5]
        self.p['hand_switch_time'] = time.time()

    def update_ghost(self):
        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0 / 4

        # if newly idle
        pad_values = self.dancer.padset.get_value_filtered()
        if sum(pad_values) == 0 and time.time() > self.dancer.idle_timeout + self.dancer.last_pad_change_time:
            self.dancer.idle_mode = True
        else:
            self.dancer.idle_mode = False

        # if idle
        if self.dancer.idle_mode:
            if time.time() > self.p['hand_switch_time']:
                self.p['hand_switch_time'] = time.time() + random.random() * 3 + 0.5
                # self.p['hand_positions'] = [random.randrange(self.dancer.num_rays / 2), random.randrange(self.dancer.num_rays / 2) + self.dancer.num_rays / 2]
                self.p['hand_positions'] = [random.randrange(self.dancer.padset.num_pins)]
                # print 'ghost hands', self.p['hand_positions']

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
        if self.p.get('flash_state', False):  # flash only one frame, so turn off immediately
            # self.dancer.rayset.shaders['handsense'].active_rays = []
            self.p['shader'].generate_parameters = {'value': 0}
            self.p['flash_state'] = False

        if self.dancer.idle_mode:
            return

        pad_values = self.dancer.padset.get_value_filtered()
        logger.debug('hand sensor value readin: %s', pad_values)
        # logger.debug('previous value: %s', self.p['sensor_values'])

        pad_changed = not (pad_values == self.p['sensor_values'])
        logger.debug('pad changed: %s', pad_changed)

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
        self.next_update_time = self.last_update_time + 1.0 / 15

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
                # print self.p['shaders']['l'].generate_parameters['value']


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
                    self.p['progress'] = 0  # reset

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
            shads = self.dancer.rayset.ring(rays, wi, (('l', 'multiply'), ('h', 'add')))
            shads['h'].generate_parameters['value_base'] = 0
            self.p['shaders'].append(shads)

        intervals = [4, 5, 6, 8, 10]
        self.p['wanderers'] = [Wanderer(3, intervals[i]) for i in range(self.p['count'])]

    def update_ring(self):
        for wi in range(self.p['count']):
            self.p['wanderers'][wi].update()
            for component in (('l', .4, 0.3), ('h', 0, 1.0)):  # component, base, multiply
                # for component in (('h', 0, 1.0),):  # component, base, multiply # disable luminance

                parameters = self.p['shaders'][wi][component[0]].generate_parameters
                parameters['center'] = self.p['wanderers'][wi].pos_curr[0]
                parameters['length'] = 0.03 + clamp_value(self.p['wanderers'][wi].pos_curr[1] / 3.0)
                parameters['value'] = float(component[2]) * self.p['wanderers'][wi].pos_curr[2] + component[1]

        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0 / 100

    # PROGRAM: Sparkle
    def init_sparkle(self):
        self.p['location'] = [random.randint(0, self.dancer.num_rays - 1)]
        # print 'sparkle', self.p['location']
        self.dancer.rayset.sparkle(self.p['location'])
        # self.dancer.rayset.shaders['sparkle'].active_indices = range(10, 20)
        self.dancer.rayset.shaders['sparkle'].generate_parameters['num_points'] = 1

        self.p['state'] = 'wait for match'

    def update_sparkle(self):
        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0 / 60

        if self.p['state'] == 'wait for match':
            pad_values = self.dancer.padset.val_filtered
            if pad_values[self.p['location'][0]]:
                self.dancer.rayset.shaders['sparkle'].generate_parameters['num_points'] = 4
                # self.dancer.rayset.shaders['sparkle'].active_indices = range(20)
                self.p['state'] = 'show match'
                self.p['show match timeout'] = time.time() + 0.3

        if self.p['state'] == 'show match' and self.p['show match timeout'] < time.time():
            self.p['state'] = 'wait for match'
            self.p['location'] = [random.randint(0, self.dancer.num_rays - 1)]
            self.dancer.rayset.shaders['sparkle'].active_rays = self.p['location']
            self.dancer.rayset.shaders['sparkle'].generate_parameters['num_points'] = 1
            # self.dancer.rayset.shaders['sparkle'].active_indices = range(10, 20)
            # print 'sparkle', self.p['location']

            # print self.p['hue_velocity']

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

        self.p['shader'].generate_parameters['value'] = [self.p['pattern'][self.p['offset'] + pi] for pi in
                                                         range(self.dancer.ray_length)]

        self.last_update_time = time.time()
        self.next_update_time = self.last_update_time + 1.0 / 30


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
    #         # print 'beat interval', time.time() - self.p['previous_beat']
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
    #     # print 'score', self.p['score']
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
    #         # print 'game target', p
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
            if time.time() - self.time[1] > 10:  # NTP update occurred and the time diff is huge
                self.reset(self.dim, self.time_interval)
            self.new_next()

        t = time.time()
        self.pos_curr = [self.c[0][d]
                         + self.c[1][d] * (t - self.time[0])
                         + self.c[2][d] * (t - self.time[0]) * (t - self.time[1])
                         for d in range(self.dim)]

        # if sum([self.pos_curr[d] < 0 for d in range(self.dim)]) > 0:
        #     # print self.pos_curr
        #     # print self.pos
        #     # print self.c
        #     # print [self.time[a] - time.time() for a in range(3)]
        #     print

