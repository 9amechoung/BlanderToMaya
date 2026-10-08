"""Operators for Maya commands that Blender has no single operator for.

Group / Ungroup, Duplicate with Transform, Booleans, Loft / Revolve / Planar /
Extrude (surfaces), Lattice, Nonlinear deformers, Match Transformations,
Add Attribute, Delete by Type, selection conversion, pick-walking,
soft selection (B), pivot editing (D / Insert), background cycling (Alt+B)...
"""

import os

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix, Vector

GEOMETRY_TYPES = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}


def _selected_center(objects):
    points = [o.matrix_world.translation for o in objects]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    return (lo + hi) / 2


def _set_parent_keep_transform(child, parent):
    world = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted() if parent else Matrix.Identity(4)
    child.matrix_world = world


def _object_mode(context):
    return context.mode == 'OBJECT'


# ---------------------------------------------------------------------------
# Edit menu: Group, Ungroup, Duplicate with Transform, Delete by Type
# ---------------------------------------------------------------------------

class MAYA_OT_group(bpy.types.Operator):
    """Group the selected objects under a new empty (Maya: Ctrl+G)"""
    bl_idname = "maya.group"
    bl_label = "Group"
    bl_options = {'REGISTER', 'UNDO'}

    pivot: EnumProperty(name="Group Pivot", items=(('CENTER', "Center", ""), ('ORIGIN', "Origin", "")),
                        default='CENTER')

    @classmethod
    def poll(cls, context):
        return _object_mode(context) and context.selected_objects

    def execute(self, context):
        selected = list(context.selected_objects)
        group = bpy.data.objects.new("group1", None)
        group.empty_display_type = 'PLAIN_AXES'
        group.empty_display_size = 0.0001  # Maya groups have no visible shape
        context.collection.objects.link(group)
        # Keep the hierarchy: the group goes under the common parent, if any.
        parents = {o.parent for o in selected}
        common = parents.pop() if len(parents) == 1 else None
        group.location = _selected_center(selected) if self.pivot == 'CENTER' else Vector()
        context.view_layer.update()  # matrix_world must be current before parenting to it
        if common is not None:
            _set_parent_keep_transform(group, common)
            context.view_layer.update()
        for obj in selected:
            _set_parent_keep_transform(obj, group)
            obj.select_set(False)
        group.select_set(True)
        context.view_layer.objects.active = group
        return {'FINISHED'}


class MAYA_OT_ungroup(bpy.types.Operator):
    """Remove the selected groups and keep their children in place"""
    bl_idname = "maya.ungroup"
    bl_label = "Ungroup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _object_mode(context) and context.selected_objects

    def execute(self, context):
        for group in list(context.selected_objects):
            for child in list(group.children):
                _set_parent_keep_transform(child, group.parent)
                child.select_set(True)
            if group.type == 'EMPTY':
                bpy.data.objects.remove(group)
        return {'FINISHED'}


_last_duplicate = {}  # {"name": duplicate name, "source": source matrix}


class MAYA_OT_duplicate_with_transform(bpy.types.Operator):
    """Duplicate and repeat the move/rotate/scale done since the last duplicate (Maya: Shift+D)"""
    bl_idname = "maya.duplicate_with_transform"
    bl_label = "Duplicate with Transform"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _object_mode(context) and context.active_object is not None

    def execute(self, context):
        src = context.active_object
        src_matrix = src.matrix_world.copy()
        delta = None
        if _last_duplicate.get("name") == src.name:
            delta = src_matrix @ _last_duplicate["source"].inverted()
        bpy.ops.object.duplicate()
        dup = context.active_object
        if delta is not None:
            dup.matrix_world = delta @ src_matrix
        _last_duplicate["name"] = dup.name
        _last_duplicate["source"] = src_matrix
        return {'FINISHED'}


