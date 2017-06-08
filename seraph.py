#!/usr/bin/python

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

from seraph_dancer import Dancer

print("Starting")

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

    dancer = Dancer()
    dancer.setup()
    dancer.main()

    # GPIO.cleanup()



