"""Maya UV Editor: UV Toolkit, marking menus, texture borders, checker, texel density.

- UV > UV Editor (or the right-click menu) opens the UV Editor in its own window with
  the UV Toolkit on the right, like Maya
- UV Toolkit (sidebar tab): Select, Transform (rotate 90 / flip / align), Create,
  Cut and Sew, Unfold, Arrange and Layout (layout / stack / normalize), Texel Density,
  Display (checker, distortion, shaded, texture borders)
- In the UV Editor: hold Right-click for UV / Edge / Face / UV Shell, Shift+Right-click
  for the UV tools, Ctrl+Right-click to convert the selection, middle-drag to move /
  rotate / scale with the active tool, hold X / V to snap to the grid / to UVs
- Texture borders: shell borders are drawn thick, like Maya
- Unfold keeps each shell where it was (Blender's Unwrap would re-pack everything into 0-1)
"""

import math

import bmesh
import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from mathutils import Vector

CHECKER_NAME = "Maya UV Checker"
EPS = 1e-5


# ---------------------------------------------------------------------------
# UV selection helpers (Blender 4.x: BMLoopUV.select, Blender 5: BMLoop.uv_select_vert)
# ---------------------------------------------------------------------------

def _sync(context):
    return context.scene.tool_settings.use_uv_select_sync


def edit_meshes(context):
    objs = getattr(context, "objects_in_mode_unique_data", None) or [context.edit_object]
    result = []
    for obj in objs:
        if obj is None or obj.type != 'MESH' or obj.mode != 'EDIT':
            continue
        bm = bmesh.from_edit_mesh(obj.data)
        uv = bm.loops.layers.uv.active
        if uv is not None:
            result.append((obj, bm, uv))
    return result


def face_visible(face, sync):
    """Is this face shown in the UV Editor? (without sync only the selected faces are)"""
    return not face.hide and (sync or face.select)


def loop_selected(loop, uv, sync):
    if sync:
        return loop.vert.select
    if hasattr(loop, "uv_select_vert"):
        return loop.uv_select_vert
    return loop[uv].select


def selected_loops(bm, uv, sync):
    return [l for f in bm.faces if face_visible(f, sync) for l in f.loops if loop_selected(l, uv, sync)]


def loop_edge_selected(loop, uv, sync):
    if sync:
        return loop.edge.select
    if hasattr(loop, "uv_select_edge"):
        return loop.uv_select_edge
    return loop[uv].select_edge


def _same(a, b):
    return abs(a.x - b.x) < EPS and abs(a.y - b.y) < EPS


def _uv_connected(f, l, uv):
    """The face on the other side of loop l's edge, if the UVs are connected there (same shell).
    A seam counts as cut, like Maya's UV borders."""
    if l.edge.seam:
        return None
    for other in l.edge.link_loops:
        if other is l or other.face is f:
            continue
        # The neighbor runs the edge the other way: l.uv == other.next.uv and l.next.uv == other.uv
        # (faces that only touch mirrored are separate shells, as in Blender's own island test)
        if _same(l[uv].uv, other.link_loop_next[uv].uv) and _same(l.link_loop_next[uv].uv, other[uv].uv):
            return other.face
    return None


def islands(bm, uv, faces):
    """Group these faces into UV shells (connected in UV space)."""
    pool = set(faces)
    result = []
    while pool:
        seed = pool.pop()
        island = [seed]
        stack = [seed]
        while stack:
            f = stack.pop()
            for l in f.loops:
                g = _uv_connected(f, l, uv)
                if g is not None and g in pool:
                    pool.discard(g)
                    island.append(g)
                    stack.append(g)
        result.append(island)
    return result


def selected_shells(bm, uv, sync):
    """Whole UV shells that contain some of the selection (Maya shell tools work on whole shells)."""
    visible = [f for f in bm.faces if face_visible(f, sync)]
    touched = {f for f in visible if any(loop_selected(l, uv, sync) for l in f.loops)}
    return [isl for isl in islands(bm, uv, visible) if touched.intersection(isl)]


def _bounds(loops, uv):
    us = [l[uv].uv.x for l in loops]
    vs = [l[uv].uv.y for l in loops]
    return min(us), min(vs), max(us), max(vs)


def _center(loops, uv):
    u0, v0, u1, v1 = _bounds(loops, uv)
    return Vector(((u0 + u1) / 2, (v0 + v1) / 2))


def _shell_loops(shell):
    return [l for f in shell for l in f.loops]


def _update(objs):
    for obj, _bm, _uv in objs:
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    _borders_dirty()


# ---------------------------------------------------------------------------
# Operators: transform / align / stack / normalize / texel density / unfold
# ---------------------------------------------------------------------------

class _UVOperator:
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'


