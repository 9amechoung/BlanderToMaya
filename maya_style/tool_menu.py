"""Maya's tool settings marking menu (Ctrl+Shift+Right-click in the 3D viewport).

              [Symmetry >]
   [ ] Object               [ ] Component
   [x] World        o       [Snap >]
     [Axis >]               [x] Keep Spacing
              [Select >]
          Selection Constraints >
          Transform Constraints >
          [x] Shift Extrude
          [x] Shift Duplicate
          [ ] Preserve UVs
          [ ] Preserve Children
          [ ] Tweak Mode
          Move Options

Object / World / Component are the transform orientation (Local / Global /
Normal). Shift Extrude / Shift Duplicate: Shift + middle-drag extrudes
(edit mode) or duplicates (object mode) before moving.
"""

import bpy
from bpy.props import StringProperty

from .prefs import get_prefs


def _check_icon(on):
    return 'CHECKBOX_HLT' if on else 'CHECKBOX_DEHLT'


def _orientation_slot(context):
    return context.scene.transform_orientation_slots[0]


def _active_tool_id(context):
    try:
        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    except (AttributeError, TypeError):
        return ""
    return tool.idname if tool else ""


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class MAYA_OT_set_orientation(bpy.types.Operator):
    """Set the manipulator orientation (Maya: Object / World / Component)"""
    bl_idname = "maya.set_orientation"
    bl_label = "Set Orientation"
    bl_options = {'REGISTER', 'UNDO'}

    orientation: StringProperty(default='GLOBAL')

    def execute(self, context):
        try:
            _orientation_slot(context).type = self.orientation
        except TypeError:
            self.report({'WARNING'}, "Orientation not available: " + self.orientation)
            return {'CANCELLED'}
        return {'FINISHED'}


class MAYA_OT_toggle_keep_spacing(bpy.types.Operator):
    """Keep component spacing when snapping (off: every vertex snaps on its own)"""
    bl_idname = "maya.toggle_keep_spacing"
    bl_label = "Keep Spacing"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.scene.tool_settings
        individual = {'FACE_PROJECT', 'FACE_NEAREST'}
        if ts.snap_elements_individual:
            remaining = set(ts.snap_elements) - individual
            ts.snap_elements = remaining or {'INCREMENT'}
        else:
            ts.snap_elements = set(ts.snap_elements) | {'FACE_PROJECT'}
            ts.use_snap = True
        return {'FINISHED'}


class MAYA_OT_toggle_tweak_mode(bpy.types.Operator):
    """Tweak mode: click-drag moves whatever is under the mouse without selecting it first"""
    bl_idname = "maya.toggle_tweak_mode"
    bl_label = "Tweak Mode"

    def execute(self, context):
        tool = "builtin.move" if _active_tool_id(context) == "builtin.select" else "builtin.select"
        bpy.ops.wm.tool_set_by_id(name=tool)
        return {'FINISHED'}


class MAYA_OT_set_tool(bpy.types.Operator):
    """Switch the active tool"""
    bl_idname = "maya.set_tool"
    bl_label = "Set Tool"

    tool: StringProperty()

    def execute(self, context):
        bpy.ops.wm.tool_set_by_id(name=self.tool)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Sub menus
# ---------------------------------------------------------------------------

def _menu_col(layout):
    col = layout.column()
    col.emboss = 'PULLDOWN_MENU'
    return col


class MAYA_MT_tool_symmetry(bpy.types.Menu):
    bl_label = "Symmetry"

    def draw(self, context):
        lay = self.layout
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            lay.label(text="(select a mesh)")
            return
        lay.prop(obj, "use_mesh_mirror_x", text="Object X")
        lay.prop(obj, "use_mesh_mirror_y", text="Object Y")
        lay.prop(obj, "use_mesh_mirror_z", text="Object Z")
        lay.separator()
        lay.prop(obj.data, "use_mirror_topology", text="Topology")


class MAYA_MT_tool_snap(bpy.types.Menu):
    bl_label = "Snap"

    def draw(self, context):
        lay = self.layout
        ts = context.scene.tool_settings
        lay.prop(ts, "use_snap", text="Snapping On")
        lay.separator()
        on = ts.snap_elements if ts.use_snap else set()
        for element, text in (('GRID', "Snap to Grids (X)"), ('EDGE', "Snap to Curves / Edges (C)"),
                              ('VERTEX', "Snap to Points (V)"), ('FACE', "Snap to Surfaces")):
            active = element in on or (element == 'GRID' and 'INCREMENT' in on)
            lay.operator("maya.toggle_snap", text=text, icon=_check_icon(active)).element = element
        lay.separator()
        lay.prop(ts, "snap_target", text="Snap With")
        lay.prop(ts, "use_snap_align_rotation", text="Align Rotation to Target")


class MAYA_MT_tool_axis(bpy.types.Menu):
    bl_label = "Axis Orientation"

    def draw(self, context):
        lay = self.layout
        slot = _orientation_slot(context)
        for value, text in (('GLOBAL', "World"), ('LOCAL', "Object"), ('NORMAL', "Component"),
                            ('PARENT', "Parent"), ('GIMBAL', "Gimbal"), ('VIEW', "View (Camera)"),
                            ('CURSOR', "Custom (3D Cursor)")):
            lay.operator("maya.set_orientation", text=text,
                         icon=_check_icon(slot.type == value)).orientation = value


