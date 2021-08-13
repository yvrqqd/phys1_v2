import time

import cv2
import gi
import configparser
import json, sys
import numpy as np
from functools import wraps
from memory_profiler import profile

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf, Gio
import cairo


class SettingsWindow:
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("UI/SettingsWindow.glade")
        builder.connect_signals(self)

        self.settings_window = builder.get_object("settings_window")
        self.radiobutton_camera = builder.get_object("radiobutton_from_camera")
        self.radiobutton_file = builder.get_object("radiobutton_from_file")
        self.spin_button = builder.get_object("camera_index_spin_button")
        self.file_chooser_button = builder.get_object("file_chooser_button")
        self.list_of_available_cameras = builder.get_object("list_available")
        self.list_of_working_cameras = builder.get_object("list_working")
        self.mask_editor_area = builder.get_object("mask_editor")
        self.toggle_btn_move_mask = builder.get_object("toggle_btn_move_mask")
        self.toggle_btn_set_0 = builder.get_object("toggle_btn_set0")
        self.toggle_btn_del_mask = builder.get_object("toggle_btn_del_mask")
        self.mask_accept_button = builder.get_object("mask_accept_button")

        self.mask_accept_button.connect("released", self.on_mask_accept_button_released)
        self.toggle_btn_move_mask.connect("toggled", self.on_toggled, 1)
        self.toggle_btn_set_0.connect("toggled", self.on_toggled, 2)
        self.toggle_btn_del_mask.connect("toggled", self.on_toggled, 3)
        self.toggle_btn_move_mask.set_active(True)

        self.mask_editor_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.mask_editor_area.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.mask_editor_area.add_events(Gdk.EventMask.BUTTON1_MOTION_MASK)

        self.mask_editor_area.set_size_request(720, 576)

        self.coords = [[0.0, 0.0], [0.0, 0.0]]
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 720, 576)
        self.context = cairo.Context(self.surface)

        self.img = GdkPixbuf.Pixbuf.new_from_file("start.png")
        self.mask_editor_area.queue_draw()
        self.load_settings()
        self.settings_window.show_all()
        self.mass = [[]]
        self.load_mask_data()

    def load_mask_data(self):
        try:
            with open("mask_data.json", 'r') as file:
                self.mass = json.load(file)
        except FileNotFoundError as e:
            print("error while loading mask data: {}".format(e))

    def on_mask_accept_button_released(self, *_):
        border = self.mass[0]

        def is_masked(row, col):
            for rec in self.mass[1:]:
                if max(rec[0], rec[0] + rec[2]) >= border[0] + row >= min(rec[0], rec[0] + rec[2]) and \
                        max(rec[1], rec[1] + rec[3]) >= border[1] + col >= min(rec[1], rec[1] + rec[3]):
                    return 1
            return 0

        mask = np.ones([512, 512], dtype="uint8")
        for x in range(0, 512):
            for y in range(0, 512):
                if is_masked(x, y):
                    mask[x][y] = 0

        mask = np.packbits(mask, axis=0)
        with open("mask", "wb") as file:
            for byte in mask:
                file.write(byte)

        with open("mask_data.json", 'w') as file:
            json.dump(self.mass, file)

    def on_toggled(self, obj, type_number):
        if type_number == 1 and self.toggle_btn_move_mask.get_active():
            self.toggle_btn_del_mask.set_active(False)
            self.toggle_btn_set_0.set_active(False)
        elif type_number == 2 and self.toggle_btn_set_0.get_active():
            self.toggle_btn_move_mask.set_active(False)
            self.toggle_btn_del_mask.set_active(False)
        elif type_number == 3 and self.toggle_btn_del_mask.get_active():
            self.toggle_btn_move_mask.set_active(False)
            self.toggle_btn_set_0.set_active(False)

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

    def on_mask_editor_area_draw(self, widget, cr, *_):
        Gdk.cairo_set_source_pixbuf(cr, self.img, 0, 0)
        cr.paint()
        if self.toggle_btn_move_mask.get_active():
            cr.set_source_rgba(0.0, 0.9, 0.9, 0.8)
            cr.rectangle(self.mass[0][0], self.mass[0][1], 512, 512)
            cr.stroke()
            for rec in self.mass[1:]:
                cr.rectangle(rec[0], rec[1], rec[2], rec[3])
                cr.fill()
        elif self.toggle_btn_set_0.get_active():
            size_x = min(
                max(
                    int(-self.coords[0][0]),
                    int(self.coords[1][0] - self.coords[0][0])
                ),
                720 - int(self.coords[0][0])

            )
            size_y = min(
                max(
                    int(-self.coords[0][1]),
                    int(self.coords[1][1] - self.coords[0][1])
                ),
                576 - int(self.coords[0][1])
            )

            cr.set_source_rgba(0.0, 0.9, 0.9, 0.8)
            cr.rectangle(int(self.coords[0][0]) + 1, int(self.coords[0][1]) + 1, size_x - 1, size_y - 1)
            cr.fill()

            cr.set_source_rgba(0.0, 0.9, 0.9, 0.8)
            cr.rectangle(int(self.coords[0][0]), int(self.coords[0][1]), size_x, size_y)
            cr.stroke()

            cr.set_source_rgba(0.2, 0.7, 0.9, 0.5)
            cr.rectangle(self.mass[0][0], self.mass[0][1], 512, 512)
            cr.stroke()

            cr.set_source_rgba(0.0, 0.9, 0.9, 0.8)
            for rec in self.mass[1:]:
                cr.rectangle(rec[0], rec[1], rec[2], rec[3])
                cr.fill()
        else:
            cr.set_source_rgba(0.0, 0.9, 0.9, 0.8)
            cr.rectangle(self.mass[0][0], self.mass[0][1], 512, 512)
            cr.stroke()

            for rec in self.mass[1:]:
                cr.rectangle(rec[0], rec[1], rec[2], rec[3])
                cr.fill()

    def on_mask_editor_area_pressed(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:  # 1 == left mouse button
            self.coords[0] = [event.x, event.y]
            self.coords[1] = [event.x, event.y]

    def on_mask_editor_area_released(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_RELEASE and event.button == 1:
            self.coords[1] = [event.x, event.y]

            if self.toggle_btn_move_mask.get_active():
                pos_x = min(max(0, int(self.coords[1][0] - 256)), 208)
                pos_y = min(max(0, int(self.coords[1][1] - 256)), 64)
                self.mass[0] = [pos_x, pos_y]
            elif self.toggle_btn_set_0.get_active():
                size_x = min(max(int(-self.coords[0][0]), int(self.coords[1][0] - self.coords[0][0])),
                             720 - int(self.coords[0][0]))
                size_y = min(max(int(-self.coords[0][1]), int(self.coords[1][1] - self.coords[0][1])),
                             576 - int(self.coords[0][1]))
                self.mass.append([int(self.coords[0][0]), int(self.coords[0][1]), size_x, size_y])
            else:
                for rec in self.mass[1:]:
                    if max(rec[0], rec[0] + rec[2]) >= event.x >= min(rec[0], rec[0] + rec[2]) and \
                            max(rec[1], rec[1] + rec[3]) >= event.y >= min(rec[1], rec[1] + rec[3]):
                        self.mass.remove(rec)
        self.mask_editor_area.queue_draw()

    def on_mask_editor_motion_notify_event(self, widget, event):
        self.coords[1] = [event.x, event.y]

        if self.toggle_btn_move_mask.get_active():
            pos_x = min(max(0, int(self.coords[1][0] - 256)), 208)
            pos_y = min(max(0, int(self.coords[1][1] - 256)), 64)
            self.mass[0] = [pos_x, pos_y]

        self.mask_editor_area.queue_draw()