class MAYA_OT_uv_transform(_UVOperator, bpy.types.Operator):
    """Rotate / flip the selected UVs around their center (Maya UV Toolkit > Transform)"""
    bl_idname = "maya.uv_transform"
    bl_label = "Transform UVs"

    mode: EnumProperty(items=(
        ('ROT_CW', "Rotate 90° Clockwise", ""),
        ('ROT_CCW', "Rotate 90° Counterclockwise", ""),
        ('FLIP_U', "Flip U (Horizontal)", ""),
        ('FLIP_V', "Flip V (Vertical)", ""),
    ))
    per_shell: BoolProperty(name="Each Shell", description="Use each shell's own center", default=False)

    def execute(self, context):
        sync = _sync(context)
        objs = edit_meshes(context)
        groups = []
        for _obj, bm, uv in objs:
            if self.per_shell:
                groups += [(uv, _shell_loops(s)) for s in selected_shells(bm, uv, sync)]
            else:
                loops = selected_loops(bm, uv, sync)
                if loops:
                    groups.append((uv, loops))
        if not groups:
            self.report({'WARNING'}, "Select some UVs first")
            return {'CANCELLED'}
        if not self.per_shell:  # one center for the whole selection, across objects
            pts = [l[uv].uv for uv, loops in groups for l in loops]
            center = Vector(((min(p.x for p in pts) + max(p.x for p in pts)) / 2,
                             (min(p.y for p in pts) + max(p.y for p in pts)) / 2))
        for uv, loops in groups:
            c = _center(loops, uv) if self.per_shell else center
            for l in loops:
                d = l[uv].uv - c
                if self.mode == 'ROT_CW':
                    d = Vector((d.y, -d.x))
                elif self.mode == 'ROT_CCW':
                    d = Vector((-d.y, d.x))
                elif self.mode == 'FLIP_U':
                    d.x = -d.x
                else:
                    d.y = -d.y
                l[uv].uv = c + d
        _update(objs)
        return {'FINISHED'}


class MAYA_OT_uv_align(_UVOperator, bpy.types.Operator):
    """Line up the selected UVs (Maya UV Toolkit > Align and Snap)"""
    bl_idname = "maya.uv_align"
    bl_label = "Align UVs"

    axis: EnumProperty(items=(('U', "U", ""), ('V', "V", "")))
    where: EnumProperty(items=(('MIN', "Min", ""), ('AVG', "Average", ""), ('MAX', "Max", "")))

    def execute(self, context):
        sync = _sync(context)
        objs = edit_meshes(context)
        loops = [(uv, l) for _o, bm, uv in objs for l in selected_loops(bm, uv, sync)]
        if not loops:
            self.report({'WARNING'}, "Select some UVs first")
            return {'CANCELLED'}
        i = 0 if self.axis == 'U' else 1
        values = [l[uv].uv[i] for uv, l in loops]
        target = {'MIN': min(values), 'MAX': max(values), 'AVG': sum(values) / len(values)}[self.where]
        for uv, l in loops:
            l[uv].uv[i] = target
        _update(objs)
        return {'FINISHED'}


class MAYA_OT_uv_stack(_UVOperator, bpy.types.Operator):
    """Stack Shells: move the selected shells on top of each other (Maya UV Toolkit > Arrange)"""
    bl_idname = "maya.uv_stack"
    bl_label = "Stack Shells"

    def execute(self, context):
        sync = _sync(context)
        objs = edit_meshes(context)
        shells = [(uv, _shell_loops(s)) for _o, bm, uv in objs for s in selected_shells(bm, uv, sync)]
        if len(shells) < 2:
            self.report({'WARNING'}, "Select two or more shells")
            return {'CANCELLED'}
        target = _center(shells[0][1], shells[0][0])
        for uv, loops in shells[1:]:
            offset = target - _center(loops, uv)
            for l in loops:
                l[uv].uv += offset
        _update(objs)
        return {'FINISHED'}


class MAYA_OT_uv_normalize(_UVOperator, bpy.types.Operator):
    """Normalize: scale the selection to fill the 0-1 UV range (Maya UV Toolkit > Arrange)"""
    bl_idname = "maya.uv_normalize"
    bl_label = "Normalize"

    keep_ratio: BoolProperty(name="Preserve Aspect Ratio", default=True)
    per_shell: BoolProperty(name="Each Shell", description="Normalize each shell on its own", default=False)

    def execute(self, context):
        sync = _sync(context)
        objs = edit_meshes(context)
        groups = []
        for _o, bm, uv in objs:
            if self.per_shell:
                groups += [[(uv, l) for l in _shell_loops(s)] for s in selected_shells(bm, uv, sync)]
            else:
                groups.append([(uv, l) for l in selected_loops(bm, uv, sync)])
        if not self.per_shell:
            groups = [[item for g in groups for item in g]]
        groups = [g for g in groups if g]
        if not groups:
            self.report({'WARNING'}, "Select some UVs first")
            return {'CANCELLED'}
        for group in groups:
            us = [l[uv].uv.x for uv, l in group]
            vs = [l[uv].uv.y for uv, l in group]
            w = max(us) - min(us) or 1.0
            h = max(vs) - min(vs) or 1.0
            sx, sy = 1.0 / w, 1.0 / h
            if self.keep_ratio:
                sx = sy = min(sx, sy)
            u0, v0 = min(us), min(vs)
            for uv, l in group:
                p = l[uv].uv
                l[uv].uv = Vector(((p.x - u0) * sx, (p.y - v0) * sy))
        _update(objs)
        return {'FINISHED'}


def _area_3d(face, matrix):
    pts = [matrix @ v.co for v in face.verts]
    area = 0.0
    for i in range(1, len(pts) - 1):
        area += (pts[i] - pts[0]).cross(pts[i + 1] - pts[0]).length / 2
    return area


