import cv2
import gi
import configparser

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf, Gio
import cairo


class SettingsWindow:
    """
    ...
    """

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

        self.mask_editor_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.mask_editor_area.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.mask_editor_area.add_events(Gdk.EventMask.BUTTON1_MOTION_MASK)

        self.mask_editor_area.set_size_request(720, 576)

        self.width_pressed = 0
        self.height_pressed = 0

        self.width_released = 0
        self.height_released = 0

        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 720, 576)
        self.context = cairo.Context(self.surface)

        self.img = GdkPixbuf.Pixbuf.new_from_file("start.png")
        self.mask_editor_area.queue_draw()
        self.load_settings()
        self.settings_window.show_all()

    def on_refresh_list_of_available_cameras(self, *args):
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

    def on_accept_changes(self, *args):
        config = configparser.ConfigParser()
        config.read("settings.ini")
        config.set("video_stream", "from_camera", str(self.radiobutton_camera.get_active()))
        config.set("video_stream", "from_file", str(self.radiobutton_file.get_active()))
        config.set("video_file", "video_file_name", str(self.file_chooser_button.get_filename()))
        config.set("video_camera", "video_camera_index", str(self.spin_button.get_value())[:-2])

        with open("settings.ini", 'w') as configfile:
            config.write(configfile)

        self.settings_window.destroy()

    def on_decline_changes(self, *args):
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

    def on_mask_editor_area_draw(self, widget, brush):
        brush.set_source_surface(self.surface, 0, 0)
        brush.paint()

    def on_mask_editor_area_pressed(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:  # 1 == left mouse button
            self.width_pressed = event.x
            self.height_pressed = event.y

    def on_mask_editor_area_released(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:  # 1 == left mouse button
            self.width_released = event.x
            self.height_released = event.y

            self.context.rectangle(0, 0, 100, 100)
            self.context.set_source_rgba(11, 1, 1, 1.0)
            self.context.fill()
            self.context.stroke()
            self.context.paint()

    def on_mask_editor_motion_notify_event(self, widget, event):
        self.context.rectangle(0, 0, 100, 100)
        self.context.set_source_rgba(11, 1, 1, 1.0)
        self.context.rectangle(0, 0, 100, 100)
        self.context.stroke()
        self.context.paint()
        self.mask_editor_area.queue_draw()
