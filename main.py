import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from phys import main_window


if __name__ == "__main__":
    window = main_window.MainWindow()
    Gtk.main()