class MAYA_OT_delete_by_type(bpy.types.Operator):
    """Delete this kind of data from the selected objects"""
    bl_idname = "maya.delete_by_type"
    bl_label = "Delete by Type"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=(
        ('HISTORY', "History", "Apply modifiers"),
        ('CHANNELS', "Channels", "Animation keys"),
        ('CONSTRAINTS', "Constraints", ""),
        ('MOTION_PATHS', "Motion Paths", ""),
        ('RIGID_BODIES', "Rigid Bodies", ""),
        ('ATTRIBUTES', "Custom Attributes", ""),
    ))

    @classmethod
    def poll(cls, context):
        return _object_mode(context) and context.selected_objects

    def execute(self, context):
        objs = list(context.selected_objects)
        if self.kind == 'HISTORY':
            bpy.ops.object.convert(target='MESH')
        elif self.kind == 'CHANNELS':
            for o in objs:
                o.animation_data_clear()
        elif self.kind == 'CONSTRAINTS':
            for o in objs:
                o.constraints.clear()
        elif self.kind == 'MOTION_PATHS':
            bpy.ops.object.paths_clear(only_selected=True)
        elif self.kind == 'RIGID_BODIES':
            bpy.ops.rigidbody.objects_remove()
        elif self.kind == 'ATTRIBUTES':
            for o in objs:
                for key in [k for k in o.keys() if not k.startswith("_")]:
                    del o[key]
        return {'FINISHED'}


class MAYA_OT_delete_all_by_type(bpy.types.Operator):
    """Delete every object of this type in the scene"""
    bl_idname = "maya.delete_all_by_type"
    bl_label = "Delete All by Type"
    bl_options = {'REGISTER', 'UNDO'}

    object_type: EnumProperty(items=(
        ('CAMERA', "Cameras", ""), ('LIGHT', "Lights", ""), ('CURVE', "NURBS Curves", ""),
        ('SURFACE', "NURBS Surfaces", ""), ('ARMATURE', "Joints", ""), ('EMPTY', "Locators / Groups", ""),
        ('LATTICE', "Lattices", ""), ('FONT', "Type", ""),
    ))

    def execute(self, context):
        doomed = [o for o in context.scene.objects if o.type == self.object_type]
        for obj in doomed:
            bpy.data.objects.remove(obj)
        self.report({'INFO'}, "Deleted %d object(s)" % len(doomed))
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Modify menu
# ---------------------------------------------------------------------------

class MAYA_OT_match_transforms(bpy.types.Operator):
    """Match the selected objects to the last selected (active) one"""
    bl_idname = "maya.match_transforms"
    bl_label = "Match Transformations"
    bl_options = {'REGISTER', 'UNDO'}

    what: EnumProperty(items=(('ALL', "All", ""), ('TRANSLATE', "Translation", ""),
                              ('ROTATE', "Rotation", ""), ('SCALE', "Scaling", "")))

    @classmethod
    def poll(cls, context):
        return _object_mode(context) and context.active_object is not None and len(context.selected_objects) > 1

    def execute(self, context):
        target = context.active_object
        t_loc, t_rot, t_scale = target.matrix_world.decompose()
        for obj in context.selected_objects:
            if obj == target:
                continue
            loc, rot, scale = obj.matrix_world.decompose()
            if self.what in {'ALL', 'TRANSLATE'}:
                loc = t_loc
            if self.what in {'ALL', 'ROTATE'}:
                rot = t_rot
            if self.what in {'ALL', 'SCALE'}:
                scale = t_scale
            obj.matrix_world = Matrix.LocRotScale(loc, rot, scale)
        return {'FINISHED'}


