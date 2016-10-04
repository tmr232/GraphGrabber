'''
Make sure to disable animations in the options!
'''
import sark.qt
from PIL import Image, ImageChops
import idaapi
from cStringIO import StringIO


def trim(im, bg=None):
    if bg is None:
        bg = get_bg(im)
    diff = ImageChops.difference(im, bg)
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

    return trimmed


def grab_image(widget):
    image_data = sark.qt.capture_widget(widget)
    image = Image.open(StringIO(image_data))
    return image


def show(w):
    image_data = sark.qt.capture_widget(w)
    image = Image.open(StringIO(image_data))
    image.show()


class GraphGrabber(idaapi.plugin_t):
    flags = idaapi.PLUGIN_PROC
    comment = 'GraphGrabber'
    help = 'Automatically grab full-res images of graphs'
    wanted_name = 'GraphGrabber'
    wanted_hotkey = 'Ctrl+Alt+G'

    def init(self):
        pass

    def run(self, arg):
        path = idaapi.askfile_c(1, 'graph.png', 'Save Graph...')
        if not path:
            return

        image = grab_graph()
        try:
            image.save(path, format='PNG')
        except:
            import traceback
            traceback.print_exc()

    def term(self):
        pass
