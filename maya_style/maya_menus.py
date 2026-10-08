"""Maya main menu bar: common menus + menu sets (Modeling / Rigging / Animation / Rendering).

Like Maya's status line dropdown, switching the menu set swaps the menus
shown after File / Edit / Create / Select / Modify / Display / Windows.
"""

import bpy
from bpy.props import EnumProperty, StringProperty

MENU_SETS = (
    ('MODELING', "Modeling", "Mesh, Edit Mesh, Mesh Tools, Mesh Display, Curves, Deform, UV"),
    ('RIGGING', "Rigging", "Skeleton, Skin, Deform, Constrain, Control"),
    ('ANIMATION', "Animation", "Key, Playback, Visualize, Deform, Constrain"),
    ('RENDERING', "Rendering", "Lighting/Shading, Texturing, Render"),
)

COMMON_MENUS = ("MAYA_MT_create", "MAYA_MT_select", "MAYA_MT_modify", "MAYA_MT_display", "MAYA_MT_windows")

SET_MENUS = {
    'MODELING': ("MAYA_MT_mesh", "MAYA_MT_edit_mesh", "MAYA_MT_mesh_tools", "MAYA_MT_mesh_display",
                 "MAYA_MT_curves", "MAYA_MT_deform", "MAYA_MT_uv"),
    'RIGGING': ("MAYA_MT_skeleton", "MAYA_MT_skin", "MAYA_MT_deform", "MAYA_MT_constrain", "MAYA_MT_control"),
    'ANIMATION': ("MAYA_MT_key", "MAYA_MT_playback", "MAYA_MT_visualize", "MAYA_MT_deform", "MAYA_MT_constrain"),
    'RENDERING': ("MAYA_MT_lighting_shading", "MAYA_MT_texturing", "MAYA_MT_render"),
}


def op(layout, idname, text, icon='NONE', **props):
    o = layout.operator(idname, text=text, icon=icon)
    for key, value in props.items():
        setattr(o, key, value)
    return o


def is_edit_mesh(context):
    return context.mode == 'EDIT_MESH'


# ---------------------------------------------------------------------------
# Helper operators
# ---------------------------------------------------------------------------

class MAYA_OT_open_editor(bpy.types.Operator):
    """Open this editor in a new window (like Maya's Windows menu)"""
    bl_idname = "maya.open_editor"
    bl_label = "Open Editor"

    ui_type: StringProperty()

    def execute(self, context):
        before = set(w.as_pointer() for w in context.window_manager.windows)
        bpy.ops.wm.window_new()
        for window in context.window_manager.windows:
            if window.as_pointer() not in before:
                area = window.screen.areas[0]
                try:
                    area.ui_type = self.ui_type
                except TypeError:
                    self.report({'WARNING'}, "Editor not available: " + self.ui_type)
                return {'FINISHED'}
        return {'CANCELLED'}


class MAYA_OT_select_all(bpy.types.Operator):
    """Select / deselect / invert in object or component mode"""
    bl_idname = "maya.select_all"
    bl_label = "Select All"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(items=(('SELECT', "All", ""), ('DESELECT', "Deselect", ""), ('INVERT', "Invert", "")))

    def execute(self, context):
        mode = context.mode
        if mode == 'EDIT_MESH':
            return bpy.ops.mesh.select_all(action=self.action)
        if mode in {'EDIT_CURVE', 'EDIT_SURFACE'}:
            return bpy.ops.curve.select_all(action=self.action)
        if mode == 'EDIT_ARMATURE':
            return bpy.ops.armature.select_all(action=self.action)
        if mode == 'POSE':
            return bpy.ops.pose.select_all(action=self.action)
        return bpy.ops.object.select_all(action=self.action)