class MAYA_OT_add_attribute(bpy.types.Operator):
    """Add a custom attribute; it shows up in the Channel Box"""
    bl_idname = "maya.add_attribute"
    bl_label = "Add Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    attr_name: StringProperty(name="Long Name", default="newAttribute")
    data_type: EnumProperty(name="Data Type", items=(('FLOAT', "Float", ""), ('INT', "Integer", ""),
                                                     ('BOOL', "Boolean", ""), ('STRING', "String", "")))
    minimum: FloatProperty(name="Minimum", default=0.0)
    maximum: FloatProperty(name="Maximum", default=10.0)
    default: FloatProperty(name="Default", default=0.0)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        name = self.attr_name.strip() or "newAttribute"
        if self.data_type == 'FLOAT':
            obj[name] = float(self.default)
        elif self.data_type == 'INT':
            obj[name] = int(self.default)
        elif self.data_type == 'BOOL':
            obj[name] = bool(self.default)
        else:
            obj[name] = ""
        if self.data_type in {'FLOAT', 'INT'}:
            ui = obj.id_properties_ui(name)
            ui.update(min=self.minimum, max=self.maximum, soft_min=self.minimum, soft_max=self.maximum)
        obj.update_tag()
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Mesh / Surfaces / Deform
# ---------------------------------------------------------------------------

class MAYA_OT_boolean(bpy.types.Operator):
    """Boolean the selected meshes: the first selected is the base, the others cut / join it"""
    bl_idname = "maya.boolean"
    bl_label = "Boolean"
    bl_options = {'REGISTER', 'UNDO'}

    operation: EnumProperty(items=(('UNION', "Union", ""), ('DIFFERENCE', "Difference", ""),
                                   ('INTERSECT', "Intersection", "")))

    @classmethod
    def poll(cls, context):
        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        return _object_mode(context) and len(meshes) >= 2

    def execute(self, context):
        active = context.active_object
        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        # Maya's base is the first selected; Blender's active is the last selected.
        others = [o for o in meshes if o != active]
        base, tools = others[0], others[1:] + [active]
        for tool in tools:
            mod = base.modifiers.new("boolean", 'BOOLEAN')
            mod.operation = self.operation
            mod.object = tool
        context.view_layer.objects.active = base
        for mod in [m for m in base.modifiers if m.type == 'BOOLEAN' and m.object in tools]:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        for tool in tools:
            bpy.data.objects.remove(tool)
        base.select_set(True)
        return {'FINISHED'}


class MAYA_OT_loft(bpy.types.Operator):
    """Loft a surface through the selected curves (in selection order)"""
    bl_idname = "maya.loft"
    bl_label = "Loft"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _object_mode(context) and len([o for o in context.selected_objects if o.type == 'CURVE']) >= 2

    def execute(self, context):
        curves = [o for o in context.selected_objects if o.type == 'CURVE']
        for o in context.selected_objects:
            o.select_set(o in curves)
        bpy.ops.object.duplicate()
        context.view_layer.objects.active = context.selected_objects[0]
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.join()
        loft = context.active_object
        loft.name = "loftedSurface1"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        try:
            bpy.ops.mesh.bridge_edge_loops()
        except RuntimeError as ex:
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'ERROR'}, "Loft failed: " + str(ex))
            return {'CANCELLED'}
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}


class MAYA_OT_revolve(bpy.types.Operator):
    """Revolve the selected curve around the Z axis (Screw modifier)"""
    bl_idname = "maya.revolve"
    bl_label = "Revolve"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type in {'CURVE', 'MESH'}

    def execute(self, context):
        mod = context.active_object.modifiers.new("revolve", 'SCREW')
        mod.steps = 32
        mod.render_steps = 32
        mod.use_merge_vertices = True
        return {'FINISHED'}


class MAYA_OT_planar(bpy.types.Operator):
    """Fill the selected closed curve with a flat surface"""
    bl_idname = "maya.planar"
    bl_label = "Planar"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'CURVE'

    def execute(self, context):
        curve = context.active_object.data
        curve.dimensions = '2D'
        curve.fill_mode = 'BOTH'
        for spline in curve.splines:
            spline.use_cyclic_u = True
        return {'FINISHED'}


class MAYA_OT_extrude_curve(bpy.types.Operator):
    """Extrude a profile curve along a path: select the profile, then the path (active)"""
    bl_idname = "maya.extrude_curve"
    bl_label = "Extrude Along Path"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len([o for o in context.selected_objects if o.type == 'CURVE']) >= 2

    def execute(self, context):
        path = context.active_object
        profile = next(o for o in context.selected_objects if o.type == 'CURVE' and o != path)
        path.data.bevel_mode = 'OBJECT'
        path.data.bevel_object = profile
        path.data.use_fill_caps = True
        return {'FINISHED'}