def _area_uv(face, uv):
    pts = [l[uv].uv for l in face.loops]
    area = 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        area += a.x * b.y - b.x * a.y
    return abs(area) / 2


def _scene_unit(context):
    """Length of one Blender unit in the displayed length unit (cm by default in Maya scenes)."""
    units = context.scene.unit_settings
    per_meter = {'KILOMETERS': 0.001, 'METERS': 1.0, 'CENTIMETERS': 100.0, 'MILLIMETERS': 1000.0,
                 'MICROMETERS': 1e6, 'MILES': 1 / 1609.344, 'FEET': 3.28084, 'INCHES': 39.3701,
                 'THOU': 39370.1}.get(units.length_unit, 1.0)
    if units.system == 'NONE':
        return 1.0, "unit"
    name = {'CENTIMETERS': "cm", 'METERS': "m", 'MILLIMETERS': "mm", 'INCHES': "in", 'FEET': "ft"}.get(
        units.length_unit, "unit")
    return units.scale_length * per_meter, name


def texel_density(context, shells_by_obj, size):
    """Pixels per displayed length unit for these faces."""
    unit, _name = _scene_unit(context)
    area3d = area_uv = 0.0
    for obj, uv, faces in shells_by_obj:
        for f in faces:
            area3d += _area_3d(f, obj.matrix_world)
            area_uv += _area_uv(f, uv)
    if area3d <= 0:
        return 0.0
    return math.sqrt(area_uv) * size / (math.sqrt(area3d) * unit)


class MAYA_OT_uv_texel_density(_UVOperator, bpy.types.Operator):
    """Get or set the texel density of the selected shells (Maya UV Toolkit > Texel Density)"""
    bl_idname = "maya.uv_texel_density"
    bl_label = "Texel Density"

    action: EnumProperty(items=(('GET', "Get", "Read the density of the selection"),
                                ('SET', "Set", "Scale each selected shell to the density")))

    def execute(self, context):
        scene = context.scene
        sync = _sync(context)
        objs = edit_meshes(context)
        shells = [(obj, uv, s) for obj, bm, uv in objs for s in selected_shells(bm, uv, sync)]
        if not shells:
            self.report({'WARNING'}, "Select some UVs first")
            return {'CANCELLED'}
        size = scene.maya_uv_map_size
        if self.action == 'GET':
            scene.maya_uv_texel_density = texel_density(context, shells, size)
            return {'FINISHED'}
        target = scene.maya_uv_texel_density
        if target <= 0:
            return {'CANCELLED'}
        for obj, uv, shell in shells:
            current = texel_density(context, [(obj, uv, shell)], size)
            if current <= 0:
                continue
            factor = target / current
            loops = _shell_loops(shell)
            c = _center(loops, uv)
            for l in loops:
                l[uv].uv = c + (l[uv].uv - c) * factor
        _update(objs)
        return {'FINISHED'}


class MAYA_OT_uv_unfold(_UVOperator, bpy.types.Operator):
    """Unfold the selected shells in place: flatten them without moving them
    (Maya Unfold; Blender's Unwrap would re-pack everything into 0-1)"""
    bl_idname = "maya.uv_unfold"
    bl_label = "Unfold"

    method: EnumProperty(name="Method", items=(
        ('ANGLE_BASED', "Angle Based", "Good for organic shapes"),
        ('CONFORMAL', "Conformal", "Keeps angles, faster"),
        ('MINIMUM_STRETCH', "Minimum Stretch", "Even texel size (Blender 4.3+)"),
    ), default='ANGLE_BASED')

    def execute(self, context):
        sync = _sync(context)
        objs = edit_meshes(context)
        before = []
        for obj, bm, uv in objs:
            bm.faces.ensure_lookup_table()
            for shell in selected_shells(bm, uv, sync):
                loops = _shell_loops(shell)
                area = sum(_area_uv(f, uv) for f in shell)
                before.append((obj, [f.index for f in shell], _center(loops, uv), area))
        if not before:
            self.report({'WARNING'}, "Select some UVs first")
            return {'CANCELLED'}
        # Unwrap uses seams: mark the current shell borders so the shells stay separate (like Maya)
        for obj, bm, uv in edit_meshes(context):
            bm.faces.ensure_lookup_table()
            for o, indices, _c, _a in before:
                if o is not obj:
                    continue
                for i in indices:
                    f = bm.faces[i]
                    for l in f.loops:
                        if _uv_connected(f, l, uv) is None:
                            l.edge.seam = True
        method = self.method
        if method not in bpy.ops.uv.unwrap.get_rna_type().properties["method"].enum_items.keys():
            method = 'ANGLE_BASED'
        # Unwrap flattens every selected face. Pin everything except the shells to unfold so the
        # rest stays put, and select the shells' faces (both put back afterwards).
        targets = {(obj.name, i) for obj, indices, _c, _a in before for i in indices}
        saved = []
        for obj, bm, uv in edit_meshes(context):
            bm.faces.ensure_lookup_table()
            # By index: the edit mesh is rebuilt by the unwrap, old BMesh references die
            pins = [(f.index, k, l[uv].pin_uv) for f in bm.faces for k, l in enumerate(f.loops)]
            picked = {f.index for f in bm.faces if f.select}
            saved.append((obj, bm, uv, pins, picked))
            for f in bm.faces:
                inside = (obj.name, f.index) in targets
                for l in f.loops:
                    l[uv].pin_uv = l[uv].pin_uv if inside else True
                if inside and not f.select:
                    f.select_set(True)
        try:
            bpy.ops.uv.unwrap(method=method, margin=0.0)
        except RuntimeError as ex:
            self.report({'WARNING'}, str(ex).replace("Error: ", "").strip())
            return {'CANCELLED'}
        finally:
            for obj, bm, uv, pins, picked in saved:
                bm = bmesh.from_edit_mesh(obj.data)
                uv = bm.loops.layers.uv.active
                bm.faces.ensure_lookup_table()
                for fi, k, pin in pins:
                    bm.faces[fi].loops[k][uv].pin_uv = pin
                if context.scene.tool_settings.use_uv_select_sync:
                    # Deselect first, then select: deselecting a neighbor would drop shared vertices
                    for f in bm.faces:
                        f.select_set(False)
                    for f in bm.faces:
                        if f.index in picked:
                            f.select_set(True)
                    bm.select_flush_mode()
        # Put every shell back where it was, with the same UV area
        objs = edit_meshes(context)
        layers = {obj.name: (bm, uv) for obj, bm, uv in objs}
        for obj, indices, center, area in before:
            bm, uv = layers[obj.name]
            bm.faces.ensure_lookup_table()
            shell = [bm.faces[i] for i in indices]
            loops = _shell_loops(shell)
            new_area = sum(_area_uv(f, uv) for f in shell)
            scale = math.sqrt(area / new_area) if new_area > 0 and area > 0 else 1.0
            c = _center(loops, uv)
            for l in loops:
                l[uv].uv = center + (l[uv].uv - c) * scale
        _update(objs)
        return {'FINISHED'}


