'''
Make sure to disable animations in the options!
'''
import sark.qt
from PIL import Image, ImageChops
import idaapi
from cStringIO import StringIO

HEIGHT_MARGIN = 10

WIDTH_MARGIN = 10

MAX_ITERATIONS = 30
MAX_WIDTH = 10000
MAX_HEIGHT = 10000

HEIGHT_INCREMENT = 100

WIDTH_INCREMENT = 100


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

    # Both the maximum iteration count and the max width and height are
    # used as safeties. You can change their values as needed.
    graph_image = None
    for _ in xrange(MAX_ITERATIONS):
        if height >= MAX_HEIGHT or width >= MAX_WIDTH:
            break

        sark.qt.resize_widget(widget, width, height)

        center_graph()

        image = grab_image(widget)

        try:
            trimmed, (left, upper, right, lower) = trim(image)
        except TypeError:
            width += WIDTH_INCREMENT
            height += HEIGHT_INCREMENT
            continue

        print width, height
        print image.width, image.height
        print trimmed.width, trimmed.height
        print left, upper, right, lower

        resize = False
        if left == 0 or right == image.width:
            print 'w'
            width += WIDTH_INCREMENT
            resize = True
        elif trimmed is not None:  # speedup
            width = trimmed.width + WIDTH_MARGIN

        if upper == 0 or lower == image.height:
            print 'h'
            height += HEIGHT_INCREMENT
            resize = True
        elif trimmed is not None:  # speedup
            height = trimmed.height + HEIGHT_MARGIN

        graph_image = trimmed

        if not resize:
            break

    return graph_image


def grab_image(widget):
    image_data = sark.qt.capture_widget(widget)
    image = Image.open(StringIO(image_data))
    return image


def show(w):
    image_data = sark.qt.capture_widget(w)
    image = Image.open(StringIO(image_data))
    image.show()


def capture_graph():
    path = idaapi.askfile_c(1, 'graph.png', 'Save Graph...')
    if not path:
        return

    image = grab_graph()
    try:
        image.save(path, format='PNG')
    except:
        import traceback
        traceback.print_exc()


class GraphGrabber(idaapi.plugin_t):
    flags = idaapi.PLUGIN_PROC
    comment = 'GraphGrabber'
    help = 'Automatically grab full-res images of graphs'
    wanted_name = 'GraphGrabber'
    wanted_hotkey = 'Ctrl+Alt+G'

    def init(self):
        return idaapi.PLUGIN_KEEP

    def run(self, arg):
        capture_graph()

    def term(self):
        pass


def PLUGIN_ENTRY():
    return GraphGrabber()


def is_script_file():
    import traceback
    stack = traceback.extract_stack()
    print stack
    (filename, line_number, function_name, text) = stack[0]
    return function_name == 'IDAPython_ExecScript'


if __name__ == '__main__':
    if is_script_file():
        capture_graph()
