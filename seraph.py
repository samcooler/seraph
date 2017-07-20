#!/usr/bin/python

import RPi.GPIO as GPIO
import time, sys

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

hdlr = logging.FileHandler('/home/pi/seraph/seraph_log.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

logger.info('')
logger.info('Starting Seraph')

from seraph_dancer import Dancer

# mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
# mixer.init()
# sound_good = mixer.Sound('high_tap.wav')
# sound_good.set_volume(0.5)
# sound_norm = mixer.Sound('low_tap.wav')
# sound_norm.set_volume(0.5)
#
# sound_norm.play()
# sound_good.play()


# Shader
# vibrate: 'k', multiply(), sine_wave()
# full_color: 'h', replace, single


if __name__ == "__main__":
    while True:
        error = False
        try:
            dancer = Dancer()
        except:
            logger.error('Dancer instantiation failed %s', sys.exc_info()[0])
            error = True

        try:
            dancer.setup()
        except:
            logger.error('Dancer setup failed %s', sys.exc_info()[0])
            error = True

        # try:
        dancer.main()
        # except:
        #     logger.error('Dancer main run failed %s', sys.exc_info()[0])
        #     error = True

        if error:
            logger.info('Waiting 10 seconds and restarting')
            time.sleep(10)

