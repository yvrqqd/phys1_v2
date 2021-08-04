import cv2
import time
import threading
import gi
import configparser
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf, Gio
from phys import CustomHeaderbar, InfoWindow, SettingsWindow, MainWindow

if __name__ == "__main__":
    # mutex = threading.Lock()
    # dimg = GdkPixbuf.Pixbuf.new_from_file("start.png")

    window = MainWindow.MainWindow()
    window.show_all()
    Gtk.main()
