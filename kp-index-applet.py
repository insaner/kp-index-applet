#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("MatePanelApplet", "4.0")
from gi.repository import Gtk, Gdk, MatePanelApplet, GLib, Gio
import cairo
import json
import sys
from datetime import datetime, timezone



class KpApplet:
    def __init__(self, applet):
        self.kp_data = []
        self.kp_times = []

        self.applet = applet
        self.settings = Gio.Settings.new("org.mate.kp-index-applet")
        self.settings.connect("changed", self.on_settings_changed)

        self.setup_popup_menu()

        self.da = Gtk.DrawingArea()
        self.da.set_size_request(	# applet dimensions
            self.settings.get_int("width"),
            self.settings.get_int("height")
            )
        self.event_box = Gtk.EventBox()
        self.event_box.add(self.da)
        self.applet.add(self.event_box)
        self.event_box.set_tooltip_text("Planetary Kp Index")
        self.da.connect("draw", self.on_draw)
        self.da.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.da.connect("motion-notify-event", self.on_motion)
        self.da.connect("leave-notify-event", self.on_leave)
        self.update_data()
        self.da.show()

        self.applet.show_all()

        GLib.timeout_add_seconds(self.settings.get_int("timeout"), self.update_data)	# data refresh rate

    def update_data(self):
        url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

        def on_response(file, result, user_data=None):
            try:
                stream = file.read_finish(result)
                raw = stream.read_bytes(1024 * 1024, None).get_data()
                stream.close(None)
                data = json.loads(raw.decode("utf-8"))
                self.kp_data = [float(row["Kp"]) for row in data[-21:-1]]
                rows = data[-21:-1]

                self.kp_data = [float(row["Kp"]) for row in rows]
                self.kp_times = [row["time_tag"] for row in rows]

                # print("Kp data loaded successfully:", self.kp_data)
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

    def on_motion(self, widget, event):
        if not self.kp_data:
            return False

        alloc = widget.get_allocation()
        w = alloc.width

        bar_w = w / len(self.kp_data)

        # Which bar is the pointer over?
        index = int(event.x / bar_w)

        if 0 <= index < len(self.kp_data):
            bar_kp = self.kp_data[index]
            bar_time = self.kp_times[index]

            current_kp = self.kp_data[-1]

            try:
                # NOAA time_tag is UTC.
                dt = datetime.fromisoformat(bar_time.replace("Z", "+00:00"))

                # Convert UTC to the computer's local timezone.
                local_dt = dt.astimezone()

                # No seconds.
                time_string = local_dt.strftime(
                    "%b %-d, %Y - %-I %p %Z"
                    # "%b %-d, %Y %-I:%M %p %Z"
                )

            except (ValueError, TypeError):
                time_string = bar_time

            widget.set_tooltip_text(
                f"Current Kp: {current_kp:.1f}\n"
                f"Kp: {bar_kp:.1f}\n"
                f"{time_string}"
            )

        return True

    def on_leave(self, widget, event):
        widget.set_tooltip_text(None)
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
                self.set_color(cr,"low-color")
            elif kp < 6.5:
                self.set_color(cr,"moderate-color")
            elif kp < 7.5:
                self.set_color(cr,"high-color")
            else:
                self.set_color(cr,"severe-color")
            cr.rectangle(i * bar_w, y, bar_w - 1, bh)
            cr.fill()

    def on_settings_changed(self, settings, key):
        # Called whenever any GSettings value changes.

        if key in ("width", "height"):
            self.da.set_size_request(
                settings.get_int("width"),
                settings.get_int("height")
            )
        # else:
        #     print("Unknown Key Changed: ", key)

        # Redraw for both size and color changes
        self.da.queue_draw()

    def set_color(self, cr, setting_name):
        # Read a CSS-style color from GSettings
        rgba = Gdk.RGBA()

        color_string = self.settings.get_string(setting_name)

        if rgba.parse(color_string):
            cr.set_source_rgba(
                rgba.red,
                rgba.green,
                rgba.blue,
                rgba.alpha
            )
        else:
            # Fall back to white if the configured color is invalid.
            cr.set_source_rgb(1.0, 1.0, 1.0)
            # print("Invalid Color")

    def setup_popup_menu(self):
        action_group = Gtk.ActionGroup(name="KpIndexActions")

        action_group.add_actions([
            (
                "Refresh",
                None,
                "_Refresh",
                None,
                "Update Kp Index data",
                self.on_refresh
            ),
            (
                "Preferences",
                None,
                "_Preferences",
                None,
                "Configure Kp Index Applet",
                self.on_preferences
            ),
        ])

        menu_xml = """
        <menuitem
            name="Refresh"
            action="Refresh"/>

        <separator/>

        <menuitem
            name="Preferences"
            action="Preferences"/>
        """

        self.applet.setup_menu(
            menu_xml,
            action_group
        )

    def on_refresh(self, action):
        self.update_data()

    def on_preferences(self, action):
        self.show_preferences()

    def show_preferences(self):
        # Show the preferences dialog.

        dialog = Gtk.Dialog(
            title="Kp Index Applet Preferences",
            transient_for=self.applet.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL
        )

        dialog.set_border_width(12)

        dialog.add_button(
            Gtk.STOCK_CLOSE,
            Gtk.ResponseType.CLOSE
        )

        content = dialog.get_content_area()

        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(10)
        grid.set_border_width(6)

        alignment = Gtk.Alignment(
            xalign=0.5,
            yalign=0.5,
            xscale=0,
            yscale=0
        )

        alignment.add(grid)
        content.pack_start(alignment, True, True, 0)

        size_label = Gtk.Label()
        size_label.set_markup("<b>Graph size</b>")
        size_label.set_halign(Gtk.Align.START)

        grid.attach(size_label, 0, 0, 2, 1)

        width_label = Gtk.Label(label="Width:")
        width_label.set_halign(Gtk.Align.START)

        width_spin = Gtk.SpinButton.new_with_range(
            1,       # minimum
            1000,    # maximum
            1        # step
        )

        width_spin.set_value(
            self.settings.get_int("width")
        )

        grid.attach(width_label, 0, 1, 1, 1)
        grid.attach(width_spin, 1, 1, 1, 1)

        height_label = Gtk.Label(label="Height:")
        height_label.set_halign(Gtk.Align.START)

        height_spin = Gtk.SpinButton.new_with_range(
            1,
            1000,
            1
        )

        height_spin.set_value(
            self.settings.get_int("height")
        )

        grid.attach(height_label, 0, 2, 1, 1)
        grid.attach(height_spin, 1, 2, 1, 1)

        colors_label = Gtk.Label()
        colors_label.set_markup("<b>Kp colors</b>")
        colors_label.set_halign(Gtk.Align.START)

        grid.attach(colors_label, 0, 3, 2, 1)

        low_button = self.create_color_button("low-color")
        moderate_button = self.create_color_button("moderate-color")
        high_button = self.create_color_button("high-color")
        severe_button = self.create_color_button("severe-color")

        # Low
        label = Gtk.Label(label="Kp < 5:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, 4, 1, 1)
        grid.attach(low_button, 1, 4, 1, 1)

        # Moderate
        label = Gtk.Label(label="Kp 5 – 6.5:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, 5, 1, 1)
        grid.attach(moderate_button, 1, 5, 1, 1)

        # High
        label = Gtk.Label(label="Kp 6.5 – 7.5:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, 6, 1, 1)
        grid.attach(high_button, 1, 6, 1, 1)

        # Severe
        label = Gtk.Label(label="Kp ≥ 7.5:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, 7, 1, 1)
        grid.attach(severe_button, 1, 7, 1, 1)

        # Connect controls to GSettings
        width_spin.connect("value-changed", self.on_width_changed)
        height_spin.connect("value-changed", self.on_height_changed)

        dialog.show_all()

        dialog.run()
        dialog.destroy()

    def create_color_button(self, setting_name):
        # Create a Gtk.ColorButton initialized from a GSettings CSS-style color string.

        button = Gtk.ColorButton()

        color = Gdk.RGBA()

        color_string = self.settings.get_string(setting_name)

        if color.parse(color_string):
            button.set_rgba(color)

        button.connect(
            "color-set",
            self.on_color_changed,
            setting_name
        )

        return button

    def on_width_changed(self, spin):
        self.settings.set_int(
            "width",
            spin.get_value_as_int()
        )

    def on_height_changed(self, spin):
        self.settings.set_int(
            "height",
            spin.get_value_as_int()
        )

    def on_color_changed(self, button, setting_name):
        # Store the selected color as a CSS-style hexadecimal string.

        rgba = button.get_rgba()

        color_string = "#{:02x}{:02x}{:02x}".format(
            round(rgba.red * 255),
            round(rgba.green * 255),
            round(rgba.blue * 255)
        )

        self.settings.set_string(
            setting_name,
            color_string
        )


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
