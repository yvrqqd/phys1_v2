import cv2
import time
import threading
import gi
import configparser
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf, Gio
from phys import InfoWindow, SettingsWindow, MainWindow


class CustomHeaderBar(Gtk.HeaderBar):
    def __init__(self, win):
        Gtk.HeaderBar.__init__(self)
        self.window = win

        self.set_show_close_button(True)
        self.props.title = "EXAMPLE"
        self.connect("destroy", Gtk.main_quit)

        self.window_box = win.get_child()
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(self.button_box)

        icon_size = Gtk.IconSize.MENU
        settings_icon = Gtk.Image.new_from_icon_name("system-run", icon_size)
        play_icon = Gtk.Image.new_from_icon_name("media-playback-start", icon_size)

        self.settings_button = Gtk.ToolButton.new(settings_icon, "settings")
        self.settings_button.connect("clicked", self.open_settings)
        self.button_box.pack_start(self.settings_button, False, False, 10)

        self.play_button = Gtk.ToolButton.new(play_icon, "play")
        self.play_button.connect("clicked", self.start_videostream)
        self.button_box.pack_start(self.play_button, False, False, 0)

        self.info_button = Gtk.Button(label="?")
        self.info_button.connect("clicked", self.open_info)
        self.button_box.pack_end(self.info_button, False, False, 0)

    def open_info(self, *args):
        win = InfoWindow.InfoWindow()

    def start_videostream(self, *args):
        self.window.video_open(self.window)

    def open_settings(self, *args):
        win = SettingsWindow.SettingsWindow()