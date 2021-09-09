import re

import cv2
import configparser
import json
import numpy as np
import threading
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio


class SettingsWindow(Gtk.Application):
    def __init__(self):
        super(SettingsWindow, self).__init__(application_id=None, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.coords_view_box = [[0.0, 0.0], [0.0, 0.0]]
        self.coords_analyse_box = [[0.0, 0.0], [0.0, 0.0]]
        self.img = GdkPixbuf.Pixbuf.new_from_file("example_img.png")
        self.load_area_data()

    def do_activate(self):
        builder = Gtk.Builder()
        builder.add_from_file("UI/settings_window.glade")
        builder.connect_signals(self)

        self.settings_window = builder.get_object("settings_window")
        self.radiobutton_camera = builder.get_object("radiobutton_from_camera")
        self.radiobutton_file = builder.get_object("radiobutton_from_file")
        self.spin_button = builder.get_object("camera_index_spin_button")
        self.file_chooser_button = builder.get_object("file_chooser_button")
        self.list_of_available_cameras = builder.get_object("list_available")
        self.list_of_working_cameras = builder.get_object("list_working")
        self.drawing_area = builder.get_object("mask_editor")
        self.toggle_view_box = builder.get_object("toggle_btn_choose_view_box")
        self.toggle_box_to_analyse = builder.get_object("toggle_btn_choose_box_to_analyse")

        self.area_accept_button = builder.get_object("area_accept_button")

        self.area_accept_button.connect("released", self.on_area_accept_button)
        self.toggle_view_box.connect("toggled", self.on_toggled, 1)
        self.toggle_box_to_analyse.connect("toggled", self.on_toggled, 2)
        self.toggle_box_to_analyse.set_active(True)

        self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.drawing_area.add_events(Gdk.EventMask.BUTTON1_MOTION_MASK)
        self.drawing_area.set_size_request(720, 576)
        self.drawing_area.queue_draw()
        self.load_settings()
        self.settings_window.show_all()

    def load_area_data(self):
        config = configparser.ConfigParser()
        config.read("settings.ini")
        self.coords_view_box = [[int(k) for k in i.split(", ")]
                                for i in config.get("area_coordinates", "coords_of_view_box")[2:-2].split("], [")]
        self.coords_analyse_box = [[int(k) for k in i.split(", ")]
                                   for i in
                                   config.get("area_coordinates", "coords_of_box_to_analyse")[2:-2].split("], [")]

    def on_area_accept_button(self, *_):
        config = configparser.ConfigParser()
        config.read("settings.ini")
        config.set("area_coordinates", "coords_of_view_box", str(self.coords_view_box))
        config.set("area_coordinates", "coords_of_box_to_analyse", str(self.coords_analyse_box))

        with open("settings.ini", 'w') as configfile:
            config.write(configfile)

    def on_toggled(self, obj, type_number):
        if type_number == 1 and self.toggle_view_box.get_active():
            self.toggle_box_to_analyse.set_active(False)
        elif type_number == 2 and self.toggle_box_to_analyse.get_active():
            self.toggle_view_box.set_active(False)

    def on_refresh_list_of_available_cameras(self, *_):
        is_working = True
        dev_port = 0
        working_ports = []
        available_ports = []
        while is_working and dev_port < 101:
            camera = cv2.VideoCapture(dev_port)
            if not camera.isOpened():
                is_working = False
            else:
                is_reading, img = camera.read()
                if is_reading:
                    working_ports.append(dev_port)
                else:
                    available_ports.append(dev_port)
            dev_port += 1

        if len(available_ports) == 0:
            self.list_of_available_cameras.set_text("None")
        else:
            tmp_str = ""
            for i in available_ports:
                tmp_str += str(i) + ' '
            self.list_of_available_cameras.set_text(tmp_str)

        if len(working_ports) == 0:
            self.list_of_working_cameras.set_text("None")
        else:
            tmp_str = ""
            for i in working_ports:
                tmp_str += str(i) + ' '
            self.list_of_working_cameras.set_text(tmp_str)

    def on_accept_changes(self, *_):
        config = configparser.ConfigParser()
        config.read("settings.ini")
        config.set("video_stream", "from_camera", str(self.radiobutton_camera.get_active()))
        config.set("video_stream", "from_file", str(self.radiobutton_file.get_active()))
        config.set("video_file", "video_file_name", str(self.file_chooser_button.get_filename()))
        config.set("video_camera", "video_camera_index", str(self.spin_button.get_value())[:-2])

        with open("settings.ini", 'w') as configfile:
            config.write(configfile)
        self.settings_window.destroy()

    def on_decline_changes(self, *_):
        self.settings_window.destroy()

    def load_settings(self):
        config = configparser.ConfigParser()
        config.read("settings.ini")

        if config["video_stream"]["from_camera"] == "True":
            self.radiobutton_camera.set_active(self)
        else:
            self.radiobutton_file.set_active(self)

        self.spin_button.set_value(int(config["video_camera"]["video_camera_index"]))
        self.file_chooser_button.set_filename(config["video_file"]["video_file_name"])

    def on_area_draw(self, widget, cr, *_):
        Gdk.cairo_set_source_pixbuf(cr, self.img, 0, 0)
        cr.paint()

        size_x = min(
            max(-self.coords_view_box[0][0], self.coords_view_box[1][0] - self.coords_view_box[0][0]),
            720 - self.coords_view_box[0][0]
        )
        size_y = min(
            max(-self.coords_view_box[0][1], self.coords_view_box[1][1] - self.coords_view_box[0][1]),
            576 - self.coords_view_box[0][1]
        )
        cr.set_source_rgba(0.0, 0.9, 0.0, 0.8)
        cr.rectangle(self.coords_view_box[0][0], self.coords_view_box[0][1], size_x, size_y)
        cr.stroke()

        size_x = min(
            max(-self.coords_analyse_box[0][0], self.coords_analyse_box[1][0] - self.coords_analyse_box[0][0]),
            720 - self.coords_analyse_box[0][0]
        )
        size_y = min(
            max(-self.coords_analyse_box[0][1], self.coords_analyse_box[1][1] - self.coords_analyse_box[0][1]),
            576 - self.coords_analyse_box[0][1]
        )
        cr.set_source_rgba(0.9, 0.9, 0.0, 0.8)
        cr.rectangle(self.coords_analyse_box[0][0], self.coords_analyse_box[0][1], size_x, size_y)
        cr.stroke()

    def on_area_pressed(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:  # 1 == left mouse button
            if self.toggle_view_box.get_active():
                self.coords_view_box[0] = [int(event.x), int(event.y)]
            else:
                self.coords_analyse_box[0] = [int(event.x), int(event.y)]

    def on_area_motion_notify_event(self, widget, event):
        pos_x = min(max(0, int(event.x)), 720)
        pos_y = min(max(0, int(event.y)), 576)
        if self.toggle_view_box.get_active():
            self.coords_view_box[1] = [pos_x, pos_y]
        else:
            self.coords_analyse_box[1] = [pos_x, pos_y]
        self.drawing_area.queue_draw()
