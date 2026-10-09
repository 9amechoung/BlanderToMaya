# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Style UI - make Blender feel like Maya.

- Maya workspace: Outliner left, Channel Box right, timeline bottom, Maya colors
- Maya menu bar with menu sets and status line in the top bar
- Industry Compatible (Maya-like) keymap applied on install
- Maya-style shelf bar on top of the 3D viewport
- Right-click (hold) component menu on objects
- Middle-drag along the picked gizmo axis (Move / Rotate / Scale)
- Ctrl+Shift+Right-click tool settings menu (orientation, snap, symmetry...)
- Shift+Right-click marking menus (object mode / edit mesh)
- Channel Box panel in the sidebar (N), plus editable local / world transforms
- Maya hotkeys (Space quad view, 4~7 shading, F8~F11, 1~3 smooth, X/V/C snap...)
"""

bl_info = {
    "name": "Maya Style UI",
    "author": "BlanderToMaya",
    "version": (0, 8, 2),
    "blender": (4, 0, 0),
    "location": "3D Viewport > Tool Header (Shelf), Shift+RMB (Marking Menu), N Panel > Channel Box",
    "description": "Maya-like keymap, shelf bar, marking menus and channel box",
    "category": "Interface",
}

from . import (prefs, operators, maya_ops, shelf, marking_menu, hotbox, rmb_menu, tool_menu, transform_tools, transform_panel, select_through, channel_box,
               modeling_toolkit, maya_menus, maya_ui, keymaps)

_modules = (prefs, operators, maya_ops, shelf, marking_menu, hotbox, rmb_menu, tool_menu, transform_tools, transform_panel, select_through, channel_box,
            modeling_toolkit, maya_menus, maya_ui, keymaps)


def register():
    for m in _modules:
        m.register()


def unregister():
    for m in reversed(_modules):
        m.unregister()
