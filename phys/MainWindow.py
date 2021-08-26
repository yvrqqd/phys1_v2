import cv2
import time
import threading
import gi
import configparser
import numpy as np
from matplotlib.backends.backend_gtk3agg import (
    FigureCanvasGTK3Agg as FigureCanvas)
from matplotlib.figure import Figure


from external import gui
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
from phys import InfoWindow, SettingsWindow

mutex_for_main_video_stream_img = threading.Lock()
mutex_for_flash_images_array = threading.Lock()
main_video_stream_img = GdkPixbuf.Pixbuf.new_from_file("start.png")
flash_images = []


class MainWindow:
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("UI/MainWindow.glade")

        main_window = builder.get_object("main_window")
        grid = builder.get_object("main_window_grid")
        self.drawing_area = builder.get_object("main_drawing_area")
        self.drawing_area2 = builder.get_object("flash_drawing_area")
        settings_button = builder.get_object("settings_button")
        analyse_toggle_button = builder.get_object("toggle_button_analyse")
        self.video_control_toggle_button = builder.get_object("toggle_button_video_control")
        self.scale = builder.get_object("scale")

        main_window.connect("destroy", Gtk.main_quit)
        self.drawing_area.connect("draw", self.on_drawing_area_draw)
        self.drawing_area2.connect("draw", self.on_drawing_area2_draw)
        settings_button.connect("pressed", self.open_settings)
        analyse_toggle_button.connect("toggled", self.on_analyse_button_toggled)
        self.video_control_toggle_button.connect("toggled", self.on_video_control_button_toggled)
        self.scale.connect("value_changed", self.on_scale_value_changed)
        self.drawing_area2.connect("button-press-event", self.on_drawing_area2_pressed)
        self.drawing_area2.connect("button-release-event", self.on_drawing_area2_released)
        self.drawing_area2.connect("motion-notify-event", self.on_drawing_area2_motion)
        self.drawing_area2.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.drawing_area2.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.drawing_area2.add_events(Gdk.EventMask.BUTTON1_MOTION_MASK)

        self.drawing_area.set_size_request(720, 576)
        self.drawing_area2.set_size_request(720, 576)
        # fig = Figure(figsize=(5, 4), dpi=100)
        # ax = fig.add_subplot()
        # t = np.arange(0.0, 3.0, 0.01)
        # s = np.sin(2 * np.pi * t)
        # ax.plot(t, s)
        # canvas = FigureCanvas(fig)
        # grid.attach(canvas, 1, 0, 1, 1)
        main_window.show_all()
        self.play_video = False
        self.analyse = False
        self.time_per_frame = 0.04
        self.coords_of_mdi = [[0.0, 0.0], [0.0, 0.0]]

    def on_drawing_area2_pressed(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            self.coords_of_mdi[0] = [event.x, event.y]
            self.coords_of_mdi[1] = [event.x, event.y]

    def on_drawing_area2_released(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            self.coords_of_mdi[1] = [event.x, event.y]

    def on_drawing_area2_motion(self, widget, event):
        self.coords_of_mdi[1] = [event.x, event.y]
        self.drawing_area2.queue_draw()

    def on_scale_value_changed(self, widget):
        self.drawing_area2.queue_draw()

    def on_analyse_button_toggled(self, widget):
        if widget.get_active():
            self.analyse = True
        else:
            self.analyse = False

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
        win = SettingsWindow.SettingsWindow()

    def video_player(self):
        global main_video_stream_img, flash_images
        filename, video_res, camera_index, \
        left_top_corner_x, left_top_corner_y, right_down_corner_x, right_down_corner_y = [None for i in range(7)]

        def read_settings():
            nonlocal filename, video_res, camera_index, \
                left_top_corner_x, left_top_corner_y, right_down_corner_x, right_down_corner_y
            config = configparser.ConfigParser()
            config.read("settings.ini")
            filename = config["video_file"]["video_file_name"]
            video_res = (False, True)[config["video_stream"]["from_camera"] == "True"]
            camera_index = int(config["video_camera"]["video_camera_index"])
            x, y = [int(i) for i in config["area_coordinates"]["coordinates"][1:-1].split(',')]
            left_top_corner_x, left_top_corner_y, right_down_corner_x, right_down_corner_y = x, y, x + 512, y + 512

        read_settings()
        mask = []
        with open("mask", "rb") as file:
            counter = 0
            while counter < 512 * 64:
                byte = file.read(1)
                mask.append(np.uint8(ord(byte)))
                counter += 1
            mask = np.unpackbits(np.array(mask), axis=0).reshape(512, 512)
        if video_res:
            cap = cv2.VideoCapture(camera_index)
        else:
            cap = cv2.VideoCapture(filename)
        if not cap.isOpened():
            raise Exception("Video stream open failed")

        self.time_per_frame = 1 / int(cap.get(cv2.CAP_PROP_FPS))
        width = cap.get(3)
        height = cap.get(4)
        self.drawing_area.set_size_request(width, height)
        time_prev = time.time()
        back_sub = cv2.createBackgroundSubtractorKNN(7, 100.0, False)
        while cap.isOpened() and self.play_video:
            time_cur = time.time()
            ret, img = cap.read()
            if not ret:
                break
            mutex_for_main_video_stream_img.acquire()
            try:
                main_video_stream_img = GdkPixbuf.Pixbuf.new_from_data(
                    img.tostring(),
                    GdkPixbuf.Colorspace.RGB, False, 8,
                    img.shape[1],
                    img.shape[0],
                    img.shape[2] * img.shape[1], None, None
                )
                self.drawing_area.queue_draw()
            finally:
                mutex_for_main_video_stream_img.release()

            tmp_img = img[
                      left_top_corner_y:right_down_corner_y,
                      left_top_corner_x:right_down_corner_x
                      ]
            tmp = tmp_img
            tmp_img = cv2.bitwise_and(tmp_img, tmp_img, mask=mask)
            tmp_img = cv2.cvtColor(tmp_img, cv2.COLOR_BGR2GRAY)
            tmp_img = cv2.GaussianBlur(tmp_img, (17, 17), 0)
            back_sub_mask = back_sub.apply(tmp_img)
            tmp_img = cv2.bitwise_and(tmp_img, tmp_img, mask=back_sub_mask)
            _, thresh = cv2.threshold(tmp_img, 17, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
            # set offset param eq to ?
            # coords of mdi[0] or left top corner
            # ? change hierarh retention
            contours = sorted(contours, key=len)
            contours.reverse()

            if contours:
                xx = 0

                mutex_for_flash_images_array.acquire()
                try:
                    if time_cur - time_prev > 1:
                        flash_images = []
                        self.scale.set_value(0.0)
                    if len(flash_images) < 10:
                        flash_images.append(GdkPixbuf.Pixbuf.new_from_data(
                            img.tostring(),
                            GdkPixbuf.Colorspace.RGB, False, 8,
                            img.shape[1],
                            img.shape[0],
                            img.shape[2] * img.shape[1], None, None
                        ))
                        self.drawing_area2.queue_draw()

                finally:
                    mutex_for_flash_images_array.release()
                for x in range(len(contours)):
                    if len(contours[x]) < 100:
                        xx = x
                        continue
                    if len(contours[x]) < 7:
                        contours = contours[:x]
                        break
                contours = contours[xx:]
                time_prev = time.time()
            cv2.drawContours(tmp, contours, 0, 194, 30)

            tmp = cv2.cvtColor(thresh, cv2.COLOR_BGR2RGB)

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
        print(1)
