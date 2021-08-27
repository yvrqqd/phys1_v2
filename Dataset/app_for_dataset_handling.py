import os
import threading
import cv2
import configparser
import gi
import numpy as np

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio

mutex_for_frame = threading.Lock()
FRAME_SOURCE = None
FRAME = None


class DatasetApp(Gtk.Application):
    def __init__(self):
        super(DatasetApp, self).__init__(application_id="dataset_app", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.coords = [[.0, .0], [.0, .0]]
        self.cap = None
        self.left_top_corner_x, self.left_top_corner_y, self.right_down_corner_x, self.right_down_corner_y = 0, 0, 0, 0
        self.positive_count = 0
        self.negative_count = 0

    def do_activate(self):
        builder = Gtk.Builder()
        builder.add_from_file("DatasetApp.glade")

        self.choose_file = builder.get_object("choose_video_file")
        self.drawing_area = builder.get_object("drawing_area1")
        self.choose_area_toggle = builder.get_object("choose_area_toggle")
        self.coord_label = builder.get_object("label_for_coords")
        main_window = builder.get_object("DatasetAppWindow")
        start_button = builder.get_object("start_button")
        skip_button = builder.get_object("skip_button")
        close_button = builder.get_object("close_button")
        next_frame_button = builder.get_object("next_frame_button")

        close_button.connect("clicked", main_window.destroy)
        start_button.connect("clicked", self.start_button_clicked)
        skip_button.connect("clicked", self.skip_button_clicked)
        next_frame_button.connect("clicked", self.next_frame_button_clicked)
        self.drawing_area.connect("button-press-event", self.on_drawing_area_pressed)
        self.drawing_area.connect("button-release-event", self.on_drawing_area_released)
        self.drawing_area.connect("motion-notify-event", self.on_drawing_area_motion)
        self.drawing_area.connect("draw", self.on_drawing_area_draw)
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.drawing_area.add_events(Gdk.EventMask.BUTTON1_MOTION_MASK)
        self.add_window(self.main_window)

        self.main_window.show_all()

    def read_frame(self):
        global FRAME_SOURCE, FRAME
        if self.cap:
            if self.cap.isOpened():
                ret, img = self.cap.read()
                if ret:
                    img = img[
                          self.left_top_corner_y:self.right_down_corner_y,
                          self.left_top_corner_x:self.right_down_corner_x
                          ]
                    with mutex_for_frame:
                        FRAME = GdkPixbuf.Pixbuf.new_from_data(
                            img.tobytes(),
                            GdkPixbuf.Colorspace.RGB, False, 8,
                            img.shape[1],
                            img.shape[0],
                            img.shape[2] * img.shape[1], None, None
                        )
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        FRAME_SOURCE = cv2.GaussianBlur(img, (11, 11), 0)
                    self.drawing_area.queue_draw()
                else:
                    print("no ret")

    def start_button_clicked(self, _):
        def read_settings():
            config = configparser.ConfigParser()
            config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "settings.ini")))
            x, y = [int(i) for i in config["area_coordinates"]["coordinates"][1:-1].split(',')]
            return x, y, x + 512, y + 512

        filename = self.choose_file.get_filename()
        self.left_top_corner_x, self.left_top_corner_y, \
            self.right_down_corner_x, self.right_down_corner_y = read_settings()
        if filename:
            self.cap = cv2.VideoCapture(filename)
            if not self.cap.isOpened():
                raise Exception("Video stream open failed")
            self.read_frame()
        else:
            print("no file")

    def skip_button_clicked(self, _):
        self.choose_area_toggle.set_active(False)
        self.read_frame()

    def next_frame_button_clicked(self, _):
        global FRAME_SOURCE
        with mutex_for_frame:
            if self.choose_area_toggle.get_active():
                if cv2.imwrite(fr"images/positive/img{self.positive_count}.jpg", FRAME_SOURCE):
                    x = int(min(self.coords[0][0], self.coords[1][0]))
                    y = int(min(self.coords[0][1], self.coords[1][1]))
                    size_x = int(abs(self.coords[0][0] - self.coords[1][0]))
                    size_y = int(abs(self.coords[0][1] - self.coords[1][1]))
                    with open("images/info.dat", 'a') as file:
                        file.write(f"/positive/img{self.negative_count}.jpg 1 {x} {y} {size_x} {size_y}\n")
                    self.positive_count += 1
                    print("Img saved")
                else:
                    print("Error while saving img")
            else:
                if cv2.imwrite(fr"images/negative/img{self.negative_count}.jpg", FRAME_SOURCE):
                    with open("images/bg.txt", 'a') as file:
                        file.write(f"/negative/img{self.negative_count}.jpg\n")
                    self.negative_count += 1
                    print("Img saved")
                else:
                    print("Error while saving img")

        self.choose_area_toggle.set_active(False)
        self.read_frame()

    def on_drawing_area_pressed(self, widget, event):
        if self.choose_area_toggle.get_active():
            if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
                self.coords[0] = [event.x, event.y]
                self.coords[1] = [event.x, event.y]
                self.coord_label.set_text(f"{np.around(self.coords[0])}\n{np.around(self.coords[1])}")
                self.drawing_area.queue_draw()

    def on_drawing_area_released(self, widget, event):
        if self.choose_area_toggle.get_active():
            if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
                self.coords[1] = [event.x, event.y]

    def on_drawing_area_motion(self, widget, event):
        if self.choose_area_toggle.get_active():
            self.coords[1] = [event.x, event.y]
            self.coord_label.set_text(f"{np.around(self.coords[0])}\n{np.around(self.coords[1])}")
            self.drawing_area.queue_draw()

    def on_drawing_area_draw(self, _, cr):
        global FRAME
        with mutex_for_frame:
            if not FRAME:
                return
            Gdk.cairo_set_source_pixbuf(cr, FRAME, 0, 0)
            cr.paint()
        if self.choose_area_toggle.get_active():
            size_x = min(max(int(-self.coords[0][0]), int(self.coords[1][0] - self.coords[0][0])),
                         512 - int(self.coords[0][0]))
            size_y = min(max(int(-self.coords[0][1]), int(self.coords[1][1] - self.coords[0][1])),
                         512 - int(self.coords[0][1]))
            cr.set_source_rgba(0.0, 0.9, 0.9, 0.8)
            cr.rectangle(int(self.coords[0][0]), int(self.coords[0][1]), size_x, size_y)
            cr.stroke()


if __name__ == "__main__":
    window = DatasetApp()
    window.run()
