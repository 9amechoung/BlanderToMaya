"""Box / lasso selection that also picks what is behind (Maya's default) - without X-ray.

Blender's own box / lasso selection only reaches hidden objects and back
vertices / edges / faces when X-ray is on. This draws its own box (or lasso)
and decides what is inside purely from screen positions, so everything under
the box is selected while the viewport keeps looking solid.

Object mode and mesh component mode are handled here; other modes fall back to
Blender's own selection.
"""

import bmesh
import bpy
from bpy.props import EnumProperty

from .prefs import get_prefs

_draw_handle = None
_drawing = {}


# ---------------------------------------------------------------------------
# Geometry helpers (plain Python: some Blender builds ship without numpy)
# ---------------------------------------------------------------------------

def _projector(region, rv3d, matrix_world):
    """Return a function: local coordinate -> region pixel (x, y), or None when behind the view."""
    m = rv3d.perspective_matrix @ matrix_world
    r0, r1, r3 = m[0], m[1], m[3]
    half_w, half_h = region.width * 0.5, region.height * 0.5

    def project(co):
        x, y, z = co
        w = r3[0] * x + r3[1] * y + r3[2] * z + r3[3]
        if w <= 1e-6:
            return None
        return ((r0[0] * x + r0[1] * y + r0[2] * z + r0[3]) / w * half_w + half_w,
                (r1[0] * x + r1[1] * y + r1[2] * z + r1[3]) / w * half_h + half_h)
    return project


def _in_poly(p, poly):
    """Even-odd point in polygon test."""
    px, py = p
    inside = False
    xb, yb = poly[-1]
    for xa, ya in poly:
        if (ya > py) != (yb > py) and px < xa + (py - ya) * (xb - xa) / (yb - ya):
            inside = not inside
        xb, yb = xa, ya
    return inside


def _point_hit(p, shape):
    if p is None:
        return False
    if shape[0] == 'BOX':
        x0, y0, x1, y1 = shape[1]
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    return _in_poly(p, shape[1])


def _orient(p, q, r):
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])


def _segments_cross(a, b, c, d):
    return _orient(a, b, c) * _orient(a, b, d) < 0 and _orient(c, d, a) * _orient(c, d, b) < 0


def _edge_hit(a, b, shape):
    """An edge is hit when an end is inside the shape or it crosses the shape's border."""
    if a is None or b is None:
        return False
    if _point_hit(a, shape) or _point_hit(b, shape):
        return True
    if shape[0] == 'BOX':
        x0, y0, x1, y1 = shape[1]
        if max(a[0], b[0]) < x0 or min(a[0], b[0]) > x1 or max(a[1], b[1]) < y0 or min(a[1], b[1]) > y1:
            return False
        border = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    else:
        border = shape[1]
    prev = border[-1]
    for cur in border:
        if _segments_cross(a, b, prev, cur):
            return True
        prev = cur
    return False


def _combine(old, hit, mode):
    if mode == 'SET':
        return hit
    if mode == 'ADD':
        return old or hit
    if mode == 'SUB':
        return old and not hit
    if mode == 'XOR':
        return old != hit
    return old and hit  # AND


# ---------------------------------------------------------------------------
# Selecting
# ---------------------------------------------------------------------------

def _select_mesh_components(context, region, rv3d, shape, mode):
    vert_mode, edge_mode, face_mode = context.tool_settings.mesh_select_mode
    objects = list(getattr(context, "objects_in_mode_unique_data", None) or [context.edit_object])
    for obj in objects:
        if obj is None or obj.type != 'MESH':
            continue
        bm = bmesh.from_edit_mesh(obj.data)
        project = _projector(region, rv3d, obj.matrix_world)
        pts = {v: (None if v.hide else project(v.co)) for v in bm.verts}

        if vert_mode:
            for v in bm.verts:
                if not v.hide:
                    v.select_set(_combine(v.select, _point_hit(pts[v], shape), mode))
        elif edge_mode:
            new = [(e, _combine(e.select, not e.hide and _edge_hit(pts[e.verts[0]], pts[e.verts[1]], shape), mode))
                   for e in bm.edges]
            for e, _sel in new:
                e.select_set(False)
            for e, sel in new:
                if sel:
                    e.select_set(True)
        elif face_mode:
            new = [(f, _combine(f.select, not f.hide and _point_hit(project(f.calc_center_median()), shape), mode))
                   for f in bm.faces]
            for f, _sel in new:
                f.select_set(False)
            for f, sel in new:
                if sel:
                    f.select_set(True)
        bm.select_flush_mode()
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)


