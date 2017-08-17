
import time
from seraph_program import Program
from seraph_rayset import RaySet
from seraph_pad import PadSet

import logging
logger = logging.getLogger(__name__)

class Dancer:


    def setup(self):
        # start input
        self.padset = PadSet(self, self.pads_pins, not self.debug_mode)

        # background shaders
        self.rayset = RaySet(self)
        if self.strip_brightness > 0:
            self.rayset.full_brightness(self.strip_brightness)

        # programs with interactivity code, create shaders and use pad input
        # this acts as the visual layering too, in inverted order
        self.active_programs.append(Program(self, 'slow_changes')) # changes background color randomly slowly
        self.active_programs.append(Program(self, 'seekers')) # glowing sprites at pad locations
        self.active_programs.append(Program(self, 'starry')) # star field of luminance & color modulation
        self.active_programs.append(Program(self, 'clockring')) # color waves moving with the time and activity
        self.active_programs.append(Program(self, 'peacock')) # glowing sprites at pad locations


        # other programs
        # self.active_programs.append(Program(self,'ghost')) # waves hands on pads if nobody is around
        # self.active_programs.append(Program(self,'handglow'))
        # self.active_programs.append(Program(self,'ring')) # pretty waves of color rainbows
        # self.active_programs.append(Program(self,'monochrome'))
        # self.active_programs.append(Program(self, 'chase'))
        # self.active_programs.append(Program(self,'checkers')) # noise waves
        # self.active_programs.append(Program(self,'handsense')) # debug pad data


        #TODO: program: random selection of programs (when a button is pressed, or on reset)


    def __init__(self):
        # configure display hardware:
        # display_length = 144*2-59 # test strip 144/m
        display_length = 144*2+59 # sundial 3.2
        # display_length = 100
        start_shift = 0
        logger.info('Starting display length %s', display_length)

        self.rayset = None
        self.num_rays = 1
        self.num_channels = 1
        # self.channel_pins = [17, 5]
        self.ray_offsets = [start_shift*self.num_rays]
        # self.channel_rays = [list(range(self.num_rays/2)),
        #                      [self.num_rays/2 + r for r in range(self.num_rays/2)]]
        self.channel_rays = [list(range(self.num_rays))]
        # self.pads_pins = [14, 15, 18, 23, 24, 25] # breadboard
        # self.pads_pins = [20,16,21,22,5,6,13,19,26,24,25,12] # protoboard
        padset1 = [12,16,20]
        padset2 = [21,24,25]
        padset3 = [22,5,6]
        padset4 = [26,19,13]
        self.pads_pins = list(reversed(padset1+padset2+padset3+padset4)) # mmm concatenation
        self.pad_mode_buttons = False # use membrane keyboard (short to ground switches)
        self.pad_sensor_offset = 0.305

        self.sundial_time_offset = 0.5

        self.strip_brightness = 0.0
        # self.ray_orientations = [False, False, False, False, False, False, False, False]
        self.strip_len = display_length
        self.ray_length = display_length

        self.spi_rate = 16 #MHz
        self.real_num_pixels = display_length + start_shift

        self.pixels_per_channel = int(self.real_num_pixels / self.num_channels)
        # self.pixels_per_channel = self.num_rays / self.num_channels * self.ray_length

        self.all_update_interval = 1/50

        self.sensor_update_time = time.time()
        self.sensor_update_interval = self.all_update_interval
        self.display_update_time = time.time()
        self.display_update_interval = self.all_update_interval

        self.idle_timeout = 3.0 # seconds
        self.last_pad_change_time = time.time()
        self.idle_mode = False

        self.full_arc_time = 0.3

        self.rayset = None
        self.padset = None
        self.active_programs = []

        self.threaded_strip_update = True
        self.render_multithreaded = False
        self.render_workers_per_ray = 2
        self.global_sync_time = 0

        self.debug_mode = False
        self.simPixel_mode = False

    def main(self):

        fps_update_time = time.time()
        fps_time_interval = 5

        frame_count = 0
        fps_framecount_last = -1

        while True:
            updated = False

            # logger.debug('idle mode: %s', self.idle_mode)

            if time.time() >= self.sensor_update_time:
                self.padset.update()
                self.sensor_update_time += self.sensor_update_interval
                updated = True

            for prog in self.active_programs:
                if prog.next_update_time < time.time():
                    prog.update()
                    updated = True

            if time.time() >= self.display_update_time:
                self.rayset.render()
                if not self.debug_mode:
                    self.rayset.write_to_strip()
                # strip.show()
                self.display_update_time += self.display_update_interval
                updated = True

            if time.time() - fps_update_time > fps_time_interval and frame_count > 1 and frame_count != fps_framecount_last:
                logger.info('frame %s, fps %s ', frame_count, round((frame_count - fps_framecount_last)/(time.time() - fps_update_time), 2))
                fps_update_time = time.time()
                fps_framecount_last = frame_count

                # print updated_time

            if updated:
                frame_count += 1

            # time.sleep(10)


