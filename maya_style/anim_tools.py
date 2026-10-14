"""Maya animation editing: tangents, the time slider and the Graph Editor.

- Tangent buttons in the Graph Editor header (Auto, Spline, Linear, Flat, Stepped, Break, Unify)
- Right-click menu on the time slider (Set Key, Delete, Copy, Paste, Tangents, Set Range...)
- Shift+drag on the time slider selects the keys in that frame range
- Middle-drag moves the selected keys in the Graph Editor and Dope Sheet
- Red key ticks on the time slider (set with the Maya colors)
"""

import bpy
from bpy.props import EnumProperty


# ---------------------------------------------------------------------------
# F-Curves of an ID, for Blender 4.x (Action.fcurves) and 5.x (slotted actions)
# ---------------------------------------------------------------------------

def fcurve_collection(id_data, create=False):
    """The F-Curve collection that animates this ID (None when it has no animation)."""
    if create and id_data.animation_data is None:
        id_data.animation_data_create()
    ad = id_data.animation_data
    if ad is None or ad.action is None:
        return None
    action = ad.action
    fcurves = getattr(action, "fcurves", None)
    if fcurves is not None:
        return fcurves
    try:
        from bpy_extras import anim_utils
        channelbag = anim_utils.action_get_channelbag_for_slot(action, ad.action_slot)
    except (ImportError, AttributeError):
        return None
    return channelbag.fcurves if channelbag is not None else None


def find_fcurve(id_data, data_path, index):
    fcurves = fcurve_collection(id_data)
    if fcurves is None:
        return None
    for fc in fcurves:
        if fc.data_path == data_path and (index < 0 or fc.array_index == index):
            return fc
    return None


def remove_fcurve(id_data, fc):
    fcurves = fcurve_collection(id_data)
    if fcurves is not None:
        fcurves.remove(fc)


def _editor_fcurves(context):
    """F-Curves shown in the current animation editor, or those of the selected objects."""
    for name in ("visible_fcurves", "editable_fcurves"):
        try:
            curves = getattr(context, name, None)
        except (AttributeError, RuntimeError):
            curves = None
        if curves:
            return list(curves)
    curves = []
    ids = set(context.selected_objects or [])
    if context.active_object is not None:
        ids.add(context.active_object)
    for obj in ids:
        for id_data in (obj, obj.data):
            if id_data is None or not hasattr(id_data, "animation_data"):
                continue
            fcurves = fcurve_collection(id_data)
            if fcurves is not None:
                curves.extend(fcurves)
    return curves


# ---------------------------------------------------------------------------
# Tangents
# ---------------------------------------------------------------------------

TANGENTS = (
    ('AUTO', "Auto", "Smooth curve that never overshoots the keys (Maya's default)", 'HANDLE_AUTOCLAMPED'),
    ('SPLINE', "Spline", "Smooth curve through the keys", 'HANDLE_AUTO'),
    ('LINEAR', "Linear", "Straight lines between the keys", 'IPO_LINEAR'),
    ('FLAT', "Flat", "Horizontal tangents: the curve eases in and out of each key", 'IPO_EASE_IN_OUT'),
    ('STEPPED', "Stepped", "Hold the value until the next key", 'IPO_CONSTANT'),
    ('BREAK', "Break Tangents", "In and out tangents move separately", 'HANDLE_FREE'),
    ('UNIFY', "Unify Tangents", "In and out tangents stay in a line", 'HANDLE_ALIGNED'),
)


def set_tangent(fcurves, kind):
    count = 0
    for fc in fcurves:
        if getattr(fc, "lock", False):
            continue
        changed = False
        for kp in fc.keyframe_points:
            if not kp.select_control_point:
                continue
            changed = True
            count += 1
            if kind == 'STEPPED':
                kp.interpolation = 'CONSTANT'
            elif kind == 'LINEAR':
                kp.interpolation = 'LINEAR'
            elif kind in {'AUTO', 'SPLINE', 'FLAT'}:
                kp.interpolation = 'BEZIER'
                handle = {'AUTO': 'AUTO_CLAMPED', 'SPLINE': 'AUTO', 'FLAT': 'ALIGNED'}[kind]
                kp.handle_left_type = handle
                kp.handle_right_type = handle
                if kind == 'FLAT':
                    x, y = kp.co
                    kp.handle_left = (x - abs(x - kp.handle_left[0]), y)
                    kp.handle_right = (x + abs(kp.handle_right[0] - x), y)
            elif kind == 'BREAK':
                kp.handle_left_type = 'FREE'
                kp.handle_right_type = 'FREE'
            elif kind == 'UNIFY':
                kp.handle_left_type = 'ALIGNED'
                kp.handle_right_type = 'ALIGNED'
        if changed:
            fc.update()
    return count


