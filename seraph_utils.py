def clamp_color(rgb):
    return map(rgb, clamp_value)

def clamp_value(val):
    if val < 0:
        return 0
    if val > 1.0:
        return 0.999
    return val

def sine(x):
    # compute sine
    x %= 6.28318531
    if x > 3.14159265:
        x -= 6.28318531
    if x < 0:
        return 1.27323954 * x + .405284735 * x * x
    else:
        return 1.27323954 * x - 0.405284735 * x * x


# print sine_table

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