class MAYA_OT_add_lattice(bpy.types.Operator):
    """Create a lattice around the selected objects and deform them with it"""
    bl_idname = "maya.add_lattice"
    bl_label = "Lattice"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _object_mode(context) and any(o.type in GEOMETRY_TYPES for o in context.selected_objects)

    def execute(self, context):
        targets = [o for o in context.selected_objects if o.type in GEOMETRY_TYPES]
        corners = [o.matrix_world @ Vector(c) for o in targets for c in o.bound_box]
        lo = Vector([min(c[i] for c in corners) for i in range(3)])
        hi = Vector([max(c[i] for c in corners) for i in range(3)])
        data = bpy.data.lattices.new("ffd1Lattice")
        data.points_u = data.points_v = data.points_w = 3
        lattice = bpy.data.objects.new("ffd1Lattice", data)
        context.collection.objects.link(lattice)
        lattice.location = (lo + hi) / 2
        lattice.scale = [max(hi[i] - lo[i], 0.01) * 1.05 for i in range(3)]
        for obj in targets:
            mod = obj.modifiers.new("ffd1", 'LATTICE')
            mod.object = lattice
            obj.select_set(False)
        lattice.select_set(True)
        context.view_layer.objects.active = lattice
        return {'FINISHED'}


class MAYA_OT_nonlinear(bpy.types.Operator):
    """Add a nonlinear deformer (Simple Deform / Wave modifier)"""
    bl_idname = "maya.nonlinear"
    bl_label = "Nonlinear Deformer"
    bl_options = {'REGISTER', 'UNDO'}

    deformer: EnumProperty(items=(('BEND', "Bend", ""), ('FLARE', "Flare", ""), ('TWIST', "Twist", ""),
                                  ('SQUASH', "Squash", ""), ('SINE', "Sine", ""), ('WAVE', "Wave", "")))

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type in GEOMETRY_TYPES | {'LATTICE'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type not in GEOMETRY_TYPES | {'LATTICE'}:
                continue
            if self.deformer in {'SINE', 'WAVE'}:
                mod = obj.modifiers.new(self.deformer.lower() + "1", 'WAVE')
                mod.use_x = self.deformer == 'SINE'
                mod.use_y = self.deformer == 'WAVE'
                continue
            mod = obj.modifiers.new(self.deformer.lower() + "1", 'SIMPLE_DEFORM')
            mod.deform_method = {'BEND': 'BEND', 'FLARE': 'TAPER', 'TWIST': 'TWIST', 'SQUASH': 'STRETCH'}[self.deformer]
            mod.deform_axis = 'Z'
        return {'FINISHED'}


class MAYA_OT_pole_vector(bpy.types.Operator):
    """Use the selected object as the pole vector of the active bone's IK"""
    bl_idname = "maya.pole_vector"
    bl_label = "Pole Vector"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and context.active_pose_bone is not None

    def execute(self, context):
        bone = context.active_pose_bone
        ik = next((c for c in bone.constraints if c.type == 'IK'), None)
        if ik is None:
            self.report({'ERROR'}, "The active bone has no IK handle (Create IK Handle first)")
            return {'CANCELLED'}
        pole = next((o for o in context.selected_objects if o != context.active_object), None)
        if pole is None:
            self.report({'ERROR'}, "Also select the object to use as pole vector")
            return {'CANCELLED'}
        ik.pole_target = pole
        return {'FINISHED'}


class MAYA_OT_quick_rig(bpy.types.Operator):
    """Add a human rig template (Rigify meta-rig)"""
    bl_idname = "maya.quick_rig"
    bl_label = "Quick Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if "armature_human_metarig_add" not in dir(bpy.ops.object):
            import addon_utils
            for name in ("rigify", "bl_ext.blender_org.rigify"):
                try:
                    addon_utils.enable(name, default_set=True)
                except Exception:
                    pass
        if "armature_human_metarig_add" not in dir(bpy.ops.object):
            self.report({'ERROR'}, "Rigify is not installed (Preferences > Get Extensions > Rigify)")
            return {'CANCELLED'}
        bpy.ops.object.armature_human_metarig_add()
        return {'FINISHED'}


class MAYA_OT_add_hair(bpy.types.Operator):
    """Add hair curves to the selected mesh (Maya: XGen / nHair)"""
    bl_idname = "maya.add_hair"
    bl_label = "Add Hair"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _object_mode(context) and context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        bpy.ops.object.curves_empty_hair_add()
        return {'FINISHED'}


class MAYA_OT_import_audio(bpy.types.Operator, ImportHelper):
    """Import a sound file into the scene timeline"""
    bl_idname = "maya.import_audio"
    bl_label = "Import Audio"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default="*.wav;*.mp3;*.ogg;*.flac;*.aif;*.aiff", options={'HIDDEN'})

    def execute(self, context):
        scene = context.scene
        editor = scene.sequence_editor or scene.sequence_editor_create()
        strips = getattr(editor, "strips", None) or editor.sequences  # renamed in Blender 4.4+
        strips.new_sound(os.path.basename(self.filepath), self.filepath, 1, scene.frame_start)
        return {'FINISHED'}