class MAYA_MT_tool_select(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        lay = self.layout
        current = _active_tool_id(context)
        for tool, text in (("builtin.select_box", "Select Tool"), ("builtin.select_lasso", "Lasso Tool"),
                           ("builtin.select_circle", "Paint Selection Tool"), ("builtin.select", "Tweak Tool"),
                           ("builtin.move", "Move Tool (W)"), ("builtin.rotate", "Rotate Tool (E)"),
                           ("builtin.scale", "Scale Tool (R)")):
            lay.operator("maya.set_tool", text=text, icon=_check_icon(current == tool)).tool = tool


class MAYA_MT_tool_selection_constraints(bpy.types.Menu):
    bl_label = "Selection Constraints"

    def draw(self, context):
        lay = self.layout
        if context.mode != 'EDIT_MESH':
            lay.label(text="(component mode only)")
            return
        if "select_edge_loop_multi" in dir(bpy.ops.mesh):  # renamed in newer Blender
            lay.operator("mesh.select_edge_loop_multi", text="Edge Loop")
            lay.operator("mesh.select_edge_ring_multi", text="Edge Ring")
        else:
            lay.operator("mesh.loop_multi_select", text="Edge Loop").ring = False
            lay.operator("mesh.loop_multi_select", text="Edge Ring").ring = True
        lay.operator("mesh.region_to_loop", text="Border")
        lay.operator("mesh.select_linked", text="Shell")
        lay.operator("mesh.select_similar", text="Similar")


class MAYA_MT_tool_transform_constraints(bpy.types.Menu):
    bl_label = "Transform Constraints"

    def draw(self, context):
        lay = self.layout
        ts = context.scene.tool_settings
        lay.operator("transform.edge_slide", text="Edge (Edge Slide)")
        lay.operator("transform.vert_slide", text="Vertex Slide")
        surface = ts.use_snap and 'FACE_PROJECT' in ts.snap_elements_individual
        lay.operator("maya.toggle_keep_spacing", text="Surface (Project on Faces)", icon=_check_icon(surface))


# ---------------------------------------------------------------------------
# The marking menu
# ---------------------------------------------------------------------------

class MAYA_MT_tool_settings_menu(bpy.types.Menu):
    bl_idname = "MAYA_MT_tool_settings_menu"
    bl_label = ""

    def draw(self, context):
        pie = self.layout.menu_pie()
        ts = context.scene.tool_settings
        orient = _orientation_slot(context).type
        prefs = get_prefs(context)

        def orientation(layout, text, value):
            layout.operator("maya.set_orientation", text=text, icon=_check_icon(orient == value)).orientation = value

        orientation(pie, "World", 'GLOBAL')                                       # W
        pie.menu("MAYA_MT_tool_snap", text="Snap  ▸")                          # E

        bottom = pie.column()                                                    # S
        # An operator button, not layout.menu(): a menu inside a pie column draws as plain text.
        bottom.operator("wm.call_menu", text="Select  ▸").name = "MAYA_MT_tool_select"
        bottom.separator()
        col = _menu_col(bottom.box())
        col.menu("MAYA_MT_tool_selection_constraints", text="Selection Constraints  ▸")
        col.menu("MAYA_MT_tool_transform_constraints", text="Transform Constraints  ▸")
        col.separator()
        if prefs is not None:
            col.prop(prefs, "shift_extrude", text="Shift Extrude")
            col.prop(prefs, "shift_duplicate", text="Shift Duplicate")
            col.separator()
        col.prop(ts, "use_transform_correct_face_attributes", text="Preserve UVs")
        col.prop(ts, "use_transform_skip_children", text="Preserve Children")
        col.operator("maya.toggle_tweak_mode", text="Tweak Mode",
                     icon=_check_icon(_active_tool_id(context) == "builtin.select"))
        col.separator()
        col.operator("maya.show_attributes", text="Move Options").tab = 'TOOL'

        pie.menu("MAYA_MT_tool_symmetry", text="Symmetry  ▸")                  # N
        orientation(pie, "Object", 'LOCAL')                                       # NW
        orientation(pie, "Component", 'NORMAL')                                   # NE
        pie.menu("MAYA_MT_tool_axis", text="Axis  ▸")                          # SW
        pie.operator("maya.toggle_keep_spacing", text="Keep Spacing",             # SE
                     icon=_check_icon(not ts.snap_elements_individual))


classes = (
    MAYA_OT_set_orientation,
    MAYA_OT_toggle_keep_spacing,
    MAYA_OT_toggle_tweak_mode,
    MAYA_OT_set_tool,
    MAYA_MT_tool_symmetry,
    MAYA_MT_tool_snap,
    MAYA_MT_tool_axis,
    MAYA_MT_tool_select,
    MAYA_MT_tool_selection_constraints,
    MAYA_MT_tool_transform_constraints,
    MAYA_MT_tool_settings_menu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