class MAYA_OT_toggle_snap(bpy.types.Operator):
    """Toggle snapping to this element (Maya status line snap buttons)"""
    bl_idname = "maya.toggle_snap"
    bl_label = "Toggle Snap"

    element: EnumProperty(items=(('GRID', "Grid", ""), ('EDGE', "Curve / Edge", ""), ('VERTEX', "Point", ""),
                                 ('FACE', "Surface", "")))

    def execute(self, context):
        ts = context.scene.tool_settings
        element = self.element
        if element == 'GRID' and 'GRID' not in ts.bl_rna.properties["snap_elements"].enum_items.keys():
            element = 'INCREMENT'
        if ts.use_snap and element in ts.snap_elements:
            ts.use_snap = False
        else:
            ts.snap_elements = {element}
            if element in {'GRID', 'INCREMENT'}:
                ts.use_snap_grid_absolute = True
            ts.use_snap = True
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Common menus
# ---------------------------------------------------------------------------

class MAYA_MT_create_polygons(bpy.types.Menu):
    bl_label = "Polygon Primitives"

    def draw(self, context):
        lay = self.layout
        op(lay, "mesh.primitive_uv_sphere_add", "Sphere", 'MESH_UVSPHERE')
        op(lay, "mesh.primitive_cube_add", "Cube", 'MESH_CUBE')
        op(lay, "mesh.primitive_cylinder_add", "Cylinder", 'MESH_CYLINDER')
        op(lay, "mesh.primitive_cone_add", "Cone", 'MESH_CONE')
        op(lay, "mesh.primitive_torus_add", "Torus", 'MESH_TORUS')
        op(lay, "mesh.primitive_plane_add", "Plane", 'MESH_PLANE')
        op(lay, "mesh.primitive_circle_add", "Disc", 'MESH_CIRCLE', fill_type='NGON')
        op(lay, "mesh.primitive_ico_sphere_add", "Platonic Solid", 'MESH_ICOSPHERE')
        op(lay, "mesh.primitive_grid_add", "Grid", 'MESH_GRID')
        op(lay, "mesh.primitive_monkey_add", "Monkey", 'MESH_MONKEY')


class MAYA_MT_create_nurbs(bpy.types.Menu):
    bl_label = "NURBS Primitives"

    def draw(self, context):
        lay = self.layout
        op(lay, "surface.primitive_nurbs_surface_sphere_add", "Sphere", 'SURFACE_NSPHERE')
        op(lay, "surface.primitive_nurbs_surface_cylinder_add", "Cylinder", 'SURFACE_NCYLINDER')
        op(lay, "surface.primitive_nurbs_surface_surface_add", "Plane", 'SURFACE_NSURFACE')
        op(lay, "surface.primitive_nurbs_surface_torus_add", "Torus", 'SURFACE_NTORUS')
        op(lay, "curve.primitive_nurbs_circle_add", "Circle", 'CURVE_NCIRCLE')


class MAYA_MT_create_curves(bpy.types.Menu):
    bl_label = "Curve Tools"

    def draw(self, context):
        lay = self.layout
        op(lay, "curve.primitive_bezier_curve_add", "Bezier Curve", 'CURVE_BEZCURVE')
        op(lay, "curve.primitive_nurbs_curve_add", "NURBS Curve", 'CURVE_NCURVE')
        op(lay, "curve.primitive_bezier_circle_add", "Circle", 'CURVE_BEZCIRCLE')
        op(lay, "curve.primitive_nurbs_path_add", "Path", 'CURVE_PATH')


class MAYA_MT_create_lights(bpy.types.Menu):
    bl_label = "Lights"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.light_add", "Ambient / Sun Light", 'LIGHT_SUN', type='SUN')
        op(lay, "object.light_add", "Point Light", 'LIGHT_POINT', type='POINT')
        op(lay, "object.light_add", "Spot Light", 'LIGHT_SPOT', type='SPOT')
        op(lay, "object.light_add", "Area Light", 'LIGHT_AREA', type='AREA')


class MAYA_MT_create(bpy.types.Menu):
    bl_label = "Create"

    def draw(self, context):
        lay = self.layout
        lay.menu("MAYA_MT_create_nurbs", icon='SURFACE_DATA')
        lay.menu("MAYA_MT_create_polygons", icon='MESH_DATA')
        lay.separator()
        lay.menu("MAYA_MT_create_lights", icon='LIGHT')
        op(lay, "object.camera_add", "Cameras", 'CAMERA_DATA')
        lay.separator()
        lay.menu("MAYA_MT_create_curves", icon='CURVE_DATA')
        op(lay, "object.text_add", "Type", 'OUTLINER_OB_FONT')
        lay.separator()
        op(lay, "object.empty_add", "Locator", 'OUTLINER_OB_EMPTY', type='PLAIN_AXES')
        op(lay, "object.empty_add", "Empty Group", 'EMPTY_AXIS', type='PLAIN_AXES')
        op(lay, "object.armature_add", "Joint", 'BONE_DATA')