class MAYA_OT_target_weld(bpy.types.Operator):
    """Target Weld: merge the selected vertices onto the last selected one
    (select the vertex to move, then Shift+click the target vertex)"""
    bl_idname = "maya.target_weld"
    bl_label = "Target Weld"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        try:
            bpy.ops.mesh.merge(type='LAST')
        except (TypeError, RuntimeError):
            self.report({'WARNING'}, "Select the vertex to move, then Shift+click the target vertex")
            return {'CANCELLED'}
        return {'FINISHED'}


class MAYA_OT_quad_draw(bpy.types.Operator):
    """Quad Draw: draw new polygons on top of another surface (Poly Build tool + snapping to faces)"""
    bl_idname = "maya.quad_draw"
    bl_label = "Quad Draw"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        ts = context.scene.tool_settings
        ts.use_snap = True
        ts.snap_elements = {'FACE_PROJECT'} if 'FACE_PROJECT' in ts.bl_rna.properties["snap_elements"].enum_items.keys() else {'FACE'}
        bpy.ops.wm.tool_set_by_id(name="builtin.poly_build")
        self.report({'INFO'}, "Quad Draw: click to add points on the live surface, Ctrl+click to make faces")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

class MAYA_OT_convert_selection(bpy.types.Operator):
    """Convert the selection to another component type (Maya: Select > Convert Selection)"""
    bl_idname = "maya.convert_selection"
    bl_label = "Convert Selection"
    bl_options = {'REGISTER', 'UNDO'}

    to: EnumProperty(items=(
        ('VERT', "To Vertices", ""), ('EDGE', "To Edges", ""), ('FACE', "To Faces", ""),
        ('UV', "To UVs", ""), ('VERT_FACE', "To Vertex Faces", ""), ('SHELL', "To Shell", ""),
        ('BORDER', "To Shell Border", ""), ('EDGE_LOOP', "To Edge Loop", ""), ('EDGE_RING', "To Edge Ring", ""),
        ('CONTAINED_EDGES', "To Contained Edges", ""), ('CONTAINED_FACES', "To Contained Faces", ""),
    ))

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def execute(self, context):
        if context.mode != 'EDIT_MESH':
            # Object selected: Maya selects all of its components of that type.
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE' if self.to in {'FACE', 'SHELL', 'CONTAINED_FACES'} else
                                     'EDGE' if self.to.startswith('EDGE') or self.to == 'CONTAINED_EDGES' else 'VERT')
            bpy.ops.mesh.select_all(action='SELECT')
        to = self.to
        if to in {'VERT', 'EDGE', 'FACE'}:
            bpy.ops.mesh.select_mode(type=to, use_expand=True)
        elif to in {'CONTAINED_EDGES', 'CONTAINED_FACES'}:
            bpy.ops.mesh.select_mode(type='EDGE' if to == 'CONTAINED_EDGES' else 'FACE', use_expand=False)
        elif to == 'VERT_FACE':
            context.tool_settings.mesh_select_mode = (True, False, True)
        elif to == 'SHELL':
            bpy.ops.mesh.select_linked()
        elif to == 'BORDER':
            bpy.ops.mesh.select_linked()
            bpy.ops.mesh.region_to_loop()
        elif to in {'EDGE_LOOP', 'EDGE_RING'}:
            bpy.ops.mesh.select_mode(type='EDGE', use_expand=True)
            ring = to == 'EDGE_RING'
            if "select_edge_loop_multi" in dir(bpy.ops.mesh):
                (bpy.ops.mesh.select_edge_ring_multi if ring else bpy.ops.mesh.select_edge_loop_multi)()
            else:
                bpy.ops.mesh.loop_multi_select(ring=ring)
        elif to == 'UV':
            bpy.ops.maya.open_uv_editor()
        return {'FINISHED'}


