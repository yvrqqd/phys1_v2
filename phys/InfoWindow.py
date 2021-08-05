import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class InfoWindow:
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("/UI/InfoWindow.glade")
        info_window = builder.get_object("info_window")
        info_window.show()
