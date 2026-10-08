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


def gizmo_frame(context):
    """Where the transform gizmo is: (center, center_2d, handle length in world units,
    handle length in pixels, orientation type, axes matrix) or None."""
    region, rv3d = context.region, context.region_data
    space = context.space_data
    if region is None or rv3d is None or space is None or space.type != 'VIEW_3D':
        return None
    if not (space.show_gizmo and space.show_gizmo_tool):
        return None
    center = _pivot(context)
    if center is None:
        return None
    to2d = lambda co: view3d_utils.location_3d_to_region_2d(region, rv3d, co)
    c2 = to2d(center)
    right = rv3d.view_rotation @ Vector((1.0, 0.0, 0.0))
    r2 = to2d(center + right)
    if c2 is None or r2 is None:
        return None
    px_per_unit = max((r2 - c2).length, 1e-6)
    prefs = context.preferences
    size_px = prefs.view.gizmo_size * prefs.system.ui_scale
    orient, axes = _orientation(context, rv3d)
    return center, c2, size_px / px_per_unit, size_px, orient, axes


def gizmo_hit(context, event, kind, tolerance=HIT_PX):
    """Which handle is under the mouse: 'X'/'Y'/'Z', 'XY'/'YZ'/'XZ', 'VIEW', 'CENTER' or None."""
    frame = gizmo_frame(context)
    if frame is None:
        return None, None
    center, c2, length, size_px, orient, axes = frame
    region, rv3d = context.region, context.region_data
    to2d = lambda co: view3d_utils.location_3d_to_region_2d(region, rv3d, co)
    mouse = Vector((event.mouse_region_x, event.mouse_region_y))
    names = ("X", "Y", "Z")
    from_center = (mouse - c2).length

    if kind == 'ROTATE':
        if abs(from_center - size_px * 1.2) < tolerance:
            return 'VIEW', orient
        view_dir = rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))  # towards the viewer
        best, best_d = None, tolerance
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
    best, best_d = None, tolerance
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
        if p is not None and (p - mouse).length < tolerance:
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
        operator = getattr(bpy.ops.transform, op_name)
        try:
            operator('INVOKE_DEFAULT', release_confirm=True, **settings)
        except (RuntimeError, TypeError):
            # e.g. a stored orientation that no longer exists: fall back to a free transform
            operator('INVOKE_DEFAULT', release_confirm=True)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Yellow highlight of the picked handle (Maya draws the active handle in yellow)
# ---------------------------------------------------------------------------

HIGHLIGHT_COLOR = (1.0, 0.85, 0.0, 1.0)
_draw_handle = None
_shader = None


def _polyline_shader():
    global _shader
    if _shader is None:
        import gpu
        try:
            _shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        except (ValueError, SystemError):
            _shader = False
    return _shader


def _draw_lines(points, width, loop=False):
    import gpu
    from gpu_extras.batch import batch_for_shader
    shader = _polyline_shader()
    if not shader or len(points) < 2:
        return
    coords = []
    seq = list(points) + ([points[0]] if loop else [])
    for a, b in zip(seq, seq[1:]):
        coords += [a, b]
    batch = batch_for_shader(shader, 'LINES', {"pos": coords})
    region = bpy.context.region
    shader.bind()
    shader.uniform_float("viewportSize", (region.width, region.height))
    shader.uniform_float("lineWidth", width)
    shader.uniform_float("color", HIGHLIGHT_COLOR)
    gpu.state.depth_test_set('NONE')
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def _circle(center, u, v, radius, segments=48):
    pts = []
    for step in range(segments + 1):
        a = step * math.tau / segments
        offset = (u * math.cos(a) + v * math.sin(a)) * radius
        pts.append(center + offset)
    return pts