class MAYA_OT_uv_component_mode(bpy.types.Operator):
    """UV Editor selection type (Maya: right-click menu in the UV Editor)"""
    bl_idname = "maya.uv_component_mode"
    bl_label = "UV Selection Type"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(items=(
        ('VERTEX', "UV", ""), ('EDGE', "Edge", ""), ('FACE', "Face", ""), ('SHELL', "UV Shell", ""),
        ('OBJECT', "Object Mode", ""),
    ))

    def execute(self, context):
        if self.mode == 'OBJECT':
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            return {'FINISHED'}
        if context.mode != 'EDIT_MESH':
            return {'CANCELLED'}
        ts = context.scene.tool_settings
        modes = ts.bl_rna.properties["uv_select_mode"].enum_items.keys()
        shell = self.mode == 'SHELL'
        if ts.use_uv_select_sync:
            if shell and hasattr(ts, "use_uv_select_island"):
                bpy.ops.mesh.select_mode(type='FACE')
                ts.use_uv_select_island = True
                return {'FINISHED'}
            if shell:
                ts.use_uv_select_sync = False  # Blender 4.x: shell selection needs sync off
            else:
                bpy.ops.mesh.select_mode(type={'VERTEX': 'VERT'}.get(self.mode, self.mode))
                if hasattr(ts, "use_uv_select_island"):
                    ts.use_uv_select_island = False
                return {'FINISHED'}
        if shell:
            if 'ISLAND' in modes:
                ts.uv_select_mode = 'ISLAND'
            else:
                ts.uv_select_mode = 'FACE'
                ts.use_uv_select_island = True
        else:
            ts.uv_select_mode = self.mode
            if hasattr(ts, "use_uv_select_island"):
                ts.use_uv_select_island = False
        return {'FINISHED'}


class MAYA_OT_uv_checker(bpy.types.Operator):
    """Show a checker map behind the UVs (Maya UV Editor checker button)"""
    bl_idname = "maya.uv_checker"
    bl_label = "Checker Map"

    @classmethod
    def poll(cls, context):
        return context.space_data is not None and context.space_data.type == 'IMAGE_EDITOR'

    def execute(self, context):
        space = context.space_data
        if space.image is not None and space.image.name == CHECKER_NAME:
            space.image = bpy.data.images.get(context.window_manager.maya_uv_prev_image)
            return {'FINISHED'}
        context.window_manager.maya_uv_prev_image = space.image.name if space.image else ""
        image = bpy.data.images.get(CHECKER_NAME)
        if image is None:
            image = bpy.data.images.new(CHECKER_NAME, 1024, 1024)
            image.generated_type = 'COLOR_GRID'
        space.image = image
        return {'FINISHED'}


class MAYA_OT_uv_editor(bpy.types.Operator):
    """Open the UV Editor in its own window with the UV Toolkit, like Maya"""
    bl_idname = "maya.open_uv_editor"
    bl_label = "UV Editor"

    def execute(self, context):
        obj = context.active_object
        if obj is not None and obj.type == 'MESH' and obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
            # Like Maya, show the whole object's UVs when nothing is picked yet
            bm = bmesh.from_edit_mesh(obj.data)
            if not any(f.select for f in bm.faces):
                bpy.ops.mesh.select_all(action='SELECT')
        wm = context.window_manager
        before = {w.as_pointer() for w in wm.windows}
        bpy.ops.wm.window_new()
        window = next((w for w in wm.windows if w.as_pointer() not in before), None)
        if window is None:
            return {'CANCELLED'}
        area = window.screen.areas[0]
        area.ui_type = 'UV'
        space = area.spaces.active

        def _later():
            try:
                space.show_region_ui = True       # UV Toolkit
                space.show_region_toolbar = True
                space.show_region_tool_header = True
                for region in area.regions:
                    if region.type == 'UI' and hasattr(region, "active_panel_category"):
                        region.active_panel_category = "UV Toolkit"
            except (ReferenceError, AttributeError, TypeError):
                pass
            return None

        bpy.app.timers.register(_later, first_interval=0.2)
        return {'FINISHED'}


