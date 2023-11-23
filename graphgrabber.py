import sark.qt
from PIL import Image, ImageChops
import idaapi
from io import BytesIO

# Those are a bit of voodoo.
# When a trimming an axis from both ends, the size on that axis is set to the
# trimmed size to speed up the capture. The margins are added because
# it sometimes fails without them.
HEIGHT_MARGIN = 10
WIDTH_MARGIN = 10

# Those 3 are safety values to keep IDA from freezing indefinitely.
# Feel free to change if needed (results are trimmed).
MAX_ITERATIONS = 30
MAX_WIDTH = 100000
MAX_HEIGHT = 100000

# Used to increment the size when needed. Higher values may speed up capture.
HEIGHT_INCREMENT = 1000
WIDTH_INCREMENT = 1000


def trim(im, bg=None):
    if bg is None:
        bg = get_bg(im)
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox(alpha_only=False)
    if bbox:
        return im.crop(bbox), bbox


def get_bg(im):
    return Image.new(im.mode, im.size, im.getpixel((0, 0)))


def center_graph(widget):
    widget.setFocus()
    graph_zoom_fit()
    graph_zoom_100()


def graph_zoom_100():
    if not idaapi.process_ui_action("GraphZoom100"):
        raise RuntimeError("Failed to zoom 100%")


def graph_zoom_fit():
    if not idaapi.process_ui_action("GraphZoomFit"):
        raise RuntimeError("Failed to zoom to fit")


def get_ida_graph_widget(idaview_name="IDA View-A"):
    widget = sark.qt.get_widget(idaview_name).children()[0]
    try:
        # IDA < 7.0
        widget = widget.children()[0]
    except IndexError:
        pass

    return widget


def grab_graph():
    widget = get_ida_graph_widget()

    width = widget.width()
    height = widget.height()

    graph_image = None

    for iteration in range(MAX_ITERATIONS):
        if height >= MAX_HEIGHT or width >= MAX_WIDTH:
            break

        print(f"Iteration: {iteration}")

        sark.qt.resize_widget(widget, width, height)
        center_graph(widget)

        image = grab_image(widget)

        try:
            trimmed, (left, upper, right, lower) = trim(image)
        except TypeError as e:
            print(e)
            width += WIDTH_INCREMENT
            height += HEIGHT_INCREMENT
            continue

        print("Desired:", width, height)
        print("Image:", image.width, image.height)
        print("Trimmed:", trimmed.width, trimmed.height)
        print("Bounds:", left, upper, right, lower)

        resize = False
        if left == 0 or right == image.width:
            print("Increase width")
            width += WIDTH_INCREMENT
            resize = True

        else:  # speedup
            width = trimmed.width + WIDTH_MARGIN

        if upper == 0 or lower == image.height:
            print("Increase height")
            height += HEIGHT_INCREMENT
            resize = True

        else:  # speedup
            height = trimmed.height + HEIGHT_MARGIN

        graph_image = trimmed

        if not resize:
            break

    return graph_image


def grab_image(widget):
    image_data = sark.qt.capture_widget(widget)
    image = Image.open(BytesIO(image_data))
    return image


def show(w):
    image_data = sark.qt.capture_widget(w)
    image = Image.open(BytesIO(image_data))
    image.show()


def capture_graph(path=None):
    if not path:
        path = idaapi.ask_file(1, "graph.png", "Save Graph...")
    if not path:
        return

    image = grab_graph()
    try:
        image.save(path, format="PNG")
    except:
        import traceback

        traceback.print_exc()


class GraphGrabber(idaapi.plugin_t):
    flags = idaapi.PLUGIN_PROC
    comment = "GraphGrabber"
    help = "Automatically grab full-res images of graphs"
    wanted_name = "GraphGrabber"
    wanted_hotkey = "Ctrl+Alt+G"

    def init(self):
        return idaapi.PLUGIN_KEEP

    def run(self, arg):
        capture_graph()

    def term(self):
        pass


def PLUGIN_ENTRY():
    return GraphGrabber()


def is_script_file():
    """Check if executing as plugin or script.

    Only works with Sark's plugin loader.
    :return: bool
    """
    # TODO: Make it work regardless of Sark's plugin loader.
    import traceback

    stack = traceback.extract_stack()
    _filename, _line_number, function_name, _text = stack[0]
    return function_name == "IDAPython_ExecScript"


if __name__ == "__main__":
    if is_script_file():
        capture_graph()
