"""Add-on hotkeys and first-run keymap switch.

Add-on keymaps are checked before the active keyconfig, so these override
the Industry Compatible keys they share (Shift+Right-click, Space, 1~5, X/V/C,
Shift+H, Alt+H) with the Maya behavior.
"""

import bpy

from .prefs import get_prefs

_addon_keymaps = []


# Keymaps where each mode's own hotkeys live; X/V/C must win over them too.
MODE_KEYMAPS = ("Object Mode", "Mesh", "Curve", "Armature", "Pose")

# (keymap, operator, key, modifiers, properties) - Maya hotkeys that the
# Industry Compatible keymap is missing or maps differently.
MAYA_HOTKEYS = (
    # Viewport
    ("3D View", "screen.region_quadview", 'SPACE', {}, {}),
    ("Screen", "screen.screen_full_area", 'SPACE', {"ctrl": True}, {}),
    ("Frames", "screen.animation_play", 'V', {"alt": True}, {}),
    # Editing
    ("Screen", "ed.redo", 'Y', {"ctrl": True}, {}),
    ("Object Mode", "maya.delete_history", 'D', {"alt": True, "shift": True}, {}),
    # Display / shading
    ("Object Non-modal", "maya.set_shading", 'FOUR', {}, {"shading": 'WIREFRAME'}),
    ("Object Non-modal", "maya.set_shading", 'FIVE', {}, {"shading": 'SOLID'}),
    ("Object Non-modal", "maya.set_shading", 'SIX', {}, {"shading": 'MATERIAL'}),
    ("Object Non-modal", "maya.set_shading", 'SEVEN', {}, {"shading": 'RENDERED'}),
    # Components
    ("3D View", "maya.component_mode", 'F8', {}, {"mode": 'TOGGLE'}),
    ("3D View", "maya.component_mode", 'F9', {}, {"mode": 'VERT'}),
    ("3D View", "maya.component_mode", 'F10', {}, {"mode": 'EDGE'}),
    ("3D View", "maya.component_mode", 'F11', {}, {"mode": 'FACE'}),
    *((km, "maya.smooth_preview", key, {}, {"level": level})
      for km in ("Object Mode", "Mesh")
      for key, level in (('ONE', '1'), ('TWO', '2'), ('THREE', '3'))),
    # Visibility: Ctrl+H hide (already in Industry Compatible), Shift+H show, Alt+H isolate
    ("Object Mode", "object.hide_view_clear", 'H', {"shift": True}, {"select": False}),
    ("Object Mode", "object.hide_view_set", 'H', {"alt": True}, {"unselected": True}),
    ("Mesh", "mesh.reveal", 'H', {"shift": True}, {"select": False}),
    ("Mesh", "mesh.hide", 'H', {"alt": True}, {"unselected": True}),
    ("Curve", "curve.reveal", 'H', {"shift": True}, {"select": False}),
    ("Curve", "curve.hide", 'H', {"alt": True}, {"unselected": True}),
    ("Armature", "armature.reveal", 'H', {"shift": True}, {"select": False}),
    ("Armature", "armature.hide", 'H', {"alt": True}, {"unselected": True}),
    ("Pose", "pose.reveal", 'H', {"shift": True}, {"select": False}),
    ("Pose", "pose.hide", 'H', {"alt": True}, {"unselected": True}),
)

# Hold to snap: X grid, V vertex, C curve (edge)
SNAP_KEYS = (('X', 'GRID'), ('V', 'VERTEX'), ('C', 'EDGE'))


def _new_item(km, idname, key, value='PRESS', props=None, **modifiers):
    kmi = km.keymap_items.new(idname, key, value, **modifiers)
    for name, prop_value in (props or {}).items():
        setattr(kmi.properties, name, prop_value)
    _addon_keymaps.append((km, kmi))


def _keymap(kc, name):
    default = bpy.context.window_manager.keyconfigs.default.keymaps.get(name)
    space_type = default.space_type if default else 'EMPTY'
    region_type = default.region_type if default else 'WINDOW'
    return kc.keymaps.new(name=name, space_type=space_type, region_type=region_type)


def register_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is None:  # background mode
        return
    prefs = get_prefs()
    use_marking_menu = prefs.use_marking_menu if prefs else True
    use_maya_hotkeys = prefs.use_maya_hotkeys if prefs else True

    if use_marking_menu:
        _new_item(_keymap(kc, "Object Mode"), "wm.call_menu_pie", 'RIGHTMOUSE', shift=True,
                  props={"name": "MAYA_MT_object_marking_menu"})
        _new_item(_keymap(kc, "Mesh"), "wm.call_menu_pie", 'RIGHTMOUSE', shift=True,
                  props={"name": "MAYA_MT_mesh_marking_menu"})

    if use_maya_hotkeys:
        for km_name, idname, key, modifiers, props in MAYA_HOTKEYS:
            _new_item(_keymap(kc, km_name), idname, key, props=props, **modifiers)
        for km_name in ("3D View",) + MODE_KEYMAPS:
            km = _keymap(kc, km_name)
            for key, element in SNAP_KEYS:
                _new_item(km, "maya.snap_hold", key, props={"element": element})
                _new_item(km, "maya.snap_hold", key, 'RELEASE', props={"element": element, "release": True})


def unregister_keymaps():
    for km, kmi in _addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except (ReferenceError, RuntimeError):
            pass
    _addon_keymaps.clear()


def _first_run():
    """Switch to the Maya-like keymap once, right after the add-on is installed."""
    prefs = get_prefs()
    if prefs is None or not prefs.auto_apply_keymap or prefs.keymap_applied:
        return None
    from .operators import activate_keyconfig
    try:
        if activate_keyconfig("Industry_Compatible"):
            prefs.keymap_applied = True
            bpy.ops.maya.setup_viewport()
            # Re-add our hotkeys on top of the freshly loaded keyconfig.
            unregister_keymaps()
            register_keymaps()
    except Exception as ex:  # never break add-on loading over this
        print("Maya Style UI: could not apply keymap:", ex)
    return None


def register():
    register_keymaps()
    if not bpy.app.background:
        bpy.app.timers.register(_first_run, first_interval=0.5)


def unregister():
    if bpy.app.timers.is_registered(_first_run):
        bpy.app.timers.unregister(_first_run)
    unregister_keymaps()
