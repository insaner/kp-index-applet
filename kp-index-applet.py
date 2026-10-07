#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("MatePanelApplet", "4.0")
from gi.repository import Gtk, MatePanelApplet, GLib, Gio
import cairo
import json
import sys

class KpApplet:
    def __init__(self, applet):
        self.applet = applet
        self.da = Gtk.DrawingArea()
        self.da.set_size_request(36, 22)	# applet dimensions
        self.applet.add(self.da)
        self.da.connect("draw", self.on_draw)
        self.kp_data = []
        self.update_data()
        self.da.show()
        self.applet.show_all()
        GLib.timeout_add_seconds(3600, self.update_data)	# refresh every hour

    def update_data(self):
        url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

        def on_response(file, result, user_data=None):
            try:
                stream = file.read_finish(result)
                raw = stream.read_bytes(1024 * 1024, None).get_data()
                stream.close(None)
                data = json.loads(raw.decode("utf-8"))
                self.kp_data = [float(row["Kp"]) for row in data[-21:-1]]
                print("Kp data loaded successfully:", self.kp_data)
            except Exception as e:
                print(f"Kp update error: {type(e).__name__}: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc()
                self.kp_data = []
            self.da.queue_draw()
            return False

        try:
            # print("Starting request to NOAA...")
            Gio.File.new_for_uri(url).read_async(GLib.PRIORITY_DEFAULT, None, on_response, None)
        except Exception as e:
            print(f"Kp request error: {e}", file=sys.stderr)
            self.kp_data = []
            self.da.queue_draw()
        return True

    def on_draw(self, widget, cr):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        if not self.kp_data:
            return

        bar_w = w / len(self.kp_data)
        for i, kp in enumerate(self.kp_data):
            bh = min((kp / 9.0) * h, h)
            y = h - bh
            if kp < 5.0:
                cr.set_source_rgb(0.2, 0.8, 0.2)
            elif kp < 6.5:
                cr.set_source_rgb(0.9, 0.9, 0.2)
            elif kp < 7.5:
                cr.set_source_rgb(1.0, 0.6, 0.1)
            else:
                cr.set_source_rgb(1.0, 0.0, 0.0)
            cr.rectangle(i * bar_w, y, bar_w - 1, bh)
            cr.fill()

def applet_factory(applet, iid, data):
    if iid != "KpIndexApplet":
        return False
    KpApplet(applet)
    return True

MatePanelApplet.Applet.factory_main(
    "KpIndexAppletFactory", True,
    MatePanelApplet.Applet.__gtype__,
    applet_factory, None
)