class MAYA_OT_uv_mmb_transform(bpy.types.Operator):
    """Middle-drag in the UV Editor: move / rotate / scale with the active tool (Maya)"""
    bl_idname = "maya.uv_mmb_transform"
    bl_label = "Middle-drag UV Transform"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH' and context.area is not None and context.area.type == 'IMAGE_EDITOR'

    def invoke(self, context, event):
        try:
            tool = context.workspace.tools.from_space_image_mode('UV', create=False)
        except (AttributeError, TypeError):
            tool = None
        idname = tool.idname if tool else ""
        try:
            if idname.endswith("rotate"):
                bpy.ops.transform.rotate('INVOKE_DEFAULT', release_confirm=True)
            elif idname.endswith("scale"):
                bpy.ops.transform.resize('INVOKE_DEFAULT', release_confirm=True)
            else:
                bpy.ops.transform.translate('INVOKE_DEFAULT', release_confirm=True)
        except RuntimeError:
            return {'PASS_THROUGH'}
        return {'FINISHED'}


_uv_snap_saved = None


class MAYA_OT_uv_snap_hold(bpy.types.Operator):
    """Snap UVs while the key is held (X: grid, V: UV points)"""
    bl_idname = "maya.uv_snap_hold"
    bl_label = "Hold to Snap UVs"

    element: EnumProperty(items=(('GRID', "Grid", ""), ('VERTEX', "UV", "")))
    release: BoolProperty(default=False, options={'SKIP_SAVE'})

    def execute(self, context):
        global _uv_snap_saved
        ts = context.scene.tool_settings
        if self.release:
            if _uv_snap_saved is not None:
                ts.use_snap_uv, ts.snap_uv_element = _uv_snap_saved
                _uv_snap_saved = None
            return {'FINISHED'}
        if _uv_snap_saved is None:
            _uv_snap_saved = (ts.use_snap_uv, set(ts.snap_uv_element))
        items = ts.bl_rna.properties["snap_uv_element"].enum_items.keys()
        element = self.element if self.element in items else 'INCREMENT'
        ts.snap_uv_element = {element}
        ts.use_snap_uv = True
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Texture borders: shell borders drawn thick in the UV Editor
# ---------------------------------------------------------------------------

BORDER_COLOR = (0.9, 0.9, 0.9, 1.0)
BORDER_MAX_FACES = 40000
_border_cache = {"dirty": True, "lines": []}
_border_handle = None


def _borders_dirty():
    _border_cache["dirty"] = True


def _compute_borders(context):
    lines = []
    sync = _sync(context)
    for obj, bm, uv in edit_meshes(context):
        if len(bm.faces) > BORDER_MAX_FACES:
            continue
        for f in bm.faces:
            if not face_visible(f, sync):
                continue
            for l in f.loops:
                other = _uv_connected(f, l, uv)
                if other is None or not face_visible(other, sync):
                    lines.append((tuple(l[uv].uv), tuple(l.link_loop_next[uv].uv)))
    return lines


def _draw_borders():
    context = bpy.context
    wm = context.window_manager
    space = context.space_data
    if not wm.maya_uv_borders or context.mode != 'EDIT_MESH' or space is None or space.mode != 'UV':
        return
    try:
        if _border_cache["dirty"]:
            _border_cache["lines"] = _compute_borders(context)
            _border_cache["dirty"] = False
        lines = _border_cache["lines"]
        if not lines:
            return
        import gpu
        from gpu_extras.batch import batch_for_shader
        region = context.region
        to_px = region.view2d.view_to_region
        coords = []
        for a, b in lines:
            coords.append(to_px(a[0], a[1], clip=False))
            coords.append(to_px(b[0], b[1], clip=False))
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": [(x, y, 0.0) for x, y in coords]})
        shader.bind()
        shader.uniform_float("viewportSize", (region.width, region.height))
        shader.uniform_float("lineWidth", 3.0)
        shader.uniform_float("color", BORDER_COLOR)
        gpu.state.blend_set('ALPHA')
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    except Exception:
        pass


@persistent
def _on_depsgraph(scene, depsgraph=None):
    if depsgraph is None:
        _borders_dirty()
        return
    for update in depsgraph.updates:
        if isinstance(update.id, (bpy.types.Mesh, bpy.types.Object)) and update.is_updated_geometry:
            _borders_dirty()
            return


# ---------------------------------------------------------------------------
# UV Toolkit (sidebar) and marking menus
# ---------------------------------------------------------------------------

def _op(layout, idname, text, icon='NONE', **props):
    from .maya_menus import op
    return op(layout, idname, text, icon, **props)