class MAYA_OT_set_tangent(bpy.types.Operator):
    """Set the tangents of the selected keys (Maya: Graph Editor tangent buttons)"""
    bl_idname = "maya.set_tangent"
    bl_label = "Set Tangents"
    bl_options = {'REGISTER', 'UNDO'}

    tangent: EnumProperty(name="Tangent", items=[t[:3] for t in TANGENTS], default='AUTO')

    @classmethod
    def description(cls, context, properties):
        for key, name, desc, _icon in TANGENTS:
            if key == properties.tangent:
                return "%s: %s" % (name, desc)
        return cls.__doc__

    def execute(self, context):
        if not set_tangent(_editor_fcurves(context), self.tangent):
            self.report({'WARNING'}, "Select some keys first")
            return {'CANCELLED'}
        for area in context.screen.areas:
            if area.type in {'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'VIEW_3D'}:
                area.tag_redraw()
        return {'FINISHED'}


def draw_tangent_buttons(layout):
    row = layout.row(align=True)
    for key, name, _desc, icon in TANGENTS:
        if key == 'BREAK':
            row.separator()
        row.operator("maya.set_tangent", text="", icon=icon).tangent = key


def _draw_graph_header(self, context):
    from .prefs import get_prefs
    prefs = get_prefs(context)
    if prefs is not None and not prefs.use_anim_tools:
        return
    self.layout.separator()
    draw_tangent_buttons(self.layout)


class MAYA_MT_tangents(bpy.types.Menu):
    bl_label = "Tangents"

    def draw(self, context):
        for key, name, _desc, icon in TANGENTS:
            self.layout.operator("maya.set_tangent", text=name, icon=icon).tangent = key


# ---------------------------------------------------------------------------
# Time slider
# ---------------------------------------------------------------------------

def _is_timeline(context):
    area = context.area
    return area is not None and area.type == 'DOPESHEET_EDITOR' and area.ui_type == 'TIMELINE'


class MAYA_MT_time_slider(bpy.types.Menu):
    bl_label = "Time Slider"

    def draw(self, context):
        lay = self.layout
        lay.operator("anim.keyframe_insert", text="Set Key  (S)", icon='KEY_HLT')
        lay.operator("action.delete", text="Delete Selected Keys", icon='X')
        lay.separator()
        lay.operator("action.copy", text="Copy", icon='COPYDOWN')
        lay.operator("action.paste", text="Paste", icon='PASTEDOWN')
        lay.operator("action.duplicate_move", text="Duplicate Keys")
        lay.separator()
        lay.menu("MAYA_MT_tangents", icon='HANDLE_AUTOCLAMPED')
        lay.separator()
        lay.operator("action.previewrange_set", text="Set Range to Selected Keys (Range Slider)")
        lay.operator("anim.previewrange_clear", text="Clear Range Slider")
        lay.prop(context.scene, "use_preview_range", text="Use Range Slider")
        lay.separator()
        lay.prop(context.scene.tool_settings, "use_keyframe_insert_auto", text="Auto Key")
        lay.prop(context.scene.render, "fps", text="Frame Rate")
        lay.operator("render.opengl", text="Playblast", icon='RENDER_ANIMATION').animation = True


class MAYA_OT_time_slider_menu(bpy.types.Operator):
    """Maya's time slider right-click menu"""
    bl_idname = "maya.time_slider_menu"
    bl_label = "Time Slider Menu"

    @classmethod
    def poll(cls, context):
        return _is_timeline(context)

    def invoke(self, context, event):
        bpy.ops.wm.call_menu(name="MAYA_MT_time_slider")
        return {'FINISHED'}


class MAYA_OT_time_range_select(bpy.types.Operator):
    """Shift+drag on the time slider: select the keys in that frame range (Maya)"""
    bl_idname = "maya.time_range_select"
    bl_label = "Select Time Range"

    @classmethod
    def poll(cls, context):
        return _is_timeline(context)

    def invoke(self, context, event):
        try:
            bpy.ops.action.select_box('INVOKE_DEFAULT', axis_range=True, mode='SET')
        except (RuntimeError, TypeError):
            return {'PASS_THROUGH'}
        return {'FINISHED'}


class MAYA_OT_move_keys(bpy.types.Operator):
    """Middle-drag: move the selected keys (Maya Graph Editor / Dope Sheet)"""
    bl_idname = "maya.move_keys"
    bl_label = "Move Keys"

    @classmethod
    def poll(cls, context):
        area = context.area
        if area is None:
            return False
        if area.type == 'GRAPH_EDITOR':
            return area.ui_type == 'FCURVES'
        return area.type == 'DOPESHEET_EDITOR' and area.ui_type != 'TIMELINE'

    def invoke(self, context, event):
        try:
            if context.area.type == 'GRAPH_EDITOR':
                bpy.ops.transform.translate('INVOKE_DEFAULT', release_confirm=True)
            else:
                bpy.ops.transform.transform('INVOKE_DEFAULT', mode='TIME_TRANSLATE', release_confirm=True)
        except (RuntimeError, TypeError):
            return {'PASS_THROUGH'}
        return {'FINISHED'}


# (keymap, operator, key, value, modifiers) - registered by keymaps.py
ANIM_KEYS = (
    ("Dopesheet", "maya.time_slider_menu", 'RIGHTMOUSE', 'PRESS', {}),
    ("Dopesheet", "maya.time_range_select", 'LEFTMOUSE', 'CLICK_DRAG', {"shift": True}),
    ("Dopesheet", "maya.move_keys", 'MIDDLEMOUSE', 'CLICK_DRAG', {}),
    ("Graph Editor", "maya.move_keys", 'MIDDLEMOUSE', 'CLICK_DRAG', {}),
)


classes = (
    MAYA_OT_set_tangent,
    MAYA_MT_tangents,
    MAYA_MT_time_slider,
    MAYA_OT_time_slider_menu,
    MAYA_OT_time_range_select,
    MAYA_OT_move_keys,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.GRAPH_HT_header.append(_draw_graph_header)


def unregister():
    bpy.types.GRAPH_HT_header.remove(_draw_graph_header)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
