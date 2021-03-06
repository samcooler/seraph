import RPi.GPIO as GPIO
import time
from seraph_utils import circular_mean
from collections import deque

import logging
logger = logging.getLogger(__name__)

class PadSet:
    def __init__(self, dancer, pins, set):
        logger.info('starting padset pins: %s set: %s', pins, set)
        self.dancer = dancer
        self.pins = pins
        self.num_pins = len(pins)
        self.pads = [Pad(dancer, pins[i], i, set) for i in range(self.num_pins)]
        self.val_current = [0] * self.num_pins

        self.latch_timeouts = [-1] * self.num_pins
        self.val_filtered = [0] * self.num_pins
        self.latch_duration = 0.5

        self.mean_hand_position = 0

        # self.filter_length = 5
        # self.val_history = [False] * self.num_pins # [deque([False] * self.num_pins, self.filter_length) for i in range(self.num_pins)]
        # self.filter_weights = [0.2, 0.4, 0.6, 0.8, 1.0]
        # self.filter_sum = sum(self.filter_weights)

    def get_value_filtered(self):
        return list(self.val_filtered)

    def get_value_current(self):
        return list(self.val_current)

    def get_mean_hand_position(self):
        return self.mean_hand_position

    def update(self):
        # pass
        for pi in range(self.num_pins):
            self.pads[pi].update_value()
            val = self.pads[pi].value

            val_filtered = val

            # latch up
            if val:
                self.latch_timeouts[pi] = time.time() + self.latch_duration

            # 0 latched to 1
            else:
                if self.latch_timeouts[pi] > 0 and time.time() < self.latch_timeouts[pi]:
                    val_filtered = 1
                else:
                    self.latch_timeouts[pi] = -1


            self.val_current[pi] = val
            self.val_filtered[pi] = val_filtered

        # generate mean hand position once
        hand_positions = [pos / len(self.val_filtered) + self.dancer.pad_sensor_offset for pos in
                          range(len(self.val_filtered)) if self.val_filtered[pos]]
        self.mean_hand_position = circular_mean(hand_positions)

class Pad:
    def __init__(self, dancer, pin_, position_, set):
        self.dancer = dancer
        self.pin = pin_
        self.position = position_
        self.pin = pin_
        self.value = 0 # can be changed by sensor read or the ghost
        # self.sensor_value = 0
        # self.previous_sensor_value = 0
        if set:
            self.setup(pin_)

        logger.info('Pad %s starting on input pin %s', self.position, self.pin)

    def update_value(self):
        # if not self.dancer.debug_mode:
        val = 1 if GPIO.input(self.pin) == 0 else 0
            # logger.debug('pad %s read value %s', self.position, val)
        # else:
        #     val = 1

        self.value = val

        # return self.value

        # have changed since last sensor read
        # if val != self.sensor_value:
        #     self.dancer.last_pad_change_time = time.time()
        #     self.dancer.idle_mode = False

        # active mode, use the sensor value
        # if not self.dancer.idle_mode:
        #     # if val == self.previous_sensor_value:

    def setup(self, pin):
        GPIO.setup(pin, GPIO.IN, pull_up_down=(GPIO.PUD_UP if self.dancer.pad_mode_buttons else GPIO.PUD_OFF))