class MAYA_PT_uv_toolkit(bpy.types.Panel):
    bl_idname = "MAYA_PT_uv_toolkit"
    bl_label = "UV Toolkit"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "UV Toolkit"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.mode == 'UV'

    def draw(self, context):
        layout = self.layout
        if context.mode != 'EDIT_MESH':
            layout.label(text="Select a mesh and open the UV Editor", icon='INFO')
            layout.operator("maya.uv_component_mode", text="Component Mode (Tab)").mode = 'FACE'
            return
        ts = context.scene.tool_settings
        layout.prop(ts, "use_uv_select_sync", text="Select in Viewport too (Sync)")


class _ToolkitSection:
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "UV Toolkit"
    bl_parent_id = "MAYA_PT_uv_toolkit"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'


class MAYA_PT_uv_select(_ToolkitSection, bpy.types.Panel):
    bl_idname = "MAYA_PT_uv_select"
    bl_label = "Select"

    def draw(self, context):
        lay = self.layout
        row = lay.row(align=True)
        for mode, icon, text in (('VERTEX', 'UV_VERTEXSEL', "UV"), ('EDGE', 'UV_EDGESEL', "Edge"),
                                 ('FACE', 'UV_FACESEL', "Face"), ('SHELL', 'UV_ISLANDSEL', "Shell")):
            row.operator("maya.uv_component_mode", text=text, icon=icon).mode = mode
        col = lay.column(align=True)
        col.operator("uv.select_linked", text="Select Shell", icon='UV_ISLANDSEL')
        col.operator("uv.select_overlap", text="Select Overlapping")
        _op(col, "uv.select_similar", "Select Similar")
        row = col.row(align=True)
        row.operator("uv.select_more", text="Grow")
        row.operator("uv.select_less", text="Shrink")


class MAYA_PT_uv_transform(_ToolkitSection, bpy.types.Panel):
    bl_idname = "MAYA_PT_uv_transform"
    bl_label = "Transform"

    def draw(self, context):
        lay = self.layout
        row = lay.row(align=True)
        row.operator("maya.uv_transform", text="", icon='LOOP_BACK').mode = 'ROT_CCW'
        row.operator("maya.uv_transform", text="", icon='LOOP_FORWARDS').mode = 'ROT_CW'
        row.operator("maya.uv_transform", text="Flip U").mode = 'FLIP_U'
        row.operator("maya.uv_transform", text="Flip V").mode = 'FLIP_V'
        lay.label(text="Align")
        for axis in ('U', 'V'):
            row = lay.row(align=True)
            for where, text in (('MIN', "Min"), ('AVG', "Avg"), ('MAX', "Max")):
                o = row.operator("maya.uv_align", text="%s %s" % (axis, text))
                o.axis, o.where = axis, where
        lay.operator("uv.align", text="Straighten UVs").axis = 'ALIGN_S'
        _op(lay, "uv.align_rotation", "Orient Shells", method='AUTO')
        lay.operator("uv.snap_selected", text="Snap to Pixels / Grid").target = 'PIXELS'


class MAYA_PT_uv_create(_ToolkitSection, bpy.types.Panel):
    bl_idname = "MAYA_PT_uv_create"
    bl_label = "Create"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        lay = self.layout
        col = lay.column(align=True)
        _op(col, "uv.smart_project", "Automatic", 'UV_DATA')
        _op(col, "uv.project_from_view", "Camera-Based / Planar", 'VIEW_CAMERA')
        _op(col, "uv.cube_project", "Cube", 'MESH_CUBE')
        _op(col, "uv.cylinder_project", "Cylindrical", 'MESH_CYLINDER')
        _op(col, "uv.sphere_project", "Spherical", 'MESH_UVSPHERE')
        _op(col, "uv.follow_active_quads", "Contour Stretch (Follow Quads)")


class MAYA_PT_uv_cut_sew(_ToolkitSection, bpy.types.Panel):
    bl_idname = "MAYA_PT_uv_cut_sew"
    bl_label = "Cut and Sew"

    def draw(self, context):
        lay = self.layout
        row = lay.row(align=True)
        row.operator("maya.uv_cut", text="Cut", icon='SCULPTMODE_HLT')
        row.operator("maya.uv_sew", text="Sew", icon='AUTOMERGE_ON').move = False
        row = lay.row(align=True)
        row.operator("maya.uv_sew", text="Move and Sew").move = True
        row.operator("uv.select_split", text="Split")
        row = lay.row(align=True)
        row.operator("uv.weld", text="Merge (Weld)")
        row.operator("uv.remove_doubles", text="Merge by Distance")


class MAYA_PT_uv_unfold(_ToolkitSection, bpy.types.Panel):
    bl_idname = "MAYA_PT_uv_unfold"
    bl_label = "Unfold"

    def draw(self, context):
        lay = self.layout
        row = lay.row(align=True)
        row.operator("maya.uv_unfold", text="Unfold", icon='UV')
        row.operator("uv.minimize_stretch", text="Optimize").iterations = 50
        _op(lay, "uv.unwrap", "Unwrap (re-pack into 0-1)", margin=0.02)


