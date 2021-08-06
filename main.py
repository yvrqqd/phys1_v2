import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from phys import MainWindow

if __name__ == "__main__":
    window = MainWindow.MainWindow()
    window.show_all()
    Gtk.main()