def _draw_highlight():
    context = bpy.context
    try:
        from .prefs import get_prefs
        prefs = get_prefs(context)
        if prefs is not None and not (prefs.use_mmb_transform and prefs.show_axis_highlight):
            return
        kind = active_tool_kind(context)
        if kind is None:
            return
        frame = gizmo_frame(context)
        if frame is None:
            return
        center, _c2, length, _size_px, _orient, axes = frame
        rv3d = context.region_data
        settings = last_axis_settings(context, kind) or {}
        picked = "".join(a for a, on in zip("XYZ", settings.get("constraint_axis", (False,) * 3)) if on)
        view_x = rv3d.view_rotation @ Vector((1.0, 0.0, 0.0))
        view_y = rv3d.view_rotation @ Vector((0.0, 1.0, 0.0))

        if kind == 'ROTATE':
            if settings.get("orient_type") == 'VIEW' and not picked:
                _draw_lines(_circle(center, view_x, view_y, length * 1.2), 4.0)
            elif len(picked) == 1:
                i = "XYZ".index(picked)
                u, v = axes.col[(i + 1) % 3], axes.col[(i + 2) % 3]
                _draw_lines(_circle(center, u, v, length), 5.0)
            return

        if not picked:
            # Free (center handle): a small yellow ring in the middle.
            _draw_lines(_circle(center, view_x, view_y, length * 0.16, 24), 3.0)
        elif len(picked) == 1:
            axis = axes.col["XYZ".index(picked)]
            _draw_lines([center + axis * length * 0.2, center + axis * length * 1.15], 6.0)
        else:  # plane handle
            i, j = ("XYZ".index(picked[0]), "XYZ".index(picked[1]))
            a, b = axes.col[i] * length, axes.col[j] * length
            mid = center + (a + b) * 0.33
            h = 0.09
            _draw_lines([mid + (a + b) * h, mid + (a - b) * h, mid - (a + b) * h, mid - (a - b) * h], 3.0, loop=True)
    except Exception:
        pass  # drawing must never break the viewport