class MAYA_PT_uv_arrange(_ToolkitSection, bpy.types.Panel):
    bl_idname = "MAYA_PT_uv_arrange"
    bl_label = "Arrange and Layout"

    def draw(self, context):
        lay = self.layout
        row = lay.row(align=True)
        row.operator("uv.pack_islands", text="Layout", icon='UV_ISLANDSEL').margin = 0.01
        row.operator("maya.uv_stack", text="Stack")
        row = lay.row(align=True)
        row.operator("maya.uv_normalize", text="Normalize")
        row.operator("uv.average_islands_scale", text="Match Scale")


class MAYA_PT_uv_texel(_ToolkitSection, bpy.types.Panel):
    bl_idname = "MAYA_PT_uv_texel"
    bl_label = "Texel Density"

    def draw(self, context):
        lay = self.layout
        scene = context.scene
        _unit, name = _scene_unit(context)
        lay.prop(scene, "maya_uv_map_size", text="Map Size")
        row = lay.row(align=True)
        row.prop(scene, "maya_uv_texel_density", text="px/" + name)
        row.operator("maya.uv_texel_density", text="Get").action = 'GET'
        row.operator("maya.uv_texel_density", text="Set").action = 'SET'


class MAYA_PT_uv_display(_ToolkitSection, bpy.types.Panel):
    bl_idname = "MAYA_PT_uv_display"
    bl_label = "Display"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        lay = self.layout
        space = context.space_data
        uv_editor = space.uv_editor
        checker = space.image is not None and space.image.name == CHECKER_NAME
        lay.operator("maya.uv_checker", text="Checker Map", icon='TEXTURE', depress=checker)
        lay.prop(context.window_manager, "maya_uv_borders", text="Texture Borders")
        lay.prop(uv_editor, "show_stretch", text="Distortion")
        if uv_editor.show_stretch:
            lay.prop(uv_editor, "display_stretch_type", text="")
        if hasattr(uv_editor, "show_faces"):
            lay.prop(uv_editor, "show_faces", text="Shaded UVs")
        if hasattr(uv_editor, "uv_face_opacity"):
            lay.prop(uv_editor, "uv_face_opacity", text="Shade Opacity")


class MAYA_OT_uv_cut(_UVOperator, bpy.types.Operator):
    """Cut the selected UV edges: they become shell borders (Maya Cut).
    Unfold or move a side to separate them"""
    bl_idname = "maya.uv_cut"
    bl_label = "Cut UV Edges"

    def execute(self, context):
        objs = edit_meshes(context)
        sync = _sync(context)
        count = picked = 0
        for _obj, bm, uv in objs:
            for f in bm.faces:
                if not face_visible(f, sync):
                    continue
                for l in f.loops:
                    if loop_edge_selected(l, uv, sync):
                        picked += 1
                        if not l.edge.seam:
                            l.edge.seam = True
                            count += 1
        if not picked:
            self.report({'WARNING'}, "Select UV edges first")
            return {'CANCELLED'}
        # The cut edges are seams: they show as shell borders and Unfold / Layout keep them apart
        _update(objs)
        self.report({'INFO'}, "Cut %d edge(s)" % count)
        return {'FINISHED'}


class MAYA_OT_uv_sew(_UVOperator, bpy.types.Operator):
    """Sew the selected UV edges back together (Move and Sew: bring the smaller shell over)"""
    bl_idname = "maya.uv_sew"
    bl_label = "Sew UV Edges"

    move: BoolProperty(name="Move and Sew", default=False)

    def execute(self, context):
        try:
            bpy.ops.uv.stitch(snap_islands=self.move, midpoint_snap=not self.move, clear_seams=True)
        except (RuntimeError, TypeError):
            try:
                bpy.ops.uv.stitch()
            except RuntimeError as ex:
                self.report({'WARNING'}, str(ex).replace("Error: ", "").strip())
                return {'CANCELLED'}
        _borders_dirty()
        return {'FINISHED'}


class MAYA_MT_uv_component_pie(bpy.types.Menu):
    bl_label = "UV Selection"

    def draw(self, context):
        pie = self.layout.menu_pie()
        # Pie order: W, E, S, N, NW, NE, SW, SE
        pie.operator("maya.uv_component_mode", text="UV", icon='UV_VERTEXSEL').mode = 'VERTEX'
        pie.operator("maya.uv_component_mode", text="Object Mode", icon='OBJECT_DATAMODE').mode = 'OBJECT'
        pie.operator("maya.uv_component_mode", text="Face", icon='UV_FACESEL').mode = 'FACE'
        pie.operator("maya.uv_component_mode", text="Edge", icon='UV_EDGESEL').mode = 'EDGE'
        pie.operator("uv.select_linked", text="Select Shell", icon='UV_ISLANDSEL')
        pie.operator("maya.uv_component_mode", text="UV Shell", icon='UV_ISLANDSEL').mode = 'SHELL'
        pie.operator("uv.select_all", text="Select All").action = 'SELECT'
        pie.operator("uv.select_all", text="Invert Selection").action = 'INVERT'