class MAYA_OT_pickwalk(bpy.types.Operator):
    """Walk the selection through the hierarchy (Maya: arrow keys)"""
    bl_idname = "maya.pickwalk"
    bl_label = "Pick Walk"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(items=(('UP', "Up (Parent)", ""), ('DOWN', "Down (Child)", ""),
                                   ('LEFT', "Left (Sibling)", ""), ('RIGHT', "Right (Sibling)", "")))

    @classmethod
    def poll(cls, context):
        return _object_mode(context) and context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        if self.direction == 'UP':
            target = obj.parent
        elif self.direction == 'DOWN':
            children = sorted(obj.children, key=lambda o: o.name)
            target = children[0] if children else None
        else:
            siblings = sorted((o for o in context.scene.objects if o.parent == obj.parent), key=lambda o: o.name)
            i = siblings.index(obj)
            target = siblings[(i + (1 if self.direction == 'RIGHT' else -1)) % len(siblings)]
        if target is None or not target.visible_get():
            return {'CANCELLED'}
        for o in context.selected_objects:
            o.select_set(False)
        target.select_set(True)
        context.view_layer.objects.active = target
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Hotkey helpers
# ---------------------------------------------------------------------------

class MAYA_OT_set_menu_set(bpy.types.Operator):
    """Switch the Maya menu set (F2 Modeling, F3 Rigging, F4 Animation, F5 FX, F6 Rendering)"""
    bl_idname = "maya.set_menu_set"
    bl_label = "Set Menu Set"

    menu_set: StringProperty(default='MODELING')

    def execute(self, context):
        context.window_manager.maya_menu_set = self.menu_set
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'TOPBAR':
                    area.tag_redraw()
        return {'FINISHED'}


def _proportional_attr(context):
    return "use_proportional_edit_objects" if context.mode == 'OBJECT' else "use_proportional_edit"


class MAYA_OT_soft_select(bpy.types.Operator):
    """Soft Selection (Maya: B toggles it, hold B and middle-drag to change the falloff radius)"""
    bl_idname = "maya.soft_select"
    bl_label = "Soft Select"

    def invoke(self, context, event):
        self._adjusting = False
        self._changed = False
        self._start_x = 0
        self._start_size = context.scene.tool_settings.proportional_size
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _header(self, context, text):
        if context.area is not None:
            context.area.header_text_set(text)

    def modal(self, context, event):
        ts = context.scene.tool_settings
        if event.type == 'B' and event.value == 'RELEASE':
            self._header(context, None)
            if not self._changed:
                attr = _proportional_attr(context)
                setattr(ts, attr, not getattr(ts, attr))
                self.report({'INFO'}, "Soft Select " + ("On" if getattr(ts, attr) else "Off"))
            return {'FINISHED'}
        if event.type == 'MIDDLEMOUSE':
            self._adjusting = event.value == 'PRESS'
            self._start_x = event.mouse_x
            self._start_size = ts.proportional_size
            if self._adjusting:
                setattr(ts, _proportional_attr(context), True)
            return {'RUNNING_MODAL'}
        if event.type == 'MOUSEMOVE' and self._adjusting:
            factor = 1.0 + (event.mouse_x - self._start_x) / 200.0
            ts.proportional_size = max(0.001, self._start_size * max(factor, 0.01))
            self._changed = True
            self._header(context, "Soft Select falloff radius: %.3f" % ts.proportional_size)
            return {'RUNNING_MODAL'}
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self._header(context, None)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}