def _redraw_viewports(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


class MAYA_OT_tool_key(bpy.types.Operator):
    """Maya Q / W / E / R: pick the tool; pressed again, put the middle-drag axis back to the center (free)"""
    bl_idname = "maya.tool_key"
    bl_label = "Select / Move / Rotate / Scale Tool"

    tool: bpy.props.StringProperty(default="builtin.move")

    def execute(self, context):
        kind = TOOL_KINDS.get(self.tool)
        already = active_tool_kind(context) == kind if kind else False
        if self.tool == "builtin.select_box":
            try:
                current = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
                already = current is not None and current.idname.startswith("builtin.select")
            except (AttributeError, TypeError):
                already = False
        if already:
            # Pressed again: back to the center handle (free move), like Maya.
            kinds = [kind] if kind else list(KINDS)
            for k in kinds:
                op = _last_transform_op(context, k)
                _picked[k] = ({}, op.as_pointer() if op else 0)
            _redraw_viewports(context)
            return {'FINISHED'}
        bpy.ops.wm.tool_set_by_id(name=self.tool, cycle=False)
        _redraw_viewports(context)
        return {'FINISHED'}


KIND_ITEMS = (
    ('TRANSLATE', "Move", ""),
    ('ROTATE', "Rotate", ""),
    ('RESIZE', "Scale", ""),
    ('AUTO', "Active Tool", "Use the active Move / Rotate / Scale tool"),
)


def _shift_extrude_or_duplicate(context):
    """Maya Shift Extrude / Shift Duplicate. Returns False if nothing was done."""
    from .prefs import get_prefs
    prefs = get_prefs(context)
    if context.mode == 'EDIT_MESH':
        if prefs is not None and not prefs.shift_extrude:
            return False
        bpy.ops.mesh.extrude_context()
        return True
    if context.mode == 'OBJECT':
        if prefs is not None and not prefs.shift_duplicate:
            return False
        bpy.ops.object.duplicate()
        return True
    return False


def _invoke_transform(kind, settings):
    operator = getattr(bpy.ops.transform, KINDS[kind][0])
    try:
        operator('INVOKE_DEFAULT', release_confirm=True, **settings)
    except (RuntimeError, TypeError):
        operator('INVOKE_DEFAULT', release_confirm=True)


class MAYA_OT_shift_gizmo_drag(bpy.types.Operator):
    """Shift + drag a manipulator handle: extrude components / duplicate objects along it (Maya)"""
    bl_idname = "maya.shift_gizmo_drag"
    bl_label = "Shift Drag Manipulator"

    kind: EnumProperty(items=KIND_ITEMS, default='TRANSLATE')

    def invoke(self, context, event):
        kind = active_tool_kind(context) if self.kind == 'AUTO' else self.kind
        if kind is None:
            return {'PASS_THROUGH'}
        # The drag event fires a few pixels after the press: allow for that.
        hit, orient = gizmo_hit(context, event, kind, tolerance=HIT_PX + 6)
        if hit is None:
            return {'PASS_THROUGH'}  # not on the manipulator: Shift box select etc.
        settings = _settings_for_hit(kind, hit, orient)
        _shift_extrude_or_duplicate(context)
        _invoke_transform(kind, settings)
        op = _last_transform_op(context, kind)
        _picked[kind] = (settings, op.as_pointer() if op else 0)
        return {'FINISHED'}


class MAYA_OT_mmb_axis_drag(bpy.types.Operator):
    """Shift + middle-drag: move along the axis you drag first (Maya)"""
    bl_idname = "maya.mmb_axis_drag"
    bl_label = "Shift Middle-drag (First Direction)"

    kind: EnumProperty(items=KIND_ITEMS, default='TRANSLATE')

    def invoke(self, context, event):
        region, rv3d = context.region, context.region_data
        center = _pivot(context)
        if region is None or rv3d is None or center is None:
            return {'PASS_THROUGH'}
        start_x = getattr(event, "mouse_prev_press_x", event.mouse_prev_x)
        start_y = getattr(event, "mouse_prev_press_y", event.mouse_prev_y)
        drag = Vector((event.mouse_x - start_x, event.mouse_y - start_y))
        orient, axes = _orientation(context, rv3d)
        settings = {}
        if drag.length > 0.5:
            c2 = view3d_utils.location_3d_to_region_2d(region, rv3d, center)
            best, best_score = None, -1.0
            for i, name in enumerate("XYZ"):
                p = view3d_utils.location_3d_to_region_2d(region, rv3d, center + axes.col[i])
                if c2 is None or p is None or (p - c2).length < 1e-6:
                    continue
                score = abs((p - c2).normalized().dot(drag.normalized()))
                if score > best_score:
                    best, best_score = name, score
            if best is not None:
                settings = _settings_for_hit(self.kind, best, orient)
        _invoke_transform(self.kind, settings)
        return {'FINISHED'}


def register():
    global _draw_handle
    bpy.utils.register_class(MAYA_OT_tool_key)
    if not bpy.app.background:
        _draw_handle = bpy.types.SpaceView3D.draw_handler_add(_draw_highlight, (), 'WINDOW', 'POST_VIEW')
    bpy.utils.register_class(MAYA_OT_gizmo_pick)
    bpy.utils.register_class(MAYA_OT_mmb_transform)
    bpy.utils.register_class(MAYA_OT_shift_gizmo_drag)
    bpy.utils.register_class(MAYA_OT_mmb_axis_drag)


def unregister():
    global _draw_handle, _shader
    if _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None
    _shader = None
    bpy.utils.unregister_class(MAYA_OT_tool_key)
    bpy.utils.unregister_class(MAYA_OT_mmb_axis_drag)
    bpy.utils.unregister_class(MAYA_OT_shift_gizmo_drag)
    bpy.utils.unregister_class(MAYA_OT_mmb_transform)
    bpy.utils.unregister_class(MAYA_OT_gizmo_pick)
    _picked.clear()
