import cv2
import time
import threading
import gi
import configparser
import numpy as np

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
from phys import CustomHeaderbar

mutex_for_second_area = threading.Lock()
mutex_for_main_video_stream_img = threading.Lock()
main_video_stream_img = GdkPixbuf.Pixbuf.new_from_file("start.png")
flash_img = GdkPixbuf.Pixbuf.new_from_file("start.png")


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

        self.play_video = True
        self.time_per_frame = 0.1

    def video_grab_thread(self):
        global main_video_stream_img, flash_img

        def read_config():
            config = configparser.ConfigParser()
            config.read("settings.ini")
            x, y = [int(i) for i in config["area_coordinates"]["coordinates"][1:-1].split(',')]
            return config["video_file"]["video_file_name"], config["video_stream"]["from_file"], x, y, x + 512, y + 512

        filename, video_res, \
        left_top_corner_x, left_top_corner_y, right_down_corner_x, right_down_corner_y = read_config()

        video_res = (False, True)[video_res == "True"]

        mask = []
        with open("mask", "rb") as file:
            counter = 0
            while counter < 512 * 64:
                byte = file.read(1)
                mask.append(np.uint8(ord(byte)))
                counter += 1
            mask = np.unpackbits(np.array(mask), axis=0).reshape(512, 512)

        cap = cv2.VideoCapture(filename)
        if not cap.isOpened():
            raise Exception("Video stream open failed")

        self.time_per_frame = 1 / int(cap.get(cv2.CAP_PROP_FPS))
        width = cap.get(3)
        height = cap.get(4)
        self.drawing_area.set_size_request(width, height)
        self.drawing_area2.set_size_request(width, height)

        ret, img = cap.read()
        if not ret:
            raise Exception("Video first frame read failed")
        mutex_for_main_video_stream_img.acquire()
        main_video_stream_img = img
        mutex_for_main_video_stream_img.release()
        # previous = img[
        #               left_top_corner_y:right_down_corner_y,
        #               left_top_corner_x:right_down_corner_x
        #     ]
        # previous = cv2.bitwise_and(previous, previous, mask=mask)
        back_sub = cv2.createBackgroundSubtractorKNN()
        while cap.isOpened() and self.play_video:
            t1 = time.time()
            ret, img = cap.read()
            if not ret:
                break

            mutex_for_main_video_stream_img.acquire()
            main_video_stream_img = GdkPixbuf.Pixbuf.new_from_data(
                img.tobytes(),
                GdkPixbuf.Colorspace.RGB, False, 8,
                img.shape[1], img.shape[0],
                img.shape[2] * img.shape[1], None, None
            )
            mutex_for_main_video_stream_img.release()
            self.drawing_area.queue_draw()

            # ----find out if a flash occurred----
            tmp_img = img[
                      left_top_corner_y:right_down_corner_y,
                      left_top_corner_x:right_down_corner_x
            ]
            tmp_img = cv2.bitwise_and(tmp_img, tmp_img, mask=mask)
            tmp_img = cv2.GaussianBlur(tmp_img, (17, 13), 0)
            back_sub_mask = back_sub.apply(tmp_img)
            tmp_img = cv2.bitwise_and(tmp_img, tmp_img, mask=back_sub_mask)

            flash_img = GdkPixbuf.Pixbuf.new_from_data(
                tmp_img.tobytes(), 0, False, 8,
                tmp_img.shape[1], tmp_img.shape[0],
                tmp_img.shape[1]*tmp_img.shape[2], None, None
            )

            self.drawing_area2.queue_draw()
            # ------------------------------------
            previous = img

            if video_res:
                pass
                # time.sleep(self.time_per_frame)
            t2 = time.time()
            print(t2-t1)
        cap.release()

        # def open_video_opencv(self):
        # global main_video_stream_img
        #
        # main_video_stream_img = GdkPixbuf.Pixbuf.new_from_data(
        #     main_video_stream_img.tostring(),
        #     GdkPixbuf.Colorspace.RGB, False, 8,
        #     main_video_stream_img.shape[1],
        #     main_video_stream_img.shape[0],
        #     main_video_stream_img.shape[2] * main_video_stream_img.shape[1], None, None
        # )
        #
        # self.drawing_area.queue_draw()
        #
        # previous = cv2.bitwise_and(previous, previous, mask=mask)
        # previous = GdkPixbuf.Pixbuf.new_from_data(
        #     previous.tostring(),
        #     GdkPixbuf.Colorspace.RGB, False, 8,
        #     previous.shape[1],
        #     previous.shape[0],
        #     previous.shape[2] * previous.shape[1], None, None
        # )
        # # previous = cv2.GaussianBlur(previous, (17, 13), 0)
        # h_bins = 512
        # # s_bins = 0
        # histSize = [h_bins]
        # h_ranges = [0, 180]
        # # s_ranges = [0, 256]
        # ranges = h_ranges
        # channels = [0]
        # # m1, m2, m3, m4 = [], [], [], []
        # while cap.isOpened():
        #     mutex_for_main_video_stream_img.acquire()
        #     ret, main_video_stream_img = cap.read()
        #     if main_video_stream_img is not None:
        #         main_video_stream_img = GdkPixbuf.Pixbuf.new_from_data(
        #             main_video_stream_img.tobytes(),
        #             GdkPixbuf.Colorspace.RGB, False, 8,
        #             main_video_stream_img.shape[1],
        #             main_video_stream_img.shape[0],
        #             main_video_stream_img.shape[2] * main_video_stream_img.shape[1], None, None
        #         )
        #         self.drawing_area.queue_draw()
        #         mutex_for_main_video_stream_img.acquire()
        #         img = img[
        #               LEFT_TOP_CORNER_Y:RIGHT_DOWN_CORNER_Y,
        #               LEFT_TOP_CORNER_X:RIGHT_DOWN_CORNER_X
        #               ]
        #         # t1 = time.time()
        #         # t2 = time.time()
        #         # img = cv2.blur(img,(5,5))
        #         #
        #         # img = cv2.GaussianBlur(img, (11, 11), 0)
        #         tmp = img
        #         img = cv2.absdiff(img, previous)
        #         # ret1, img = cv2.threshold(img, 10, 255, cv2.THRESH_BINARY)
        #
        #         dimg2 = GdkPixbuf.Pixbuf.new_from_data(
        #             img.tobytes(),
        #             GdkPixbuf.Colorspace.RGB, False, 8,
        #             img.shape[1],
        #             img.shape[0],
        #             img.shape[2] * img.shape[1], None, None
        #         )
        #
        #         self.drawing_area2.queue_draw()
        #
        #         # print(t2-t1)
        #         hist_prev = cv2.calcHist([pr2], channels, None, histSize, ranges, accumulate=False)
        #         # cv2.normalize(hist_prev, hist_prev, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        #         #
        #         hist_curr = cv2.calcHist([img], channels, None, histSize, ranges, accumulate=False)
        #         # cv2.normalize(hist_curr, hist_curr, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        #         #
        #         #
        #
        #         # # start = time.time()
        #         # base_base = cv2.compareHist(hist_curr, hist_prev, 0)
        #         # m1.append(base_base)
        #         # # end = time.time()
        #         # # print("1", end-start)
        #         # # start = time.time()
        #         # base_base = cv2.compareHist(hist_curr, hist_prev, 1)
        #         # m2.append(base_base)
        #         # # end = time.time()
        #         # # print("2", end - start)
        #         # # start = time.time()
        #         base_base = cv2.compareHist(hist_curr, hist_prev, 2)
        #         m1.append(base_base)
        #         # m3.append(base_base)
        #         # # end = time.time()
        #         # # print("3", end - start)
        #         # # start = time.time()
        #         # base_base = cv2.compareHist(hist_curr, hist_prev, 3)
        #         # m4.append(base_base)
        #         # end = time.time()/
        #         # print("4", end - start)
        #
        #         # base_base = cv2.compareHist(hist_curr, hist_prev, 3)
        #         # if base_base > 0.05:
        #         #     print(t)
        #         #     # self.drawing_area2.queue_draw()
        #         #     # cv2.imwrite('work_ex/' + str(t) + '.jpg', tmp)
        #         # else:
        #         #     pass
        #
        #         previous = tmp
        #
        #         # dimg = GdkPixbuf.Pixbuf.new_from_data(img.tobytes(),
        #         #                                       GdkPixbuf.Colorspace.RGB, False, 8,
        #         #                                       img.shape[1],
        #         #                                       img.shape[0],
        #         #                                       img.shape[2] * img.shape[1], None, None)
        #         # if base_base > 0.05:
        #         #     self.drawing_area2.queue_draw()

    def video_open(self, *_):
        thread = threading.Thread(target=self.video_grab_thread, daemon=True)
        thread.start()

    @staticmethod
    def on_drawing_area_draw(_, cr):
        global main_video_stream_img
        mutex_for_main_video_stream_img.acquire()
        Gdk.cairo_set_source_pixbuf(cr, main_video_stream_img, 0, 0)
        mutex_for_main_video_stream_img.release()
        cr.paint()

    @staticmethod
    def on_drawing_area2_draw(_, cr):
        global flash_img
        mutex_for_second_area.acquire()
        Gdk.cairo_set_source_pixbuf(cr, flash_img, 0, 0)
        mutex_for_second_area.release()
        cr.paint()