class MAYA_MT_uv_tools_pie(bpy.types.Menu):
    bl_label = "UV Tools"

    def draw(self, context):
        pie = self.layout.menu_pie()
        pie.operator("maya.uv_cut", text="Cut", icon='SCULPTMODE_HLT')
        pie.operator("maya.uv_sew", text="Sew", icon='AUTOMERGE_ON').move = False
        pie.operator("uv.pack_islands", text="Layout", icon='UV_ISLANDSEL').margin = 0.01
        pie.operator("maya.uv_unfold", text="Unfold", icon='UV')
        pie.operator("maya.uv_transform", text="Rotate 90°", icon='LOOP_FORWARDS').mode = 'ROT_CW'
        pie.operator("maya.uv_sew", text="Move and Sew").move = True
        pie.operator("maya.uv_transform", text="Flip U", icon='ARROW_LEFTRIGHT').mode = 'FLIP_U'
        pie.operator("uv.align", text="Straighten").axis = 'ALIGN_S'


class MAYA_MT_uv_convert_pie(bpy.types.Menu):
    bl_label = "Convert UV Selection"

    def draw(self, context):
        pie = self.layout.menu_pie()
        pie.operator("maya.uv_component_mode", text="To UVs", icon='UV_VERTEXSEL').mode = 'VERTEX'
        pie.operator("maya.uv_component_mode", text="To Edges", icon='UV_EDGESEL').mode = 'EDGE'
        pie.operator("maya.uv_component_mode", text="To Faces", icon='UV_FACESEL').mode = 'FACE'
        pie.operator("uv.select_linked", text="To Shell", icon='UV_ISLANDSEL')
        pie.operator("uv.select_loop", text="To Edge Loop")
        pie.operator("uv.select_edge_ring", text="To Edge Ring")


# (keymap, operator, key, value, modifiers, properties) - registered by keymaps.py
UV_KEYS = (
    ("UV Editor", "wm.call_menu_pie", 'RIGHTMOUSE', 'PRESS', {}, {"name": "MAYA_MT_uv_component_pie"}),
    ("UV Editor", "wm.call_menu_pie", 'RIGHTMOUSE', 'PRESS', {"shift": True}, {"name": "MAYA_MT_uv_tools_pie"}),
    ("UV Editor", "wm.call_menu_pie", 'RIGHTMOUSE', 'PRESS', {"ctrl": True}, {"name": "MAYA_MT_uv_convert_pie"}),
    ("UV Editor", "maya.uv_mmb_transform", 'MIDDLEMOUSE', 'CLICK_DRAG', {}, {}),
    ("UV Editor", "maya.uv_snap_hold", 'X', 'PRESS', {}, {"element": 'GRID'}),
    ("UV Editor", "maya.uv_snap_hold", 'X', 'RELEASE', {}, {"element": 'GRID', "release": True}),
    ("UV Editor", "maya.uv_snap_hold", 'V', 'PRESS', {}, {"element": 'VERTEX'}),
    ("UV Editor", "maya.uv_snap_hold", 'V', 'RELEASE', {}, {"element": 'VERTEX', "release": True}),
    ("UV Editor", "maya.uv_transform", 'R', 'PRESS', {"ctrl": True}, {"mode": 'ROT_CW'}),
    ("Image", "image.view_selected", 'F', 'PRESS', {}, {}),
    ("Image", "image.view_all", 'A', 'PRESS', {}, {"fit_view": True}),
)


classes = (
    MAYA_OT_uv_transform,
    MAYA_OT_uv_align,
    MAYA_OT_uv_stack,
    MAYA_OT_uv_normalize,
    MAYA_OT_uv_texel_density,
    MAYA_OT_uv_unfold,
    MAYA_OT_uv_component_mode,
    MAYA_OT_uv_checker,
    MAYA_OT_uv_editor,
    MAYA_OT_uv_mmb_transform,
    MAYA_OT_uv_snap_hold,
    MAYA_OT_uv_cut,
    MAYA_OT_uv_sew,
    MAYA_PT_uv_toolkit,
    MAYA_PT_uv_select,
    MAYA_PT_uv_transform,
    MAYA_PT_uv_create,
    MAYA_PT_uv_cut_sew,
    MAYA_PT_uv_unfold,
    MAYA_PT_uv_arrange,
    MAYA_PT_uv_texel,
    MAYA_PT_uv_display,
    MAYA_MT_uv_component_pie,
    MAYA_MT_uv_tools_pie,
    MAYA_MT_uv_convert_pie,
)


def register():
    global _border_handle
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.maya_uv_map_size = IntProperty(
        name="Map Size", description="Texture resolution used for texel density (pixels)",
        default=1024, min=1, soft_max=8192)
    bpy.types.Scene.maya_uv_texel_density = FloatProperty(
        name="Texel Density", description="Pixels per scene length unit", default=10.24, min=0.0, precision=3)
    bpy.types.WindowManager.maya_uv_borders = BoolProperty(
        name="Texture Borders", description="Draw UV shell borders thick, like Maya", default=True)
    bpy.types.WindowManager.maya_uv_prev_image = StringProperty()
    _border_handle = bpy.types.SpaceImageEditor.draw_handler_add(_draw_borders, (), 'WINDOW', 'POST_PIXEL')
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph)


def unregister():
    global _border_handle
    if _on_depsgraph in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph)
    if _border_handle is not None:
        bpy.types.SpaceImageEditor.draw_handler_remove(_border_handle, 'WINDOW')
        _border_handle = None
    del bpy.types.WindowManager.maya_uv_prev_image
    del bpy.types.WindowManager.maya_uv_borders
    del bpy.types.Scene.maya_uv_texel_density
    del bpy.types.Scene.maya_uv_map_size
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
