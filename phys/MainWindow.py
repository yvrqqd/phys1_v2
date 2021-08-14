import cv2
import time
import threading
import gi
import configparser
import numpy as np

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
from phys import CustomHeaderbar

mutex = threading.Lock()
dimg = GdkPixbuf.Pixbuf.new_from_file("start.png")
dimg2 = GdkPixbuf.Pixbuf.new_from_file("start.png")


class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__()
        header_bar = CustomHeaderbar.CustomHeaderBar(self)
        self.set_titlebar(header_bar)
        self.set_default_size(1440, 600)
        grid = Gtk.Grid()
        self.add(grid)
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect('draw', self.on_drawing_area_draw)
        self.drawing_area.set_size_request(720, 576)
        grid.attach(self.drawing_area, 0, 0, 1, 1)

        self.drawing_area2 = Gtk.DrawingArea()
        self.drawing_area2.connect('draw', self.on_drawing_area2_draw)
        self.drawing_area2.set_size_request(720, 576)

        grid.attach(self.drawing_area2, 1, 0, 1, 1)

    def open_video_opencv(self):
        global dimg, dimg2

        def readconfig():
            config = configparser.ConfigParser()
            config.read("settings.ini")
            return config["video_file"]["video_file_name"]

        def read_settings():
            config = configparser.ConfigParser()
            config.read("settings.ini")
            x, y = [int(i) for i in config["area_coordinates"]["coordinates"][1:-1].split(',')]
            return x, y, x + 512, y + 512

        LEFT_TOP_CORNER_X, LEFT_TOP_CORNER_Y, RIGHT_DOWN_CORNER_X, RIGHT_DOWN_CORNER_Y = read_settings()
        filename = readconfig()

        mask = []
        with open("mask", "rb") as file:
            counter = 0
            while counter < 512 * 64:
                byte = file.read(1)
                mask.append(np.uint8(ord(byte)))
                counter += 1
            mask = np.unpackbits(np.array(mask), axis=0).reshape(512, 512)

        img1 = GdkPixbuf.Pixbuf.new_from_file("start.png")
        cap = cv2.VideoCapture(filename)
        time_per_frame = 1 / int(cap.get(cv2.CAP_PROP_FPS))
        width = cap.get(3)  # float `width`
        height = cap.get(4)  # float `height`
        self.drawing_area.set_size_request(width, height)
        self.drawing_area2.set_size_request(width, height)
        ret, img = cap.read()
        previous = img[LEFT_TOP_CORNER_Y:RIGHT_DOWN_CORNER_Y, LEFT_TOP_CORNER_X:RIGHT_DOWN_CORNER_X]

        previous = cv2.bitwise_and(previous, previous, mask=mask)
        previous = GdkPixbuf.Pixbuf.new_from_data(
            previous.tostring(),
            GdkPixbuf.Colorspace.RGB, False, 8,
            previous.shape[1],
            previous.shape[0],
            previous.shape[2] * previous.shape[1], None, None
        )

        dimg1 = previous
        dimg2 = previous
        self.drawing_area2.queue_draw()
        self.drawing_area.queue_draw()
        time.sleep(100)
        previous = cv2.GaussianBlur(previous, (17, 13), 0)

        h_bins = 512
        s_bins = 0
        histSize = [h_bins]
        h_ranges = [0, 180]
        s_ranges = [0, 256]
        ranges = h_ranges
        channels = [0]
        m1, m2, m3, m4 = [], [], [], []
        t = 1
        pr2 = previous
        time.sleep(100)
        while cap.isOpened():

            ret, img = cap.read()
            if img is not None:
                # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                # print(base_base)
                t += 1
                mutex.acquire()
                img = img[
                      LEFT_TOP_CORNER_Y:RIGHT_DOWN_CORNER_Y,
                      LEFT_TOP_CORNER_X:RIGHT_DOWN_CORNER_X
                      ]
                # t1 = time.time()
                # t2 = time.time()
                # img = cv2.blur(img,(5,5))
                #
                # img = cv2.GaussianBlur(img, (11, 11), 0)
                tmp = img
                img = cv2.absdiff(img, previous)
                # ret1, img = cv2.threshold(img, 10, 255, cv2.THRESH_BINARY)

                dimg2 = GdkPixbuf.Pixbuf.new_from_data(
                    img.tobytes(),
                    GdkPixbuf.Colorspace.RGB, False, 8,
                    img.shape[1],
                    img.shape[0],
                    img.shape[2] * img.shape[1], None, None
                )

                self.drawing_area2.queue_draw()

                # print(t2-t1)
                hist_prev = cv2.calcHist([pr2], channels, None, histSize, ranges, accumulate=False)
                # cv2.normalize(hist_prev, hist_prev, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
                #
                hist_curr = cv2.calcHist([img], channels, None, histSize, ranges, accumulate=False)
                # cv2.normalize(hist_curr, hist_curr, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
                #
                #

                # # start = time.time()
                # base_base = cv2.compareHist(hist_curr, hist_prev, 0)
                # m1.append(base_base)
                # # end = time.time()
                # # print("1", end-start)
                # # start = time.time()
                # base_base = cv2.compareHist(hist_curr, hist_prev, 1)
                # m2.append(base_base)
                # # end = time.time()
                # # print("2", end - start)
                # # start = time.time()
                base_base = cv2.compareHist(hist_curr, hist_prev, 2)
                m1.append(base_base)
                # m3.append(base_base)
                # # end = time.time()
                # # print("3", end - start)
                # # start = time.time()
                # base_base = cv2.compareHist(hist_curr, hist_prev, 3)
                # m4.append(base_base)
                # end = time.time()/
                # print("4", end - start)

                # base_base = cv2.compareHist(hist_curr, hist_prev, 3)
                # if base_base > 0.05:
                #     print(t)
                #     # self.drawing_area2.queue_draw()
                #     # cv2.imwrite('work_ex/' + str(t) + '.jpg', tmp)
                # else:
                #     pass

                previous = tmp

                # dimg = GdkPixbuf.Pixbuf.new_from_data(img.tobytes(),
                #                                       GdkPixbuf.Colorspace.RGB, False, 8,
                #                                       img.shape[1],
                #                                       img.shape[0],
                #                                       img.shape[2] * img.shape[1], None, None)
                # if base_base > 0.05:
                #     self.drawing_area2.queue_draw()

                dimg = GdkPixbuf.Pixbuf.new_from_data(
                    tmp.tobytes(),
                    GdkPixbuf.Colorspace.RGB, False, 8,
                    tmp.shape[1],
                    tmp.shape[0],
                    tmp.shape[2] * tmp.shape[1], None, None
                )

                self.drawing_area.queue_draw()

                mutex.release()
                time.sleep(time_per_frame / 100)
            else:
                break
        print(m1)
        # print(m2)
        # print(m3)
        # print(m4)

    def video_open(self, *_):
        thread = threading.Thread(target=self.open_video_opencv)
        thread.daemon = False
        thread.start()

    def on_drawing_area_draw(self, widget, cr):
        global dimg
        mutex.acquire()
        Gdk.cairo_set_source_pixbuf(cr, dimg, 0, 0)
        cr.paint()
        mutex.release()

    def on_drawing_area2_draw(self, widget, cr):
        global dimg2
        mutex.acquire()
        Gdk.cairo_set_source_pixbuf(cr, dimg2, 0, 0)
        cr.paint()
        mutex.release()
