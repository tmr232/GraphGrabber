'''
Make sure to disable animations in the options!
'''


from time import sleep

import sark.qt
from PIL import Image, ImageChops
import idaapi
from cStringIO import StringIO


def trim(im, bg=None):
    if bg is None:
        bg = get_bg(im)
    diff = ImageChops.difference(im, bg)
    # diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox), bbox


def get_bg(im):
    return Image.new(im.mode, im.size, im.getpixel((0, 0)))


def center_graph():
    graph_zoom_fit()
    graph_zoom_100()


def graph_zoom_100():
    idaapi.process_ui_action('GraphZoom100')


def graph_zoom_fit():
    idaapi.process_ui_action('GraphZoomFit')


def grab_graph():
    widget = sark.qt.get_widget('IDA View-A').children()[0].children()[0]
    width = widget.width()
    height = widget.height()

    for x in range(30):
        # The extra pixels are to make sure we use the background for trimming
        # and not the node borders.
        sark.qt.resize_widget(widget, width, height)

        center_graph()

        image = grab_image(widget)

        try:
            trimmed, (left, upper, right, lower) = trim(image)
        except:
            trimmed, (left, upper, right, lower) = None, (None, None, None, None)

        print width, height
        print image.width, image.height
        print trimmed.width, trimmed.height
        resize = False
        # if width == trimmed.width:
        if left == 0 or right == image.width:
            print 'w'
            width += 100
            resize = True
        elif trimmed is not None:  # speedup
            width = trimmed.width + 10

        # if height == trimmed.height:
        if upper == 0 or lower == image.height:
            print 'h'
            height += 100
            resize = True
        elif trimmed is not None:  # speedup
            width = trimmed.height + 10

        if not resize:
            break

    trimmed.show()


def grab_image(widget):
    image_data = sark.qt.capture_widget(widget)
    image = Image.open(StringIO(image_data))
    return image


def fit_graph(): # Does not work!
    widget = sark.qt.get_widget('IDA View-A').children()[0].children()[0]

    for x in range(5):
        print x
        print widget.width(), widget.height()
        graph_zoom_fit()
        i_fit = sark.qt.capture_widget(widget)
        graph_zoom_100()
        i_100 = sark.qt.capture_widget(widget)

        if i_fit == i_100:
            break

        sark.qt.resize_widget(widget, widget.width() + 100, widget.height() + 100)

    image_data = sark.qt.capture_widget(widget)
    image = Image.open(StringIO(image_data))

    trimmed, x = trim(image)
    trimmed.show()


def show(w):
    image_data = sark.qt.capture_widget(w)
    image = Image.open(StringIO(image_data))
    image.show()
