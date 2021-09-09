import cv2
import time
import threading
import configparser
import io
import asyncio
import numpy as np
import matplotlib.pyplot as plt

import multiprocessing
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GdkPixbuf
from phys import settings_window

mutex_for_main_video_stream_img = threading.Lock()
mutex_for_flash_images_array = threading.Lock()
main_video_stream_img = GdkPixbuf.Pixbuf.new_from_file("start.png")
flash_images = []


class ChartHandler:
    def __init__(self):
        self.cm = []
        self._tmp_cms = []
        self._event = threading.Event()
        self._previous_cm = [252, 101]
        self._previous_time = time.time()
        self.q = multiprocessing.Queue()
        self.processes = []

    async def on_event(self):
        print("-------", self.cm)
        current_time = time.time()
        if current_time - self._previous_time < 1:
            return
        self._previous_time = current_time
        await asyncio.sleep(0.5)
        x, y = self.__count_cm()
        print(x, y)
        if abs(x - self._previous_cm[0]) + abs(y - self._previous_cm[1]) > 40:
            print(f"suspicious shift to {x, y}")
            return

        self._previous_cm = [x, y]
        print(f"new point ->{self._previous_cm}")
        self._tmp_cms.append((x, y, self._previous_time))
        for x in self.processes:
            x.join()
        pl = multiprocessing.Process(None, self.get_image, args=(self.q, self._tmp_cms,))
        pl.start()
        self.processes.append(pl)

    @staticmethod
    def get_image(qq, array_of_cm):
        fig, ax = plt.subplots()
        print([i for i in range(len(list(zip(*array_of_cm))[0]))], list(zip(*array_of_cm))[0])
        ax.plot([i for i in range(len(list(zip(*array_of_cm))[0]))], list(zip(*array_of_cm))[0], color="tab:red")
        ax2 = ax.twinx()
        ax2.plot([i for i in range(len(list(zip(*array_of_cm))[0]))], list(zip(*array_of_cm))[1], color="tab:blue")
        fig.set_size_inches(12, 3)
        #  = io.BytesIO()
        fig.savefig("1.png", transparent=False)

    def __count_cm(self):
        av_x, av_y = map(sum, zip(*self.cm))
        for point in self.cm:
            if abs(point[0] - av_x) + abs(point[1] - av_y) > 40:
                self.cm.remove(point)
        return map(lambda x: x // len(self.cm), map(sum, zip(*self.cm)))


class MainWindow:
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("UI/main_window.glade")

        self.main_window = builder.get_object("main_window")
        grid = builder.get_object("main_window_grid")
        self.drawing_area = builder.get_object("main_drawing_area")
        self.drawing_area2 = builder.get_object("flash_drawing_area")
        settings_button = builder.get_object("settings_button")
        analyse_toggle_button = builder.get_object("toggle_button_analyse")
        self.video_control_toggle_button = builder.get_object("toggle_button_video_control")
        self.scale = builder.get_object("scale")
        self.adj = builder.get_object("adjustment1")

        self.main_window.connect("destroy", Gtk.main_quit)
        self.drawing_area.connect("draw", self.on_drawing_area_draw)
        self.drawing_area2.connect("draw", self.on_drawing_area2_draw)
        settings_button.connect("pressed", self.open_settings)
        analyse_toggle_button.connect("toggled", self.on_analyse_button_toggled)
        self.video_control_toggle_button.connect("toggled", self.on_video_control_button_toggled)
        self.scale.connect("value_changed", self.on_scale_value_changed)
        # self.drawing_area2.connect("button-press-event", self.on_drawing_area2_pressed)
        # self.drawing_area2.connect("button-release-event", self.on_drawing_area2_released)
        # self.drawing_area2.connect("motion-notify-event", self.on_drawing_area2_motion)
        # self.drawing_area2.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        # self.drawing_area2.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        # self.drawing_area2.add_events(Gdk.EventMask.BUTTON1_MOTION_MASK)

        self.drawing_area.set_size_request(632, 562)
        self.drawing_area2.set_size_request(632, 562)
        # fig = Figure(figsize=(5, 4), dpi=100)
        # ax = fig.add_subplot()
        # t = np.arange(0.0, 3.0, 0.01)
        # s = np.sin(2 * np.pi * t)
        # ax.plot(t, s)
        # canvas = FigureCanvas(fig)
        # grid.attach(canvas, 1, 0, 1, 1)
        self.main_window.show_all()
        self.play_video = False
        self.analyse = False
        self.time_per_frame = 0.04
        self.coords_of_mdi = [[0.0, 0.0], [0.0, 0.0]]
        self.chart = ChartHandler()

    # def on_drawing_area2_pressed(self, widget, event):
    #     if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
    #         self.coords_of_mdi[0] = [event.x, event.y]
    #         self.coords_of_mdi[1] = [event.x, event.y]
    #
    # def on_drawing_area2_released(self, widget, event):
    #     if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
    #         self.coords_of_mdi[1] = [event.x, event.y]
    #
    # def on_drawing_area2_motion(self, widget, event):
    #     self.coords_of_mdi[1] = [event.x, event.y]
    #     self.drawing_area2.queue_draw()

    def on_scale_value_changed(self, widget):
        self.drawing_area2.queue_draw()

    def on_analyse_button_toggled(self, widget):
        if widget.get_active():
            self.analyse = True
            self.main_window.resize(1266, 562)
        else:
            self.analyse = False
            self.main_window.resize(632, 562)

    def on_video_control_button_toggled(self, widget):
        if widget.get_active():
            widget.set_label("Остановить")
            self.play_video = True
            self.video_open()
        else:
            widget.set_label("Запустить")
            self.play_video = False

    @staticmethod
    def open_settings(*_):
        win = settings_window.SettingsWindow()
        win.run()

    def video_player(self):
        global main_video_stream_img, flash_images

        def loop_thread_():
            nonlocal loop
            loop.run_forever()

        loop = asyncio.new_event_loop()
        loop_thread = threading.Thread(target=loop_thread_, daemon=True)
        loop_thread.start()

        video_res: bool
        filename: str
        camera_index: int
        view_x1: int
        view_y1: int
        view_x2: int
        view_y2: int
        analyse_x1: int
        analyse_y1: int
        analyse_x2: int
        analyse_y2: int

        def read_settings():

            def sort_coords(arr):
                if arr[0][0] > arr[1][0]:
                    arr[0][0], arr[1][0] = arr[1][0], arr[0][0]
                if arr[0][1] > arr[1][1]:
                    arr[0][1], arr[1][1] = arr[1][1], arr[0][1]
                return arr[0][0], arr[0][1], arr[1][0], arr[1][1]

            nonlocal video_res, filename, camera_index
            nonlocal view_x1, view_y1, view_x2, view_y2
            nonlocal analyse_x1, analyse_y1, analyse_x2, analyse_y2

            config = configparser.ConfigParser()
            config.read("settings.ini")
            filename = config["video_file"]["video_file_name"]
            video_res = (False, True)[config["video_stream"]["from_camera"] == "True"]
            camera_index = int(config["video_camera"]["video_camera_index"])
            tmp_arr = [
                [int(k) for k in i.split(", ")]
                for i in config.get("area_coordinates", "coords_of_view_box")[2:-2].split("], [")
            ]
            view_x1, view_y1, view_x2, view_y2 = sort_coords(tmp_arr)
            tmp_arr = [
                [int(k) for k in i.split(", ")]
                for i in config.get("area_coordinates", "coords_of_box_to_analyse")[2:-2].split("], [")
            ]
            analyse_x1, analyse_y1, analyse_x2, analyse_y2 = sort_coords(tmp_arr)

        read_settings()

        # view_x1
        # view_y1 = 576 - view_y1
        # # view_x2
        # view_y2: 576 - view_y2
        # # analyse_x1
        # analyse_y1 = 576 - analyse_y1
        # # analyse_x2
        # analyse_y2 = 576 - analyse_y2

        if video_res:
            cap = cv2.VideoCapture(camera_index)
        else:
            cap = cv2.VideoCapture(filename)
        if not cap.isOpened():
            raise Exception("Video stream open failed")

        self.time_per_frame = 1 / int(cap.get(cv2.CAP_PROP_FPS))
        width, height = cap.get(3), cap.get(4)
        if width != 720 or height != 576:
            print("? video properties")
            return

        time_prev = time.time()
        back_sub = cv2.createBackgroundSubtractorKNN(7, 100.0, False)
        while cap.isOpened() and self.play_video:
            time_cur = time.time()
            ret, img = cap.read()
            if not ret:
                break
            mutex_for_main_video_stream_img.acquire()
            try:
                tmp_img1 = img[
                           view_y1:view_y2,
                           view_x1:view_x2
                           ]
                main_video_stream_img = GdkPixbuf.Pixbuf.new_from_data(
                    tmp_img1.tostring(),
                    GdkPixbuf.Colorspace.RGB, False, 8,
                    tmp_img1.shape[1],
                    tmp_img1.shape[0],
                    tmp_img1.shape[2] * tmp_img1.shape[1], None, None
                )
                self.drawing_area.queue_draw()
            finally:
                mutex_for_main_video_stream_img.release()

            tmp_img = img[
                      analyse_y1:analyse_y2,
                      analyse_x1:analyse_x2
                      ]
            tmp = tmp_img
            tmp_img = cv2.cvtColor(tmp_img, cv2.COLOR_BGR2GRAY)
            tmp_img = cv2.GaussianBlur(tmp_img, (19, 15), 0)
            back_sub_mask = back_sub.apply(tmp_img)
            tmp_img = cv2.bitwise_and(tmp_img, tmp_img, mask=back_sub_mask)
            _, thresh = cv2.threshold(tmp_img, 17, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
            # set offset param eq to ?
            # coords of mdi[0] or left top corner
            # ? change hierarh retention

            if contours:
                mutex_for_flash_images_array.acquire()
                if len(contours) == 1:
                    mu = cv2.moments(contours[0])
                    mc = (int(mu['m10'] / (mu['m00'] + 1e-5)), int(mu['m01'] / (mu['m00'] + 1e-5)))
                    self.chart.cm.append(mc)
                    if len(self.chart.cm) == 1:
                        asyncio.run_coroutine_threadsafe(self.chart.on_event(), loop)

                else:
                    pass
                try:
                    if time_cur - time_prev > 1:
                        self.chart.cm = []
                        flash_images = []
                        self.scale.set_value(0.0)
                    if len(flash_images) < 11:
                        cv2.drawContours(tmp, contours, -1, (0, 255, 0), 3)
                        flash_images.append(GdkPixbuf.Pixbuf.new_from_data(
                            tmp.tostring(),
                            GdkPixbuf.Colorspace.RGB, False, 8,
                            tmp.shape[1],
                            tmp.shape[0],
                            tmp.shape[2] * tmp_img.shape[1], None, None
                        ))
                        self.adj.set_upper(len(flash_images) - 1)
                        self.drawing_area2.queue_draw()

                finally:
                    mutex_for_flash_images_array.release()
                # for x in range(len(contours)):
                #     if len(contours[x]) < 100:
                #         xx = x
                #         continue
                #     if len(contours[x]) < 7:
                #         contours = contours[:x]
                #         break
                # contours = contours[xx:]
                time_prev = time.time()
            # cv2.drawContours(tmp, contours, 0, 194, 30)

            if not video_res:
                time.sleep(self.time_per_frame)
        cap.release()
        self.play_video = False

    def video_open(self):
        thread_video_player = threading.Thread(target=self.video_player, daemon=True)
        thread_video_player.start()

    @staticmethod
    def on_drawing_area_draw(_, cr):
        global main_video_stream_img
        mutex_for_main_video_stream_img.acquire()
        try:
            Gdk.cairo_set_source_pixbuf(cr, main_video_stream_img, 0, 0)
            cr.paint()
        finally:
            mutex_for_main_video_stream_img.release()

    def on_drawing_area2_draw(self, _, cr):
        global flash_images
        mutex_for_flash_images_array.acquire()
        try:
            if flash_images:
                Gdk.cairo_set_source_pixbuf(
                    cr,
                    flash_images[min(int(self.scale.get_value()), len(flash_images) - 1)], 0, 0)
                cr.paint()
        finally:
            mutex_for_flash_images_array.release()
        size_x = min(max(int(-self.coords_of_mdi[0][0]), int(self.coords_of_mdi[1][0] - self.coords_of_mdi[0][0])),
                     720 - int(self.coords_of_mdi[0][0]))
        size_y = min(max(int(-self.coords_of_mdi[0][1]), int(self.coords_of_mdi[1][1] - self.coords_of_mdi[0][1])),
                     576 - int(self.coords_of_mdi[0][1]))
        cr.set_source_rgba(0.0, 0.9, 0.9, 0.8)
        cr.rectangle(int(self.coords_of_mdi[0][0]), int(self.coords_of_mdi[0][1]), size_x, size_y)
        cr.stroke()
