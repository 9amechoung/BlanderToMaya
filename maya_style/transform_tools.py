"""Maya-style middle mouse drag for the Move / Rotate / Scale tools.

In Maya you click an axis handle on the manipulator (it turns yellow) and
then middle-drag anywhere in the viewport to move along that axis only.

Blender's gizmo ignores a plain click (it only reacts to a drag), so a click
on an arrow / ring is detected here by projecting the gizmo to the screen.
Dragging a handle also counts: the transform it runs records its axis.
Middle-dragging repeats a transform with the picked axis.
"""

import math

import bpy
from bpy.props import EnumProperty
from bpy_extras import view3d_utils
from mathutils import Matrix, Vector

# tool kind -> (transform operator, its RNA id name)
KINDS = {
    'TRANSLATE': ("translate", "TRANSFORM_OT_translate"),
    'ROTATE': ("rotate", "TRANSFORM_OT_rotate"),
    'RESIZE': ("resize", "TRANSFORM_OT_resize"),
}

TOOL_KEYMAPS = (
    ("3D View Tool: Move", 'TRANSLATE'),
    ("3D View Tool: Rotate", 'ROTATE'),
    ("3D View Tool: Scale", 'RESIZE'),
)

TOOL_KINDS = {
    "builtin.move": 'TRANSLATE',
    "builtin.rotate": 'ROTATE',
    "builtin.scale": 'RESIZE',
}


# kind -> (settings, pointer of the newest transform operator when the axis was picked)
_picked = {}


def _last_transform_op(context, kind):
    idname = KINDS[kind][1]
    for op in reversed(context.window_manager.operators):
        if op.bl_idname == idname:
            return op
    return None


def last_axis_settings(context, kind):
    """Axis to use for a middle-drag: the last picked gizmo handle (click or drag)."""
    op = _last_transform_op(context, kind)
    op_ptr = op.as_pointer() if op is not None else 0
    picked = _picked.get(kind)
    if picked is not None and picked[1] == op_ptr:
        # No transform of this kind ran since the click: the click wins.
        return picked[0]
    if op is None:
        return None
    props = op.properties
    settings = {
        "constraint_axis": tuple(props.constraint_axis),
        "orient_type": props.orient_type,
    }
    if kind == 'ROTATE':
        settings["orient_axis"] = props.orient_axis
    return settings


# ---------------------------------------------------------------------------
# Gizmo hit test (where are the arrows / rings on screen?)
# ---------------------------------------------------------------------------

HIT_PX = 9  # how close (pixels) a click must be to a handle


def _pivot(context):
    ts = context.scene.tool_settings
    if ts.transform_pivot_point == 'CURSOR':
        return context.scene.cursor.location.copy()
    obj = context.active_object
    if context.mode == 'EDIT_MESH' and obj is not None:
        import bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        points = [obj.matrix_world @ v.co for v in bm.verts if v.select]
    elif context.mode == 'OBJECT':
        if ts.transform_pivot_point == 'ACTIVE_ELEMENT' and obj is not None:
            return obj.matrix_world.translation.copy()
        points = [o.matrix_world.translation for o in context.selected_objects]
    else:
        points = [obj.matrix_world.translation] if obj is not None else []
    if not points:
        return None
    if ts.transform_pivot_point == 'BOUNDING_BOX_CENTER':
        lo = Vector([min(p[i] for p in points) for i in range(3)])
        hi = Vector([max(p[i] for p in points) for i in range(3)])
        return (lo + hi) / 2
    return sum(points, Vector()) / len(points)


def _orientation(context, rv3d):
    """(orient_type, 3x3 matrix whose columns are the gizmo X/Y/Z axes)."""
    slot = context.scene.transform_orientation_slots[0]
    orient = slot.type
    obj = context.active_object
    if orient == 'GLOBAL':
        return orient, Matrix.Identity(3)
    if orient == 'VIEW':
        return orient, rv3d.view_rotation.to_matrix()
    if orient == 'CURSOR':
        return orient, context.scene.cursor.matrix.to_3x3().normalized()
    if slot.custom_orientation is not None:
        return orient, slot.custom_orientation.matrix.copy()
    if obj is not None:  # LOCAL, NORMAL, GIMBAL, PARENT: close enough to local
        return orient, obj.matrix_world.to_3x3().normalized()
    return orient, Matrix.Identity(3)


