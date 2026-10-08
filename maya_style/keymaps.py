"""Add-on hotkeys and first-run keymap switch.

Add-on keymaps are checked before the active keyconfig, so these override
Industry Compatible's Shift+Right-click (3D cursor) and F8~F11.
"""

import bpy

from .prefs import get_prefs

_addon_keymaps = []


def _new_item(km, idname, key, **kwargs):
    props = kwargs.pop("props", {})
    kmi = km.keymap_items.new(idname, key, 'PRESS', **kwargs)
    for name, value in props.items():
        setattr(kmi.properties, name, value)
    _addon_keymaps.append((km, kmi))


def register_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is None:  # background mode
        return
    prefs = get_prefs()
    use_marking_menu = prefs.use_marking_menu if prefs else True
    use_component_hotkeys = prefs.use_component_hotkeys if prefs else True

    if use_marking_menu:
        km = kc.keymaps.new(name="Object Mode", space_type='EMPTY')
        _new_item(km, "wm.call_menu_pie", 'RIGHTMOUSE', shift=True,
                  props={"name": "MAYA_MT_object_marking_menu"})
        km = kc.keymaps.new(name="Mesh", space_type='EMPTY')
        _new_item(km, "wm.call_menu_pie", 'RIGHTMOUSE', shift=True,
                  props={"name": "MAYA_MT_mesh_marking_menu"})

    if use_component_hotkeys:
        km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
        for key, mode in (('F8', 'TOGGLE'), ('F9', 'VERT'), ('F10', 'EDGE'), ('F11', 'FACE')):
            _new_item(km, "maya.component_mode", key, props={"mode": mode})


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
