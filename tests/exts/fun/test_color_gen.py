import colorsys


def test_color_gen():
    """
    Generates the colors for the blocks
    """
    n = 81
    for i in range(n):
        hue = i / n
        r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 1.0)
        #print((int(r*255), int(g*255), int(b*255)), end="")
        #print(",")
