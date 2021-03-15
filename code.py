import os
import time
from multiprocessing import Pool

import pygame
import numpy as np

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

# Window
WIDTH, HEIGHT = 400, 400

# Zoom
ZOOM = 0.3
ZOOM_FACTOR = 2.0  # NOTE: don't change quite buggy, too lazy to fix
ZOOM_IN_MAX = 1.0e-18  # starts taxing the CPU
ZOOM_OUT_MAX = 0.2  # too small to see otherwise

# X -
X_AXIS = 1 / ZOOM
X_CAM = -0.5
X_OFFSET = (-X_AXIS / 2) + X_CAM

# Y -
Y_AXIS = HEIGHT / (WIDTH * ZOOM)
Y_CAM = 0
Y_OFFSET = (-Y_AXIS / 2) - Y_CAM

# Iterations
ITERATIONS = 100
ITERATIONS_FACTOR = 1.4
ITERATIONS_MAX = 1000
ITERATIONS_MIN = 5

# Ratio
RATIO = X_AXIS / WIDTH


def mandelbrot_XY(x, y, ratio, x_offset, y_offset, iterations):
    """
    calculate the RGB value for the pixel at some (x, y) coordinate
    """
    a = ca = (x * ratio) + x_offset
    b = cb = (y * ratio) + y_offset
    n = 0
    # change lim condition to a * a + b * b < 4 for normal effect
    while a + b < 40 and n < iterations:
        ai = a * a - b * b
        bi = 2 * a * b
        a = ai + ca
        b = bi + cb
        n += 1

    m = n / iterations
    # m = np.sqrt(m)
    lin = int(255 * m) % 255
    sin = int(255 * (-np.cos(np.pi * m) + 1) / 2) % 255
    # sqrt = int(255 * np.sqrt(m)) % 255
    sqr = int(255 * (m * m)) % 255
    # return pixel rgb value
    pixel = (sqr, lin, sin)
    return pixel


def control(mouse, button):
    """
    Changes display properties based on the mouse event. Returns a boolean
    value indicating if the screen should be redrawn.
    """
    # ignore events we don't care about
    if button not in (1, 3, 4, 5):
        return False

    global X_OFFSET, Y_OFFSET, RATIO, ITERATIONS
    x_pos, y_pos = mouse

    # click: zoom-in/out
    if button in (1, 3):
        old = new = RATIO

        if button == 1:  # left click - zoom in
            new = max(ZOOM_IN_MAX, RATIO / ZOOM_FACTOR)
            if new == old:
                return False
            X_OFFSET += x_pos * new
            Y_OFFSET += y_pos * new

        if button == 3:  # right click - zoom out
            new = min(ZOOM_OUT_MAX, RATIO * ZOOM_FACTOR)
            if new == old:
                return False
            X_OFFSET -= x_pos * old
            Y_OFFSET -= y_pos * old

        RATIO = new
        print("RATIO:", old, "->", RATIO )
        return True

    # scroll: iterations-inc/dec
    elif button in (4, 5):
        old = new = ITERATIONS

        if button == 4:  # scroll-up - increase iterations
            new = min(ITERATIONS_MAX, int(ITERATIONS * ITERATIONS_FACTOR))

        if button == 5:  # scroll-down - decrease iterations
            new = max(ITERATIONS_MIN, int(ITERATIONS / ITERATIONS_FACTOR))

        if new != old:
            ITERATIONS = new
            print("ITERATIONS:", old, "->", ITERATIONS)
            return True

    return False


def draw(screen, pool):
    t0 = time.perf_counter()

    pixels = pool.starmap(mandelbrot_XY, [
        (x, y, RATIO, X_OFFSET, Y_OFFSET, ITERATIONS)
        for y in range(HEIGHT)
        for x in range(WIDTH)
    ])

    # array = np.asarray(pixels)
    # reshaped_array = array.reshape(WIDTH, HEIGHT, 3)
    # pygame.surfarray.blit_array(screen, reshaped_array)

    for x in range(HEIGHT):
        for y in range(WIDTH):
            screen.set_at((x, y), pixels[y * HEIGHT + x])

    pygame.display.flip()

    print("draw-perf:", time.perf_counter() - t0)


def main(pool):
    # init the screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # first draw
    draw(screen, pool)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONUP:
                # redraw if needed
                if control(pygame.mouse.get_pos(), event.button):
                    draw(screen, pool)
                    pygame.display.flip()


if __name__ == "__main__":
    pool = Pool()  # multiprocessing Pool

    try:
        main(pool)
    finally:
        pool.close()
