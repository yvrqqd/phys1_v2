import cv2
import time
import threading
import gi
import configparser
import numpy as np

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf, Gio
from phys import CustomHeaderbar, InfoWindow, SettingsWindow

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
        global dimg, dimg_available, dimg2

        LEFT_TOP_CORNER_X = 104
        LEFT_TOP_CORNER_Y = 60
        RIGHT_DOWN_CORNER_X = 636
        RIGHT_DOWN_CORNER_Y = 572

        config = configparser.ConfigParser()
        config.read("settings.ini")

        img1 = GdkPixbuf.Pixbuf.new_from_file("start.png")

        self.filename = config["video_file"]["video_file_name"]
        cap = cv2.VideoCapture(self.filename)

        time_per_frame = 1 / int(cap.get(cv2.CAP_PROP_FPS))
        width = cap.get(3)  # float `width`
        height = cap.get(4)  # float `height`
        self.drawing_area.set_size_request(width, height)
        self.drawing_area2.set_size_request(width, height)
        ret, img = cap.read()
        # previous = cv2.imread("start.png")
        previous = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)[LEFT_TOP_CORNER_X:RIGHT_DOWN_CORNER_Y,
                   LEFT_TOP_CORNER_X:RIGHT_DOWN_CORNER_X]
        previous = cv2.GaussianBlur(previous, (17, 13), 0)
        h_bins = 50
        s_bins = 60
        histSize = [h_bins, s_bins]
        # hue varies from 0 to 179, saturation from 0 to 255
        h_ranges = [0, 180]
        s_ranges = [0, 256]
        ranges = h_ranges + s_ranges  # concat lists
        # Use the 0-th and 1-st channels
        channels = [0, 1]
        m1, m2, m3, m4 = [], [], [], []
        t = 1
        pr2 = previous
        kernel = np.ones((5, 5), np.float32) / 25
        while cap.isOpened():

            ret, img = cap.read()
            if img is not None:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                # print(base_base)
                t += 1
                mutex.acquire()

                img = img[LEFT_TOP_CORNER_X:RIGHT_DOWN_CORNER_Y, LEFT_TOP_CORNER_X:RIGHT_DOWN_CORNER_X]
                # t1 = time.time()
                # t2 = time.time()
                # img = cv2.blur(img,(5,5))
                #
                img = cv2.GaussianBlur(img, (11, 11),0)
                tmp = img
                img = cv2.absdiff(img, previous)
                ret1, img = cv2.threshold(img, 10, 255, cv2.THRESH_BINARY)

                dimg2 = GdkPixbuf.Pixbuf.new_from_data(img.tobytes(),
                                                       GdkPixbuf.Colorspace.RGB, False, 8,
                                                       img.shape[1],
                                                       img.shape[0],
                                                       img.shape[2] * img.shape[1], None, None)
                self.drawing_area2.queue_draw()

                # print(t2-t1)
                # hist_prev = cv2.calcHist([pr2], channels, None, histSize, ranges, accumulate=False)
                # cv2.normalize(hist_prev, hist_prev, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
                #
                # hist_curr = cv2.calcHist([img], channels, None, histSize, ranges, accumulate=False)
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
                # base_base = cv2.compareHist(hist_curr, hist_prev, 2)
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

                dimg = GdkPixbuf.Pixbuf.new_from_data(tmp.tobytes(),
                                                      GdkPixbuf.Colorspace.RGB, False, 8,
                                                      tmp.shape[1],
                                                      tmp.shape[0],
                                                      tmp.shape[2] * tmp.shape[1], None, None)
                self.drawing_area.queue_draw()
                mutex.release()

                time.sleep(time_per_frame)
            else:
                break
        # print(m1)
        # print(m2)
        # print(m3)
        # print(m4)

    def video_open(self, *args):
        thread = threading.Thread(target=self.open_video_opencv)
        thread.daemon = True
        thread.start()

    def on_drawing_area_draw(self, widget, cr):
        global dimg
        mutex.acquire()
        Gdk.cairo_set_source_pixbuf(cr, dimg, 10, 0)
        cr.paint()
        mutex.release()

    def on_drawing_area2_draw(self, widget, cr):
        global dimg2
        mutex.acquire()
        Gdk.cairo_set_source_pixbuf(cr, dimg2, 10, 0)
        cr.paint()
        mutex.release()
