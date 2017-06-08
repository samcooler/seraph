import RPi.GPIO as GPIO
import time
from collections import deque

class PadSet:
    def __init__(self, dancer, pins, set):
        self.dancer = dancer
        self.pins = pins
        self.pads = [Pad(dancer, pins[i], i, set) for i in range(dancer.num_rays)]
        self.val_current = [False] * dancer.num_rays

        self.val_filtered = [False] * dancer.num_rays
        self.filter_length = 5
        self.val_history = [deque([False] * dancer.num_rays, self.filter_length) for i in range(dancer.num_rays)]
        self.filter_weights = [0.2, 0.4, 0.6, 0.8, 1.0]
        self.filter_sum = sum(self.filter_weights)

    def update(self):
        pass
        # for pi in range(self.dancer.num_rays):
        #     val = self.pads[pi].value
        #     self.val_current[pi] = val
        #     self.val_history[pi].append(val)
        #     s = sum([self.filter_weights[hi] * self.val_history[pi][hi] for hi in range(self.filter_length)])
        #     self.val_filtered[pi] = bool(s / self.filter_sum)

        # print self.val_current, self.val_filtered



class Pad:
    def __init__(self, dancer, pin_, position_, set):
        self.dancer = dancer
        self.pin = pin_
        self.position = position_
        self.pin = pin_
        self.value = False # can be changed by sensor read or the ghost
        self.sensor_value = False
        self.previous_sensor_value = False
        if set:
            self.setup(pin_)


    def update_value(self):
        if not self.dancer.debug_mode:
            val = GPIO.input(self.pin) == 1
        else:
            val = True

        # have changed since last sensor read
        if val != self.sensor_value:
            self.dancer.last_pad_change_time = time.time()
            self.dancer.idle_mode = False

        # active mode, use the sensor value
        if not self.dancer.idle_mode:
            # if val == self.previous_sensor_value:
            self.value = val
                # self.sensor_value = val
            # else:
            #     self.previous_sensor_value = val

        # if self.sensor_value:
        #     print 'sensor on',self.position

        return self.value

    def setup(self, pin):
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