def _object_hit(depsgraph, region, rv3d, obj, shape):
    project = _projector(region, rv3d, obj.matrix_world)
    if obj.type == 'MESH':
        mesh = obj.evaluated_get(depsgraph).data
        pts = [project(v.co) for v in mesh.vertices]
        if any(_point_hit(p, shape) for p in pts):
            return True
        if any(_edge_hit(pts[a], pts[b], shape) for a, b in (e.vertices for e in mesh.edges)):
            return True
    # Lights, cameras, empties, or a box drawn entirely inside a big face: use the bounding box.
    corners = [project(c) for c in obj.bound_box]
    if any(_point_hit(p, shape) for p in corners):
        return True
    corners = [p for p in corners if p is not None]
    if shape[0] == 'BOX' and corners and obj.type != 'MESH':
        x0, y0, x1, y1 = shape[1]
        return (min(p[0] for p in corners) <= x1 and max(p[0] for p in corners) >= x0
                and min(p[1] for p in corners) <= y1 and max(p[1] for p in corners) >= y0)
    return False


def _select_objects(context, region, rv3d, shape, mode):
    depsgraph = context.evaluated_depsgraph_get()
    candidates = [o for o in context.visible_objects if not o.hide_select]
    for obj in candidates:
        old = obj.select_get()
        new = _combine(old, _object_hit(depsgraph, region, rv3d, obj, shape), mode)
        if new != old:
            obj.select_set(new)
    active = context.view_layer.objects.active
    if active is None or not active.select_get():
        chosen = [o for o in candidates if o.select_get()]
        if chosen:
            context.view_layer.objects.active = chosen[0]


# ---------------------------------------------------------------------------
# Drawing the box / lasso (no X-ray, just a white outline)
# ---------------------------------------------------------------------------

def _draw_outline():
    pts = _drawing.get("points")
    if not pts or bpy.context.region != _drawing.get("region"):
        return
    try:
        import gpu
        from gpu_extras.batch import batch_for_shader
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": [(x, y) for x, y in pts]})
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float("color", (1.0, 1.0, 1.0, 0.9))
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

def _handled_here(context):
    if context.mode == 'OBJECT':
        return True
    return context.mode == 'EDIT_MESH'


class MAYA_OT_select_through(bpy.types.Operator):
    """Box / lasso select that also selects hidden objects and back components, like Maya (no X-ray)"""
    bl_idname = "maya.select_through"
    bl_label = "Select (Through)"
    bl_options = {'REGISTER', 'UNDO'}

    gesture: EnumProperty(items=(('BOX', "Box", ""), ('LASSO', "Lasso", "")), default='BOX')
    mode: EnumProperty(items=(('SET', "Set", ""), ('ADD', "Add", ""), ('SUB', "Subtract", ""),
                              ('XOR', "Toggle", ""), ('AND', "Intersect", "")), default='SET')

    def _fallback(self):
        name = "select_box" if self.gesture == 'BOX' else "select_lasso"
        getattr(bpy.ops.view3d, name)('INVOKE_DEFAULT', mode=self.mode)
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = get_prefs(context)
        space = context.space_data
        if (prefs is not None and not prefs.use_select_through) or space is None or space.type != 'VIEW_3D' \
                or context.region_data is None or not _handled_here(context):
            return self._fallback()
        # The drag event arrives a few pixels after the press: start the box where the button went down.
        start = (event.mouse_prev_press_x - context.region.x, event.mouse_prev_press_y - context.region.y)
        self._start = start
        self._path = [start, (event.mouse_region_x, event.mouse_region_y)]
        self._update_drawing(context)
        global _draw_handle
        if _draw_handle is None:
            _draw_handle = bpy.types.SpaceView3D.draw_handler_add(_draw_outline, (), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _rect(self):
        (ax, ay), (bx, by) = self._start, self._path[-1]
        return (min(ax, bx), min(ay, by), max(ax, bx), max(ay, by))

    def _update_drawing(self, context):
        if self.gesture == 'BOX':
            x0, y0, x1, y1 = self._rect()
            _drawing["points"] = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        else:
            _drawing["points"] = list(self._path)
        _drawing["region"] = context.region
        context.area.tag_redraw()

    def _finish_drawing(self, context):
        _drawing.clear()
        context.area.tag_redraw()

    def modal(self, context, event):
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            point = (event.mouse_region_x, event.mouse_region_y)
            if self.gesture == 'BOX':
                self._path[-1] = point
            else:
                self._path.append(point)
            self._update_drawing(context)
            return {'RUNNING_MODAL'}
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self._finish_drawing(context)
            shape = ('BOX', self._rect()) if self.gesture == 'BOX' else ('LASSO', [tuple(p) for p in self._path])
            region, rv3d = context.region, context.region_data
            if context.mode == 'EDIT_MESH':
                _select_mesh_components(context, region, rv3d, shape, self.mode)
            else:
                _select_objects(context, region, rv3d, shape, self.mode)
            return {'FINISHED'}
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self._finish_drawing(context)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}


classes = (MAYA_OT_select_through,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    global _draw_handle
    if _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