class MAYA_MT_select(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.select_all", "All", action='SELECT')
        op(lay, "maya.select_all", "Deselect All", action='DESELECT')
        op(lay, "maya.select_all", "Inverse", action='INVERT')
        lay.separator()
        if is_edit_mesh(context):
            op(lay, "mesh.select_more", "Grow")
            op(lay, "mesh.select_less", "Shrink")
            op(lay, "mesh.select_linked", "Select Shell")
            op(lay, "mesh.select_similar", "Similar")
            op(lay, "mesh.select_nth", "Checker")
            op(lay, "mesh.select_mirror", "Mirror")
            lay.separator()
            op(lay, "mesh.select_non_manifold", "Border / Non-manifold")
            op(lay, "mesh.select_face_by_sides", "By Number of Sides")
            op(lay, "mesh.select_random", "Random")
        else:
            op(lay, "object.select_grouped", "Hierarchy", type='CHILDREN_RECURSIVE', extend=True)
            op(lay, "object.select_grouped", "Similar (Type)", type='TYPE', extend=True)
            op(lay, "object.select_mirror", "Mirror")
            op(lay, "object.select_random", "Random")
            lay.separator()
            lay.operator_menu_enum("object.select_by_type", "type", text="All by Type")
            op(lay, "object.select_pattern", "By Name...")


class MAYA_MT_modify(bpy.types.Menu):
    bl_label = "Modify"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.freeze_transforms", "Freeze Transformations", 'FREEZE')
        op(lay, "object.transforms_to_deltas", "Reset Transformations (to Deltas)")
        op(lay, "object.location_clear", "Clear Translate")
        op(lay, "object.rotation_clear", "Clear Rotate")
        op(lay, "object.scale_clear", "Clear Scale")
        lay.separator()
        op(lay, "maya.center_pivot", "Center Pivot", 'PIVOT_BOUNDBOX')
        op(lay, "object.origin_set", "Pivot to World Origin", type='ORIGIN_CURSOR')
        lay.separator()
        op(lay, "object.join", "Combine", 'SELECT_EXTEND')
        op(lay, "maya.delete_history", "Delete History", 'TRASH')
        op(lay, "object.convert", "Convert to Polygons", 'OUTLINER_OB_MESH', target='MESH')
        lay.separator()
        op(lay, "object.parent_set", "Parent", 'LINKED', type='OBJECT')
        op(lay, "object.parent_clear", "Unparent", 'UNLINKED', type='CLEAR_KEEP_TRANSFORM')
        op(lay, "object.duplicate_move", "Duplicate", 'DUPLICATE')
        op(lay, "object.duplicate_move_linked", "Duplicate Instance", 'LINKED')
        op(lay, "object.make_single_user", "Convert Instance to Object", object=True, obdata=True)


class MAYA_MT_display(bpy.types.Menu):
    bl_label = "Display"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.set_shading", "Wireframe (4)", 'SHADING_WIRE', shading='WIREFRAME')
        op(lay, "maya.set_shading", "Smooth Shade (5)", 'SHADING_SOLID', shading='SOLID')
        op(lay, "maya.set_shading", "Textured (6)", 'SHADING_TEXTURE', shading='MATERIAL')
        op(lay, "maya.set_shading", "Lighting (7)", 'SHADING_RENDERED', shading='RENDERED')
        lay.separator()
        op(lay, "object.hide_view_set", "Hide Selection (Ctrl+H)", 'HIDE_ON', unselected=False)
        op(lay, "object.hide_view_clear", "Show All (Shift+H)", 'HIDE_OFF')
        op(lay, "object.hide_view_set", "Isolate (Alt+H)", unselected=True)
        lay.separator()
        op(lay, "maya.smooth_preview", "Polygon Display: Original (1)", level='1')
        op(lay, "maya.smooth_preview", "Polygon Display: Cage + Smooth (2)", level='2')
        op(lay, "maya.smooth_preview", "Polygon Display: Smooth (3)", level='3')
        lay.separator()
        op(lay, "screen.region_quadview", "Four View / Single View (Space)", 'VIEW_PERSPECTIVE')
        op(lay, "view3d.view_selected", "Frame Selection (F)", 'ZOOM_SELECTED')
        op(lay, "view3d.view_all", "Frame All (A)", 'ZOOM_ALL')
        space = context.space_data
        if space is not None and space.type == 'VIEW_3D':
            lay.separator()
            lay.prop(space.overlay, "show_floor", text="Grid")
            lay.prop(space.overlay, "show_wireframes", text="Wireframe on Shaded")


class MAYA_MT_windows(bpy.types.Menu):
    bl_label = "Windows"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.open_editor", "Outliner", 'OUTLINER', ui_type='OUTLINER')
        op(lay, "maya.show_attributes", "Attribute Editor", 'PROPERTIES', tab='OBJECT')
        lay.separator()
        op(lay, "maya.open_editor", "Graph Editor", 'GRAPH', ui_type='FCURVES')
        op(lay, "maya.open_editor", "Dope Sheet", 'ACTION', ui_type='DOPESHEET')
        op(lay, "maya.open_editor", "Time Editor (NLA)", 'NLA', ui_type='NLA_EDITOR')
        lay.separator()
        op(lay, "maya.open_editor", "Hypershade (Shader Editor)", 'NODE_MATERIAL', ui_type='ShaderNodeTree')
        op(lay, "maya.open_editor", "UV Editor", 'UV', ui_type='UV')
        op(lay, "maya.open_editor", "Node Editor (Geometry Nodes)", 'NODETREE', ui_type='GeometryNodeTree')
        lay.separator()
        op(lay, "maya.open_editor", "Script Editor (Python)", 'CONSOLE', ui_type='CONSOLE')
        op(lay, "maya.open_editor", "Text Editor", 'TEXT', ui_type='TEXT_EDITOR')
        lay.separator()
        op(lay, "screen.userpref_show", "Settings / Preferences", 'PREFERENCES')
        op(lay, "maya.setup_maya_ui", "Reset Maya Workspace", 'WORKSPACE')


# ---------------------------------------------------------------------------
# Modeling menu set
# ---------------------------------------------------------------------------

class MAYA_MT_mesh(bpy.types.Menu):
    bl_label = "Mesh"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.join", "Combine", 'SELECT_EXTEND')
        op(lay, "mesh.separate", "Separate", 'SELECT_SUBTRACT', type='LOOSE')
        lay.separator()
        op(lay, "maya.add_modifier", "Boolean", 'MOD_BOOLEAN', modifier='BOOLEAN')
        op(lay, "maya.add_modifier", "Mirror", 'MOD_MIRROR', modifier='MIRROR')
        op(lay, "maya.add_modifier", "Smooth", 'MOD_SUBSURF', modifier='SUBSURF')
        op(lay, "maya.add_modifier", "Reduce", 'MOD_DECIM', modifier='DECIMATE')
        op(lay, "maya.add_modifier", "Remesh", 'MOD_REMESH', modifier='REMESH')
        op(lay, "maya.add_modifier", "Solidify", 'MOD_SOLIDIFY', modifier='SOLIDIFY')
        lay.separator()
        op(lay, "mesh.fill_holes", "Fill Hole", 'SNAP_FACE')
        op(lay, "mesh.quads_convert_to_tris", "Triangulate", 'MOD_TRIANGULATE')
        op(lay, "mesh.tris_convert_to_quads", "Quadrangulate")
        op(lay, "mesh.remove_doubles", "Cleanup (Merge by Distance)", 'AUTOMERGE_OFF')


class MAYA_MT_edit_mesh(bpy.types.Menu):
    bl_label = "Edit Mesh"

    def draw(self, context):
        lay = self.layout
        op(lay, "view3d.edit_mesh_extrude_move_normal", "Extrude", 'FACESEL')
        op(lay, "mesh.bevel", "Bevel", 'MOD_BEVEL')
        op(lay, "mesh.bridge_edge_loops", "Bridge", 'MOD_LATTICE')
        op(lay, "mesh.inset", "Inset (Extrude Inward)", 'FULLSCREEN_EXIT')
        op(lay, "mesh.subdivide", "Add Divisions", 'MESH_GRID')
        lay.separator()
        op(lay, "mesh.merge", "Merge", 'AUTOMERGE_ON', type='CENTER')
        op(lay, "mesh.merge", "Merge to Last (Target Weld)", type='LAST')
        op(lay, "mesh.merge", "Collapse", type='COLLAPSE')
        op(lay, "mesh.dissolve_mode", "Delete Edge/Vertex", 'X')
        op(lay, "mesh.delete_edgeloop", "Delete Edge Loop")
        lay.separator()
        op(lay, "mesh.duplicate_move", "Duplicate", 'DUPLICATE')
        op(lay, "mesh.split", "Extract / Detach")
        op(lay, "mesh.poke", "Poke")
        op(lay, "mesh.wireframe", "Wedge / Wireframe")
        lay.separator()
        op(lay, "transform.edge_slide", "Edge Slide", 'ARROW_LEFTRIGHT')
        op(lay, "transform.vert_slide", "Vertex Slide")
        op(lay, "mesh.flip_normals", "Flip (Reverse Normals)", 'NORMALS_FACE')
        op(lay, "mesh.spin", "Spin")


class MAYA_MT_mesh_tools(bpy.types.Menu):
    bl_label = "Mesh Tools"

    def draw(self, context):
        lay = self.layout
        op(lay, "mesh.loopcut_slide", "Insert Edge Loop", 'MOD_MULTIRES')
        op(lay, "mesh.offset_edge_loops_slide", "Offset Edge Loop")
        op(lay, "mesh.knife_tool", "Multi-Cut", 'SCULPTMODE_HLT')
        op(lay, "mesh.bisect", "Slice (Bisect)")
        lay.separator()
        op(lay, "mesh.polybuild_face_at_cursor_move", "Quad Draw")
        op(lay, "mesh.edge_face_add", "Append to Polygon (Fill)")
        op(lay, "mesh.fill_grid", "Fill Grid")
        lay.separator()
        op(lay, "mesh.vertices_smooth", "Relax", 'MOD_SMOOTH')
        op(lay, "mesh.symmetrize", "Symmetrize", 'MOD_MIRROR')
        op(lay, "mesh.sort_elements", "Sort Elements")


class MAYA_MT_mesh_display(bpy.types.Menu):
    bl_label = "Mesh Display"

    def draw(self, context):
        lay = self.layout
        op(lay, "mesh.normals_make_consistent", "Conform (Recalculate Normals)", inside=False)
        op(lay, "mesh.flip_normals", "Reverse", 'NORMALS_FACE')
        lay.separator()
        op(lay, "mesh.faces_shade_smooth", "Soften Edge (Smooth Faces)", 'SMOOTHCURVE')
        op(lay, "mesh.faces_shade_flat", "Harden Edge (Flat Faces)", 'SHARPCURVE')
        op(lay, "mesh.mark_sharp", "Mark Hard Edges", clear=False)
        op(lay, "mesh.mark_sharp", "Clear Hard Edges", clear=True)
        lay.separator()
        op(lay, "object.shade_smooth", "Smooth Shade Object", 'SHADING_RENDERED')
        op(lay, "object.shade_flat", "Flat Shade Object", 'SHADING_SOLID')
        space = context.space_data
        if space is not None and space.type == 'VIEW_3D':
            lay.separator()
            lay.prop(space.overlay, "show_face_normals", text="Display Face Normals")
            lay.prop(space.overlay, "show_vertex_normals", text="Display Vertex Normals")
            lay.prop(space.overlay, "show_face_orientation", text="Face Orientation (Backfaces)")


class MAYA_MT_curves(bpy.types.Menu):
    bl_label = "Curves"

    def draw(self, context):
        lay = self.layout
        lay.menu("MAYA_MT_create_curves", icon='CURVE_DATA')
        lay.separator()
        op(lay, "curve.switch_direction", "Reverse Direction")
        op(lay, "curve.subdivide", "Insert Knot (Subdivide)")
        op(lay, "curve.cyclic_toggle", "Open/Close")
        op(lay, "curve.smooth", "Smooth")
        lay.separator()
        op(lay, "object.convert", "Convert to Mesh", 'OUTLINER_OB_MESH', target='MESH')
        op(lay, "object.convert", "Convert Mesh to Curve", 'OUTLINER_OB_CURVE', target='CURVE')


class MAYA_MT_deform(bpy.types.Menu):
    bl_label = "Deform"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.shape_key_add", "Blend Shape (Shape Key)", 'SHAPEKEY_DATA', from_mix=False)
        op(lay, "maya.add_modifier", "Lattice", 'MOD_LATTICE', modifier='LATTICE')
        op(lay, "maya.add_modifier", "Wrap (Shrinkwrap)", 'MOD_SHRINKWRAP', modifier='SHRINKWRAP')
        op(lay, "maya.add_modifier", "Wire / Curve", 'MOD_CURVE', modifier='CURVE')
        lay.separator()
        op(lay, "maya.add_modifier", "Nonlinear: Bend / Twist (Simple Deform)", 'MOD_SIMPLEDEFORM', modifier='SIMPLE_DEFORM')
        op(lay, "maya.add_modifier", "Nonlinear: Wave", 'MOD_WAVE', modifier='WAVE')
        op(lay, "maya.add_modifier", "Sculpt (Cast)", 'MOD_CAST', modifier='CAST')
        op(lay, "maya.add_modifier", "Delta Mush (Smooth)", 'MOD_SMOOTH', modifier='CORRECTIVE_SMOOTH')


class MAYA_MT_uv(bpy.types.Menu):
    bl_label = "UV"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.open_uv_editor", "UV Editor", 'UV')
        lay.separator()
        op(lay, "uv.smart_project", "Automatic", 'UV_DATA')
        op(lay, "uv.unwrap", "Unfold", 'UV')
        op(lay, "uv.cube_project", "Cube Projection", 'MESH_CUBE')
        op(lay, "uv.cylinder_project", "Cylindrical", 'MESH_CYLINDER')
        op(lay, "uv.sphere_project", "Spherical", 'MESH_UVSPHERE')
        op(lay, "uv.project_from_view", "Planar", 'VIEW_CAMERA')
        lay.separator()
        op(lay, "mesh.mark_seam", "Cut", clear=False)
        op(lay, "mesh.mark_seam", "Sew", clear=True)


# ---------------------------------------------------------------------------
# Rigging menu set
# ---------------------------------------------------------------------------

class MAYA_MT_skeleton(bpy.types.Menu):
    bl_label = "Skeleton"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.armature_add", "Create Joints", 'BONE_DATA')
        op(lay, "armature.extrude_move", "Extrude Joint")
        op(lay, "armature.subdivide", "Insert Joint")
        op(lay, "armature.parent_set", "Connect Joint", type='CONNECTED')
        op(lay, "armature.parent_clear", "Disconnect Joint", type='DISCONNECT')
        lay.separator()
        op(lay, "pose.ik_add", "Create IK Handle", 'CON_KINEMATIC')
        op(lay, "pose.ik_clear", "Remove IK")
        lay.separator()
        op(lay, "armature.symmetrize", "Mirror Joints", 'MOD_MIRROR')
        op(lay, "armature.calculate_roll", "Orient Joint", type='GLOBAL_POS_Z')
        lay.separator()
        op(lay, "object.mode_set", "Pose Mode", 'POSE_HLT', mode='POSE')
        op(lay, "object.mode_set", "Edit Joints", 'EDITMODE_HLT', mode='EDIT')


class MAYA_MT_skin(bpy.types.Menu):
    bl_label = "Skin"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.parent_set", "Bind Skin", 'MOD_ARMATURE', type='ARMATURE_AUTO')
        op(lay, "object.parent_set", "Bind Skin (Empty Weights)", type='ARMATURE_NAME')
        op(lay, "object.parent_clear", "Unbind Skin", type='CLEAR')
        lay.separator()
        op(lay, "object.mode_set", "Paint Skin Weights", 'WPAINT_HLT', mode='WEIGHT_PAINT')
        op(lay, "object.vertex_group_normalize_all", "Normalize Weights")
        op(lay, "object.vertex_group_mirror", "Mirror Skin Weights")
        op(lay, "object.vertex_group_clean", "Prune Small Weights")


class MAYA_MT_constrain(bpy.types.Menu):
    bl_label = "Constrain"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.constraint_add", "Parent", 'CON_CHILDOF', type='CHILD_OF')
        op(lay, "object.constraint_add", "Point", 'CON_LOCLIKE', type='COPY_LOCATION')
        op(lay, "object.constraint_add", "Orient", 'CON_ROTLIKE', type='COPY_ROTATION')
        op(lay, "object.constraint_add", "Scale", 'CON_SIZELIKE', type='COPY_SCALE')
        op(lay, "object.constraint_add", "Aim", 'CON_TRACKTO', type='DAMPED_TRACK')
        op(lay, "object.constraint_add", "Pole Vector / Locked Track", 'CON_LOCKTRACK', type='LOCKED_TRACK')
        lay.separator()
        op(lay, "object.constraint_add", "Geometry (Shrinkwrap)", 'CON_SHRINKWRAP', type='SHRINKWRAP')
        op(lay, "object.constraint_add", "Motion Path (Follow Path)", 'CON_FOLLOWPATH', type='FOLLOW_PATH')
        lay.separator()
        op(lay, "object.constraints_clear", "Remove Constraints")


class MAYA_MT_control(bpy.types.Menu):
    bl_label = "Control"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.empty_add", "Circle Control", 'MESH_CIRCLE', type='CIRCLE')
        op(lay, "object.empty_add", "Cube Control", 'MESH_CUBE', type='CUBE')
        op(lay, "object.empty_add", "Arrows Control", 'EMPTY_ARROWS', type='ARROWS')
        op(lay, "object.empty_add", "Locator", 'EMPTY_AXIS', type='PLAIN_AXES')
        lay.separator()
        op(lay, "object.parent_set", "Parent to Control", 'LINKED', type='OBJECT')


# ---------------------------------------------------------------------------
# Animation menu set
# ---------------------------------------------------------------------------

class MAYA_MT_key(bpy.types.Menu):
    bl_label = "Key"

    def draw(self, context):
        lay = self.layout
        op(lay, "anim.keyframe_insert", "Set Key (S)", 'KEY_HLT')
        op(lay, "anim.keyframe_delete_v3d", "Delete Key", 'KEY_DEHLT')
        op(lay, "anim.keyframe_insert_menu", "Set Key Options...", type='Location')
        lay.separator()
        op(lay, "anim.keyframe_clear_v3d", "Clear All Keys")
        op(lay, "anim.keying_set_active_set", "Keying Set...")
        lay.separator()
        op(lay, "maya.open_editor", "Graph Editor", 'GRAPH', ui_type='FCURVES')
        op(lay, "maya.open_editor", "Dope Sheet", 'ACTION', ui_type='DOPESHEET')
        lay.separator()
        lay.prop(context.scene.tool_settings, "use_keyframe_insert_auto", text="Auto Key")


class MAYA_MT_playback(bpy.types.Menu):
    bl_label = "Playback"

    def draw(self, context):
        lay = self.layout
        op(lay, "screen.animation_play", "Play / Stop (Alt+V)", 'PLAY')
        op(lay, "screen.animation_play", "Play Backwards", 'PLAY_REVERSE', reverse=True)
        lay.separator()
        op(lay, "screen.frame_jump", "Go to Start", 'REW', end=False)
        op(lay, "screen.keyframe_jump", "Previous Key", 'PREV_KEYFRAME', next=False)
        op(lay, "screen.keyframe_jump", "Next Key", 'NEXT_KEYFRAME', next=True)
        op(lay, "screen.frame_jump", "Go to End", 'FF', end=True)
        lay.separator()
        lay.prop(context.scene.render, "fps", text="Frame Rate")


class MAYA_MT_visualize(bpy.types.Menu):
    bl_label = "Visualize"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.paths_calculate", "Create Motion Trail", 'IPO_BEZIER')
        op(lay, "object.paths_clear", "Delete Motion Trail")
        lay.separator()
        op(lay, "render.opengl", "Playblast (Viewport Render Animation)", 'RENDER_ANIMATION', animation=True)
        op(lay, "render.opengl", "Viewport Render Frame", 'RENDER_STILL')
        op(lay, "nla.bake", "Bake Simulation / Animation", 'ACTION')


# ---------------------------------------------------------------------------
# Rendering menu set
# ---------------------------------------------------------------------------

class MAYA_MT_lighting_shading(bpy.types.Menu):
    bl_label = "Lighting/Shading"

    def draw(self, context):
        lay = self.layout
        lay.menu("MAYA_MT_rmb_new_material", text="Assign New Material", icon='MATERIAL')
        lay.menu("MAYA_MT_rmb_existing_material", text="Assign Existing Material", icon='MATERIAL')
        op(lay, "maya.show_attributes", "Material Attributes...", tab='MATERIAL')
        lay.separator()
        lay.menu("MAYA_MT_create_lights", icon='LIGHT')
        op(lay, "maya.show_attributes", "Environment (World)", 'WORLD', tab='WORLD')
        lay.separator()
        op(lay, "maya.open_editor", "Hypershade (Shader Editor)", 'NODE_MATERIAL', ui_type='ShaderNodeTree')


class MAYA_MT_texturing(bpy.types.Menu):
    bl_label = "Texturing"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.mode_set", "3D Paint Tool (Texture Paint)", 'TPAINT_HLT', mode='TEXTURE_PAINT')
        op(lay, "object.mode_set", "Vertex Color Paint", 'VPAINT_HLT', mode='VERTEX_PAINT')
        lay.separator()
        op(lay, "maya.open_editor", "Image / UV Editor", 'IMAGE_DATA', ui_type='UV')
        op(lay, "image.new", "New Image Texture", 'TEXTURE')


class MAYA_MT_render(bpy.types.Menu):
    bl_label = "Render"

    def draw(self, context):
        lay = self.layout
        op(lay, "render.render", "Render Current Frame", 'RENDER_STILL', use_viewport=True)
        op(lay, "render.render", "Render Sequence", 'RENDER_ANIMATION', animation=True, use_viewport=True)
        op(lay, "maya.set_shading", "IPR Render (Viewport Rendered)", 'SHADING_RENDERED', shading='RENDERED')
        lay.separator()
        op(lay, "maya.show_attributes", "Render Settings", 'PROPERTIES', tab='RENDER')
        op(lay, "maya.show_attributes", "Output Settings", 'OUTPUT', tab='OUTPUT')
        op(lay, "render.view_show", "Render View", 'RENDER_RESULT')


# ---------------------------------------------------------------------------

def draw_menu_bar(layout, context):
    wm = context.window_manager
    for idname in COMMON_MENUS + SET_MENUS[wm.maya_menu_set]:
        layout.menu(idname)


classes = (
    MAYA_OT_open_editor,
    MAYA_OT_select_all,
    MAYA_OT_toggle_snap,
    MAYA_MT_create_polygons,
    MAYA_MT_create_nurbs,
    MAYA_MT_create_curves,
    MAYA_MT_create_lights,
    MAYA_MT_create,
    MAYA_MT_select,
    MAYA_MT_modify,
    MAYA_MT_display,
    MAYA_MT_windows,
    MAYA_MT_mesh,
    MAYA_MT_edit_mesh,
    MAYA_MT_mesh_tools,
    MAYA_MT_mesh_display,
    MAYA_MT_curves,
    MAYA_MT_deform,
    MAYA_MT_uv,
    MAYA_MT_skeleton,
    MAYA_MT_skin,
    MAYA_MT_constrain,
    MAYA_MT_control,
    MAYA_MT_key,
    MAYA_MT_playback,
    MAYA_MT_visualize,
    MAYA_MT_lighting_shading,
    MAYA_MT_texturing,
    MAYA_MT_render,
)


def register():
    bpy.types.WindowManager.maya_menu_set = EnumProperty(
        name="Menu Set", description="Maya menu set: changes the menus in the top bar",
        items=MENU_SETS, default='MODELING',
    )
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.maya_menu_set
