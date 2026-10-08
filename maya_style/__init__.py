# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Style UI - make Blender feel like Maya.

- Industry Compatible (Maya-like) keymap applied on install
- Maya-style shelf bar on top of the 3D viewport
- Shift+Right-click marking menus (object mode / edit mesh)
- Channel Box panel in the sidebar (N)
- F8~F11 component mode hotkeys
"""

bl_info = {
    "name": "Maya Style UI",
    "author": "BlanderToMaya",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Tool Header (Shelf), Shift+RMB (Marking Menu), N Panel > Channel Box",
    "description": "Maya-like keymap, shelf bar, marking menus and channel box",
    "category": "Interface",
}

from . import prefs, operators, shelf, marking_menu, channel_box, keymaps

_modules = (prefs, operators, shelf, marking_menu, channel_box, keymaps)


def register():
    for m in _modules:
        m.register()


def unregister():
    for m in reversed(_modules):
        m.unregister()
