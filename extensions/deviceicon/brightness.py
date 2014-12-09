# Copyright (C) 2014 Sam Parkinson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from gettext import gettext as _
import math

from gi.repository import Gtk

from sugar3 import profile
from sugar3.graphics import style
from sugar3.graphics.icon import Icon
from sugar3.graphics.tray import TrayIcon
from sugar3.graphics.palette import Palette
from sugar3.graphics.palettemenu import PaletteMenuBox
from sugar3.graphics.xocolor import XoColor

from jarabe.frame.frameinvoker import FrameWidgetInvoker
from jarabe.model.brightness import brightness

_ICON_NAME = 'brightness'


class DeviceView(TrayIcon):

    FRAME_POSITION_RELATIVE = 160

    def __init__(self, label):
        self._color = profile.get_color()
        self._label = label

        TrayIcon.__init__(self, icon_name=_ICON_NAME, xo_color=self._color)

        self.set_palette_invoker(FrameWidgetInvoker(self))
        self.palette_invoker.props.toggle_palette = True

        brightness.brightness_changed.connect(self.__brightness_changed_cb)

        self._update_output_info()

    def create_palette(self):
        palette = DisplayPalette()
        palette.set_group_id('frame')
        return palette

    def _update_output_info(self):
        current_level = brightness.get_brightness()
        xo_color = self._color

        icon_number = math.ceil(float(brightness.get_brightness()) * 3
                                / brightness.get_max_brightness()) * 33
        if icon_number == 99:
            icon_number = 100

        self.icon.props.icon_name = \
            'brightness-{:03d}'.format(int(icon_number))

    def __brightness_changed_cb(self, **kwargs):
        self._update_output_info()


class BrightnessManagerWidget(Gtk.VBox):

    def __init__(self, text, icon_name):
        Gtk.VBox.__init__(self)
        self._progress_bar = None
        self._adjustment = None

        icon = Icon(icon_size=Gtk.IconSize.MENU)
        icon.props.icon_name = icon_name
        icon.props.xo_color = XoColor('%s,%s' % (style.COLOR_WHITE.get_svg(),
                                      style.COLOR_BUTTON_GREY.get_svg()))
        icon.show()

        label = Gtk.Label(text)
        label.show()

        grid = Gtk.Grid()
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.attach(icon, 0, 0, 1, 1)
        grid.attach(label, 1, 0, 1, 1)
        grid.show()

        alignment = Gtk.Alignment()
        alignment.set(0.5, 0, 0, 0)
        alignment.add(grid)
        alignment.show()
        self.add(alignment)

        alignment = Gtk.Alignment()
        alignment.set(0.5, 0, 0, 0)
        alignment.set_padding(0, 0, style.DEFAULT_SPACING,
                              style.DEFAULT_SPACING)

        if brightness.can_set_brightness():
            adjustment = Gtk.Adjustment(
                value=brightness.get_brightness(),
                lower=0,
                upper=brightness.get_max_brightness() + 1,
                step_incr=1,
                page_incr=1,
                page_size=1)
            self._adjustment = adjustment

            self._adjustment_hid = \
                self._adjustment.connect('value_changed', self.__adjusted_cb)

            hscale = Gtk.HScale()
            hscale.props.draw_value = False
            hscale.set_adjustment(adjustment)
            hscale.set_digits(0)
            hscale.set_size_request(style.GRID_CELL_SIZE * 4, -1)
            alignment.add(hscale)
            hscale.show()
        else:
            self._progress_bar = Gtk.ProgressBar()
            self._progress_bar.set_size_request(
                style.zoom(style.GRID_CELL_SIZE * 4), -1)
            alignment.add(self._progress_bar)
            self._progress_bar.show()

        alignment.show()
        self.add(alignment)

    def update(self):
        if self._adjustment:
            self._adjustment.handler_block(self._adjustment_hid)
            self._adjustment.props.value = brightness.get_brightness()
            self._adjustment.handler_unblock(self._adjustment_hid)
        else:
            self._progress_bar.props.fraction = \
                float(brightness.get_brightness()) \
                / brightness.get_max_brightness()

    def __adjusted_cb(self, device, data=None):
        value = self._adjustment.props.value
        brightness.set_brightness(int(value))


class DisplayPalette(Palette):

    def __init__(self):
        Palette.__init__(self, label=_('My Display'))

        self._brightness_manager = BrightnessManagerWidget(_('Brightness'),
                                                           'brightness-100')
        self._brightness_manager.show()

        self._box = PaletteMenuBox()
        self._box.append_item(self._brightness_manager, 0, 0)
        self._box.show()

        self.set_content(self._box)
        self.connect('popup', self.__popup_cb)

    def __popup_cb(self, palette):
        self._brightness_manager.update()


def setup(tray):
    tray.add_device(DeviceView(_('Display')))
