from functools import wraps
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from phys import InfoWindow, SettingsWindow


def parity_checker(function):
    @wraps(function)
    def change_parity(*args, **kwargs):
        change_parity.parity = (1, 0)[change_parity.parity]
        return function(*args, **kwargs)
    change_parity.parity = 0
    return change_parity


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
        self.play_button.connect("clicked", self.start_video_stream)
        self.button_box.pack_start(self.play_button, False, False, 0)

        self.info_button = Gtk.Button(label="?")
        self.info_button.connect("clicked", self.open_info)
        self.button_box.pack_end(self.info_button, False, False, 0)

    @staticmethod
    def open_info(*_):
        win = InfoWindow.InfoWindow()

    @parity_checker
    def start_video_stream(self, *_):
        if self.start_video_stream.parity:
            self.window.play_video = True
            self.window.video_open(self.window)
        else:
            self.window.play_video = False

    @staticmethod
    def open_settings(*_):
        win = SettingsWindow.SettingsWindow()
