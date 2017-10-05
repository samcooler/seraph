import random, math

def clamp_color(rgb):
    return map(rgb, clamp_value)

def clamp_value(val):
    if val < 0:
        return 0
    if val > 1.0:
        return 0.999
    return val


def clamp_circular(val):
    return val % 1.0


def sine(x):
    # compute sine
    x %= 6.28318531
    if x > 3.14159265:
        x -= 6.28318531
    if x < 0:
        return 1.27323954 * x + .405284735 * x * x
    else:
        return 1.27323954 * x - 0.405284735 * x * x


def circular_mean(angles):
    if len(angles) == 0:
        return 0
    elif len(angles) == 1:
        return angles[0]
    else:
				    angles_radians = [(p % 1.0) * math.pi * 2 for p in angles]
				    vectors = [[math.cos(a), math.sin(a)] for a in angles_radians]
				    vectors_t = list(zip(*vectors))
				    #print(vectors_t)
				    angle = math.atan2(sum(vectors_t[1]), sum(vectors_t[0]))
				    return (angle / (2 * math.pi)) % 1


def generate_distributed_values(l, thresh):
    too_close = [1, 1]
    values = []
    while any(too_close):
        values = [random.random() for i in range(l)]
        diffs = [values[(i + 1) % l] - values[i] for i in range(l)]
        too_close = [abs(b) < thresh for b in diffs]
    return values


def sine_phase(x):
    # compute sine
    # print x, int((x % 1.0) * sine_range), sine_table[int((x % 1.0) * sine_range)]
    return sine_table[int((x % 1.0) * sine_range)]
    # return 4 * abs(x % 1.0 - 0.5) - 1 # actually slow
    # x %= 1.0
    # if x > 0.5:
    #     x -= 1.0
    #     return 8 * x + 16 * x * x
    #
    # else:
    #     return 8 * x - 16 * x * x


def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    elif x == 0:
        return 0
    else:
        return x