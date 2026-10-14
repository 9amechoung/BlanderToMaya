"""Maya scene defaults and selection display.

- New scenes start like Maya's: lengths shown in centimeters, time range 1-120 at 24 fps,
  35 mm cameras and viewports (Blender: meters, 1-250, 50 mm)
- Selected objects show their wireframe on top of the shading (green for the lead
  selection, white for the others), like Maya
"""

import bpy
from bpy.app.handlers import persistent

from .prefs import get_prefs

DEFAULTS_KEY = "_maya_scene_defaults"
WIRE_KEY = "_maya_wire"

WIRE_TYPES = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'CURVES'}

MAYA_FRAME_END = 120
MAYA_LENS = 35.0


# ---------------------------------------------------------------------------
# Scene defaults
# ---------------------------------------------------------------------------

def apply_scene_defaults(scene):
    units = scene.unit_settings
    units.system = 'METRIC'
    units.length_unit = 'CENTIMETERS'  # 1 Blender unit is still 1 m: FBX gives the same size in Maya
    scene.frame_start = 1
    scene.frame_end = MAYA_FRAME_END
    scene.render.fps = 24
    scene.render.fps_base = 1.0
    for obj in scene.objects:
        if obj.type == 'CAMERA':
            obj.data.lens = MAYA_LENS
    scene[DEFAULTS_KEY] = True


def apply_viewport_lens(screens=None):
    for screen in screens or bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.lens = MAYA_LENS


class MAYA_OT_scene_defaults(bpy.types.Operator):
    """Maya scene settings: centimeters, frames 1-120 at 24 fps, 35 mm camera and viewport"""
    bl_idname = "maya.scene_defaults"
    bl_label = "Maya Scene Defaults"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        apply_scene_defaults(context.scene)
        apply_viewport_lens()
        return {'FINISHED'}


@persistent
def _on_load(_dummy):
    _wire_state.clear()
    prefs = get_prefs()
    if prefs is not None and not prefs.use_scene_defaults:
        return
    if bpy.data.filepath:  # an existing file keeps its own settings
        return
    for scene in bpy.data.scenes:
        if not scene.get(DEFAULTS_KEY):
            apply_scene_defaults(scene)
    apply_viewport_lens()


# ---------------------------------------------------------------------------
# Wireframe on the selected objects
# ---------------------------------------------------------------------------

_wire_state = {}


def _selected_names(view_layer):
    try:
        return frozenset(o.name for o in view_layer.objects.selected)
    except (AttributeError, ReferenceError):
        return frozenset()


def update_selection_wire(scene=None, force=False):
    context = bpy.context
    view_layer = getattr(context, "view_layer", None)
    if view_layer is None:
        return
    prefs = get_prefs()
    enabled = prefs is None or prefs.use_selection_wire
    selected = _selected_names(view_layer) if enabled else frozenset()
    key = view_layer.as_pointer()
    if not force and _wire_state.get(key) == selected:
        return
    _wire_state[key] = selected
    for obj in view_layer.objects:
        if obj.type not in WIRE_TYPES:
            continue
        want = obj.name in selected
        if want and not obj.show_wire:
            obj.show_wire = True
            obj[WIRE_KEY] = True
        elif not want and obj.get(WIRE_KEY):
            obj.show_wire = False
            del obj[WIRE_KEY]


def clear_selection_wire():
    for obj in bpy.data.objects:
        if obj.get(WIRE_KEY):
            obj.show_wire = False
            del obj[WIRE_KEY]
    _wire_state.clear()


@persistent
def _on_depsgraph(scene, _depsgraph=None):
    try:
        update_selection_wire(scene)
    except (AttributeError, ReferenceError, RuntimeError):
        pass


classes = (
    MAYA_OT_scene_defaults,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_post.append(_on_load)
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph)


def unregister():
    for handlers, fn in ((bpy.app.handlers.depsgraph_update_post, _on_depsgraph),
                         (bpy.app.handlers.load_post, _on_load)):
        if fn in handlers:
            handlers.remove(fn)
    try:
        clear_selection_wire()
    except (AttributeError, RuntimeError):
        pass
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