class MAYA_OT_pivot_edit(bpy.types.Operator):
    """Edit the pivot (Maya: hold D or toggle with Insert): moves only the origin"""
    bl_idname = "maya.pivot_edit"
    bl_label = "Edit Pivot"

    state: EnumProperty(items=(('ON', "On", ""), ('OFF', "Off", ""), ('TOGGLE', "Toggle", "")))

    def execute(self, context):
        ts = context.scene.tool_settings
        if self.state == 'TOGGLE':
            ts.use_transform_data_origin = not ts.use_transform_data_origin
        else:
            ts.use_transform_data_origin = self.state == 'ON'
        if context.area is not None:
            context.area.header_text_set("Pivot edit: move/rotate changes only the pivot"
                                         if ts.use_transform_data_origin else None)
        return {'FINISHED'}


_BACKGROUNDS = ((0.365, 0.365, 0.365), (0.0, 0.0, 0.0), (0.16, 0.16, 0.16), (0.63, 0.63, 0.63))


class MAYA_OT_cycle_background(bpy.types.Operator):
    """Cycle the viewport background: Maya grey, black, dark grey, light grey (Maya: Alt+B)"""
    bl_idname = "maya.cycle_background"
    bl_label = "Cycle Background Color"

    def execute(self, context):
        shading = context.space_data.shading
        if shading.background_type != 'VIEWPORT':
            shading.background_type = 'VIEWPORT'
            index = 1
        else:
            current = tuple(round(c, 2) for c in shading.background_color)
            colors = [tuple(round(c, 2) for c in col) for col in _BACKGROUNDS]
            index = (colors.index(current) + 1) % len(colors) if current in colors else 1
        if index == 0:
            shading.background_type = 'THEME'
        else:
            shading.background_color = _BACKGROUNDS[index]
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.space_data is not None and context.space_data.type == 'VIEW_3D'


class MAYA_OT_toggle_attribute_editor(bpy.types.Operator):
    """Switch the right panel between Channel Box (Object tab) and Attribute Editor (Modifiers tab)"""
    bl_idname = "maya.toggle_attribute_editor"
    bl_label = "Attribute Editor"

    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                space = area.spaces.active
                try:
                    space.context = 'MODIFIER' if space.context == 'OBJECT' else 'OBJECT'
                except TypeError:
                    space.context = 'OBJECT'
                return {'FINISHED'}
        return bpy.ops.maya.show_attributes(tab='OBJECT')


classes = (
    MAYA_OT_group,
    MAYA_OT_ungroup,
    MAYA_OT_duplicate_with_transform,
    MAYA_OT_delete_by_type,
    MAYA_OT_delete_all_by_type,
    MAYA_OT_match_transforms,
    MAYA_OT_add_attribute,
    MAYA_OT_boolean,
    MAYA_OT_loft,
    MAYA_OT_revolve,
    MAYA_OT_planar,
    MAYA_OT_extrude_curve,
    MAYA_OT_add_lattice,
    MAYA_OT_nonlinear,
    MAYA_OT_pole_vector,
    MAYA_OT_quick_rig,
    MAYA_OT_add_hair,
    MAYA_OT_import_audio,
    MAYA_OT_quad_draw,
    MAYA_OT_target_weld,
    MAYA_OT_convert_selection,
    MAYA_OT_pickwalk,
    MAYA_OT_set_menu_set,
    MAYA_OT_soft_select,
    MAYA_OT_pivot_edit,
    MAYA_OT_cycle_background,
    MAYA_OT_toggle_attribute_editor,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
