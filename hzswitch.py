#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# hzswitch: plugin to control Rhythmbox playback pitch
# to enhance classical music
# Copyright (C) 2017 Kurt Weber
#
# Based on rbtempo by Bruce Merry
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import GObject, GLib, Gio, Gtk, RB, Peas, Gst

def find_widget_by_name(root, name):
    """Recursively find the widget named `name` under root, returning
    `None` if it could not be found."""
    if Gtk.Buildable.get_name(root) == name:
        return root
    elif isinstance(root, Gtk.Container):
        for child in root.get_children():
            ans = find_widget_by_name(child, name)
            if ans is not None:
                return ans
    return None

class HzSwitchPlugin(GObject.Object, Peas.Activatable):
    object = GObject.property(type=GObject.GObject)
    active = False
    mode = 0
    modes = [
        ["Mode 1: A4=440Hz to 432Hz", 0.98182],   #Detune by -1.818% to get from A4=440Hz to A4=432Hz
        ["Mode 2: A4=432Hz to 440Hz", 1.01852],   #Detune by +1.818% to get from A4=432Hz to A4=440Hz
        ["Mode 3: C3=128Hz R.Steiner", 0.978497727273],  #Detune to get Rudolf Steiner frequency C3=128Hz or A4=430,539 Hz (only for the cool kids)
    ]

    def get_shell(self):
        return self.object

    def get_player(self):
        return self.get_shell().props.shell_player.props.player

    def get_toolbar(self):
        """Get the widget for the main toolbar."""
        return find_widget_by_name(self.get_shell().props.window, 'main-toolbar')

    def on_modebtn_pressed(self, widget, data):
        self.mode += 1
        if self.mode > len(self.modes) - 1:
            self.mode = 0
        widget.set_label(self.modes[self.mode][0])
        if self.pitch_element != None:
            self.pitch_element.props.pitch = self.modes[self.mode][1]
        self.save_settings()
        
    def on_tglbtn_toggled(self, widget, data):
        self.active = widget.get_active()
        if widget.get_active():
            self.add_filter()
            self.pitch_element.props.pitch = self.modes[self.mode][1]
        else:
            self.pitch_element.props.pitch = 1.0
            self.remove_filter()
        self.save_settings()

    def get_shell_player(self):
        return self.get_shell().props.shell_player #player to control things like pause and so on
            
    def on_playing_song_changed(self, player, entry):
        self.get_shell_player().seek(0)

    def create_tglbtn(self):
        self.load_settings()
        tglbtn = Gtk.ToggleButton(label='Hz-Switch')
        tglbtn.connect('toggled', self.on_tglbtn_toggled, None)
        tglbtn.set_active(self.active)
        tglbtn.show()
        return tglbtn
        
    def create_modebtn(self):
        self.load_settings()
        modebtn = Gtk.Button(label=self.modes[self.mode][0])
        modebtn.connect('pressed', self.on_modebtn_pressed, None)
        modebtn.show()
        return modebtn        

    def create_toolbox(self):
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 2)
        box.pack_start(self.create_modebtn(), False, False, 0)
        box.pack_start(self.create_tglbtn(), False, False, 0)        
        item = Gtk.ToolItem.new()
        item.set_margin_left(6)
        item.set_margin_top(12)
        item.set_margin_bottom(12)
        item.add(box)
        item.show_all()
        return item

    def add_filter(self):
        """Add the filter to the player, if not already present"""
        if self.pitch_element is None:
            self.pitch_element = Gst.ElementFactory.make("pitch", None)
            self.get_player().add_filter(self.pitch_element)

    def remove_filter(self):
        """Delete the filter if it is present"""
        if self.pitch_element is not None:
            self.get_player().remove_filter(self.pitch_element)
            self.pitch_element = None

    def do_activate(self):
        """Plugin activation callback"""
        self.pitch_element = None
        self.toolbox = self.create_toolbox()
        self.get_toolbar().insert(self.toolbox, 2)
        player = self.get_shell().props.shell_player
        player.connect('playing-song-changed', self.on_playing_song_changed)

    def do_deactivate(self):
        """Plugin deactivation callback"""
        self.get_toolbar().remove(self.toolbox)
        self.remove_filter()
        del self.toolbox
        del self.pitch_element
        
    def save_settings(self):
        scriptname = __file__.split("/")[-1]
        filelocation = __file__[:-1*len(scriptname)]
        with open(filelocation + "settings.ini", "w", encoding="UTF-8") as fw:
            fw.writelines("mode=" + str(self.mode) + "\n")
            fw.writelines("active=" + str(self.active) + "\n")
            
    def load_settings(self):
        scriptname = __file__.split("/")[-1]
        filelocation = __file__[:-1*len(scriptname)]
        with open(filelocation + "settings.ini", "r", encoding="UTF-8") as fr:
            for line in fr.readlines():
                if "mode" in line:
                    self.mode = int(line[:-1][-1])
                if "active=True" in line:
                    self.active = True
