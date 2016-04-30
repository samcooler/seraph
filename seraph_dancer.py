
import time
from seraph_program import Program
from seraph_rayset import RaySet
from seraph_pad import PadSet

class Dancer:
    def __init__(self):
        self.rayset = None
        self.num_rays = 1
        self.num_channels = 1
        self.channel_pins = [17, 5]
        self.ray_offsets = [0*self.num_rays]
        # self.channel_rays = [list(range(self.num_rays/2)),
        #                      [self.num_rays/2 + r for r in range(self.num_rays/2)]]
        self.channel_rays = [list(range(self.num_rays))]
        self.pads_pins = [14, 15, 18, 23, 24, 25]
        self.strip_brightness = 0.1
        # self.ray_orientations = [False, False, False, False, False, False, False, False]
        self.strip_len = 300
        self.ray_length = 300

        self.spi_rate = 1 * 1000000
        self.real_num_pixels = 300

        self.pixels_per_channel = self.real_num_pixels / self.num_channels
        # self.pixels_per_channel = self.num_rays / self.num_channels * self.ray_length

        self.all_update_interval = 1/20

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

        self.render_multithreaded = True
        self.render_workers_per_ray = 2
        self.global_sync_time = 0

        self.debug_mode = False

    def main(self):

        print "cell 1 go"
        updated_time = time.time()
        frame_count = 0

        while True:
            updated = False

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

            if frame_count % 30 == 0:
                print 'fps', round(1/((time.time() - updated_time) / 30), 2)
                updated_time = time.time()
                # print updated_time

            if updated:
                frame_count += 1

            # time.sleep(0.5)

    def setup(self):
        self.padset = PadSet(self, self.pads_pins, not self.debug_mode)

        self.rayset = RaySet(self)
        self.rayset.full_brightness(self.strip_brightness)

        # global active_programs
        # self.active_programs.append(Program(self,'ghost'))
        # self.active_programs.append(Program(self,'slow_changes'))
        # self.active_programs.append(Program(self,'handglow'))
        # self.active_programs.append(Program(self,'peacock'))
        # self.active_programs.append(Program(self,'handsense'))
        self.active_programs.append(Program(self,'ring'))
        # self.active_programs.append(Program(self,'monochrome'))
        # self.active_programs.append(Program(self, 'chase'))
        # self.active_programs.append(Program(self, 'starry'))


        # self.active_programs.append(Program(self,'checkers'))