def _dist_to_segment(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length


def gizmo_hit(context, event, kind):
    """Which handle is under the mouse: 'X'/'Y'/'Z', 'XY'/'YZ'/'XZ', 'VIEW', 'CENTER' or None."""
    region, rv3d = context.region, context.region_data
    space = context.space_data
    if region is None or rv3d is None or not (space.show_gizmo and space.show_gizmo_tool):
        return None, None
    center = _pivot(context)
    if center is None:
        return None, None
    to2d = lambda co: view3d_utils.location_3d_to_region_2d(region, rv3d, co)
    c2 = to2d(center)
    if c2 is None:
        return None, None
    mouse = Vector((event.mouse_region_x, event.mouse_region_y))
    right = rv3d.view_rotation @ Vector((1.0, 0.0, 0.0))
    r2 = to2d(center + right)
    if r2 is None:
        return None, None
    px_per_unit = max((r2 - c2).length, 1e-6)
    prefs = context.preferences
    size_px = prefs.view.gizmo_size * prefs.system.ui_scale
    length = size_px / px_per_unit  # gizmo handle length in world units
    orient, axes = _orientation(context, rv3d)
    names = ("X", "Y", "Z")
    from_center = (mouse - c2).length

    if kind == 'ROTATE':
        if abs(from_center - size_px * 1.2) < HIT_PX:
            return 'VIEW', orient
        view_dir = rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))  # towards the viewer
        best, best_d = None, HIT_PX
        for i, name in enumerate(names):
            axis = axes.col[i]
            u = axes.col[(i + 1) % 3]
            v = axes.col[(i + 2) % 3]
            for step in range(72):
                a = step * math.tau / 72
                offset = (u * math.cos(a) + v * math.sin(a)) * length
                if offset.dot(view_dir) < -0.05 * length:
                    continue  # back half of the ring is hidden
                p = to2d(center + offset)
                if p is not None and (p - mouse).length < best_d:
                    best, best_d = name, (p - mouse).length
        return best, orient

    if from_center < 12:
        return 'CENTER', orient
    best, best_d = None, HIT_PX
    for i, name in enumerate(names):
        tip = to2d(center + axes.col[i] * length * 1.25)
        if tip is None:
            continue
        start = c2 + (tip - c2) * 0.2
        d = _dist_to_segment(mouse, start, tip)
        if d < best_d:
            best, best_d = name, d
    if best is not None:
        return best, orient
    # Plane handles: small squares between two axes, about 1/3 out
    for i, j, name in ((0, 1, "XY"), (1, 2, "YZ"), (0, 2, "XZ")):
        p = to2d(center + (axes.col[i] + axes.col[j]) * length * 0.33)
        if p is not None and (p - mouse).length < HIT_PX:
            return name, orient
    return None, orient


def _settings_for_hit(kind, hit, orient):
    if hit in (None, 'CENTER'):
        return {}
    if kind == 'ROTATE':
        if hit == 'VIEW':
            return {"orient_axis": 'Z', "orient_type": 'VIEW', "constraint_axis": (False, False, False)}
        return {"orient_axis": hit, "orient_type": orient,
                "constraint_axis": tuple(a == hit for a in "XYZ")}
    return {"orient_type": orient, "constraint_axis": tuple(a in hit for a in "XYZ")}


class MAYA_OT_gizmo_pick(bpy.types.Operator):
    """Click a gizmo handle to pick its axis for middle-drag (like Maya's yellow handle)"""
    bl_idname = "maya.gizmo_pick"
    bl_label = "Pick Gizmo Axis"

    kind: EnumProperty(
        items=(
            ('TRANSLATE', "Move", ""),
            ('ROTATE', "Rotate", ""),
            ('RESIZE', "Scale", ""),
        ),
        default='TRANSLATE',
    )

    def invoke(self, context, event):
        hit, orient = gizmo_hit(context, event, self.kind)
        if hit is None:
            return {'PASS_THROUGH'}  # not on the gizmo: normal click select
        op = _last_transform_op(context, self.kind)
        _picked[self.kind] = (_settings_for_hit(self.kind, hit, orient), op.as_pointer() if op else 0)
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}


def axis_label(settings, kind):
    if not settings:
        return "Free"
    axes = "".join(a for a, on in zip("XYZ", settings["constraint_axis"]) if on)
    if kind == 'ROTATE' and not axes:
        axes = settings.get("orient_axis", "")
        if settings["orient_type"] == 'VIEW':
            return "View"
    if not axes:
        return "Free"
    if len(axes) == 2:  # plane handle
        return axes + " plane"
    return axes


def active_tool_kind(context):
    try:
        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    except (AttributeError, TypeError):
        return None
    return TOOL_KINDS.get(tool.idname) if tool else None


class MAYA_OT_mmb_transform(bpy.types.Operator):
    """Middle-drag to move / rotate / scale along the last picked gizmo axis (like Maya)"""
    bl_idname = "maya.mmb_transform"
    bl_label = "Middle-drag Transform"

    kind: EnumProperty(
        items=(
            ('TRANSLATE', "Move", ""),
            ('ROTATE', "Rotate", ""),
            ('RESIZE', "Scale", ""),
        ),
        default='TRANSLATE',
    )

    def invoke(self, context, event):
        op_name, _idname = KINDS[self.kind]
        settings = last_axis_settings(context, self.kind) or {}
        if event.shift:
            # Maya: Shift + drag extrudes components / duplicates objects first.
            from .prefs import get_prefs
            prefs = get_prefs(context)
            if context.mode == 'EDIT_MESH' and (prefs is None or prefs.shift_extrude):
                bpy.ops.mesh.extrude_context()
            elif context.mode == 'OBJECT' and (prefs is None or prefs.shift_duplicate):
                bpy.ops.object.duplicate()
        operator = getattr(bpy.ops.transform, op_name)
        try:
            operator('INVOKE_DEFAULT', release_confirm=True, **settings)
        except (RuntimeError, TypeError):
            # e.g. a stored orientation that no longer exists: fall back to a free transform
            operator('INVOKE_DEFAULT', release_confirm=True)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MAYA_OT_gizmo_pick)
    bpy.utils.register_class(MAYA_OT_mmb_transform)


def unregister():
    bpy.utils.unregister_class(MAYA_OT_mmb_transform)
    bpy.utils.unregister_class(MAYA_OT_gizmo_pick)
    _picked.clear()
