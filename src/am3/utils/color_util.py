R = "\033[0;31;40m"  # RED
G = "\033[0;32;40m"  # GREEN
Y = "\033[0;33;40m"  # Yellow
B = "\033[0;34;40m"  # Blue
C1 = "\033[1;36;40m"  # Bright Cyan
N = "\033[0m"  # Reset


def red(s):
    return R + s + N


def green(s):
    return G + s + N


def blue(s):
    return B + s + N


def yellow(s):
    return Y + s + N


def bright_cyan(s):
    return C1 + s + N


def bool_color(b):
    if b:
        return G + str(b) + N
    return R + str(b) + N
