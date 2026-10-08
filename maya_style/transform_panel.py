"""Local and world (global) transform values, both editable.

Local = relative to the parent (what the Channel Box shows: Translate / Rotate / Scale).
World = where the object really is in the scene, whatever its parents do.
In component mode the center of the selected vertices is shown in both spaces too.
"""

import bmesh
import bpy
from bpy.props import FloatVectorProperty
from mathutils import Euler, Matrix, Vector


# ---------------------------------------------------------------------------
# World-space object values (computed from matrix_world, written back to it)
# ---------------------------------------------------------------------------

def _decompose(obj):
    return obj.matrix_world.decompose()


def _get_world_location(self):
    return tuple(_decompose(self)[0])


def _set_world_location(self, value):
    _loc, rot, scale = _decompose(self)
    self.matrix_world = Matrix.LocRotScale(Vector(value), rot, scale)


def _get_world_rotation(self):
    return tuple(_decompose(self)[1].to_euler('XYZ'))


def _set_world_rotation(self, value):
    loc, _rot, scale = _decompose(self)
    self.matrix_world = Matrix.LocRotScale(loc, Euler(value, 'XYZ').to_quaternion(), scale)


def _get_world_scale(self):
    return tuple(_decompose(self)[2])


def _set_world_scale(self, value):
    loc, rot, _scale = _decompose(self)
    self.matrix_world = Matrix.LocRotScale(loc, rot, Vector(value))


# ---------------------------------------------------------------------------
# Selected components (center of the selected vertices), in edit mode
# ---------------------------------------------------------------------------

def _edit_bmesh(obj):
    if obj.type != 'MESH' or obj.mode != 'EDIT':
        return None
    return bmesh.from_edit_mesh(obj.data)


def _selected_verts(bm):
    return [v for v in bm.verts if v.select]


def _median(verts):
    return sum((v.co for v in verts), Vector()) / len(verts)


def _get_component_local(self):
    bm = _edit_bmesh(self)
    verts = _selected_verts(bm) if bm else []
    return tuple(_median(verts)) if verts else (0.0, 0.0, 0.0)


def _move_components(obj, new_local):
    bm = _edit_bmesh(obj)
    verts = _selected_verts(bm) if bm else []
    if not verts:
        return
    delta = Vector(new_local) - _median(verts)
    for v in verts:
        v.co += delta
    bmesh.update_edit_mesh(obj.data)


def _set_component_local(self, value):
    _move_components(self, value)


def _get_component_world(self):
    bm = _edit_bmesh(self)
    verts = _selected_verts(bm) if bm else []
    return tuple(self.matrix_world @ _median(verts)) if verts else (0.0, 0.0, 0.0)


def _set_component_world(self, value):
    _move_components(self, self.matrix_world.inverted() @ Vector(value))


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def _row(col, data, prop, label, index):
    row = col.row(align=True)
    split = row.split(factor=0.45, align=True)
    split.alignment = 'RIGHT'
    split.label(text=label)
    split.prop(data, prop, index=index, text="")


def draw_world_space(layout, obj):
    """World (global) Translate / Rotate / Scale, editable."""
    box = layout.box()
    box.label(text="World Space (Global)", icon='WORLD')
    if obj.parent is None:
        box.label(text="No parent: same as Local")
    col = box.column(align=True)
    for i, axis in enumerate("XYZ"):
        _row(col, obj, "maya_world_location", "Translate " + axis, i)
    col.separator()
    for i, axis in enumerate("XYZ"):
        _row(col, obj, "maya_world_rotation", "Rotate " + axis, i)
    col.separator()
    for i, axis in enumerate("XYZ"):
        _row(col, obj, "maya_world_scale", "Scale " + axis, i)


def draw_components(layout, obj):
    """Center of the selected vertices, local and world, editable."""
    bm = _edit_bmesh(obj)
    if bm is None:
        return
    count = len(_selected_verts(bm))
    box = layout.box()
    box.label(text="Selected Components (%d vertices, center)" % count, icon='VERTEXSEL')
    if not count:
        return
    col = box.column(align=True)
    col.label(text="Local (Object Space)")
    for i, axis in enumerate("XYZ"):
        _row(col, obj, "maya_component_local", axis, i)
    col.separator()
    col.label(text="World Space")
    for i, axis in enumerate("XYZ"):
        _row(col, obj, "maya_component_world", axis, i)


class MAYA_PT_world_space(bpy.types.Panel):
    bl_idname = "MAYA_PT_world_space"
    bl_label = "Local / World"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Channel Box"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        obj = context.active_object
        self.layout.label(text="Local values are in the Channel Box above.", icon='INFO')
        draw_components(self.layout, obj)
        draw_world_space(self.layout, obj)


def register():
    bpy.types.Object.maya_world_location = FloatVectorProperty(
        name="World Translate", description="Position in the world (ignores parents). Editable",
        subtype='TRANSLATION', unit='LENGTH', size=3, get=_get_world_location, set=_set_world_location)
    bpy.types.Object.maya_world_rotation = FloatVectorProperty(
        name="World Rotate", description="Rotation in the world (XYZ Euler, ignores parents). Editable",
        subtype='EULER', unit='ROTATION', size=3, get=_get_world_rotation, set=_set_world_rotation)
    bpy.types.Object.maya_world_scale = FloatVectorProperty(
        name="World Scale", description="Scale in the world (ignores parents). Editable",
        subtype='XYZ', size=3, get=_get_world_scale, set=_set_world_scale)
    bpy.types.Object.maya_component_local = FloatVectorProperty(
        name="Components (Local)", description="Center of the selected vertices in object space. Editable",
        subtype='TRANSLATION', unit='LENGTH', size=3, get=_get_component_local, set=_set_component_local)
    bpy.types.Object.maya_component_world = FloatVectorProperty(
        name="Components (World)", description="Center of the selected vertices in world space. Editable",
        subtype='TRANSLATION', unit='LENGTH', size=3, get=_get_component_world, set=_set_component_world)
    bpy.utils.register_class(MAYA_PT_world_space)


def unregister():
    bpy.utils.unregister_class(MAYA_PT_world_space)
    for name in ("maya_world_location", "maya_world_rotation", "maya_world_scale",
                 "maya_component_local", "maya_component_world"):
        delattr(bpy.types.Object, name)
