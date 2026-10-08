"""Maya main menu bar: common menus + menu sets (Modeling / Rigging / Animation / FX / Rendering).

Like Maya's status line dropdown (or F2-F6), switching the menu set swaps the
menus shown after File / Edit / Create / Select / Modify / Display / Windows.
Items whose Blender operator doesn't exist in this Blender build are shown
greyed out instead of failing.
"""

import bpy

from .operators import set_props
from bpy.props import EnumProperty, StringProperty

MENU_SETS = (
    ('MODELING', "Modeling", "Mesh, Edit Mesh, Mesh Tools, Mesh Display, Curves, Surfaces, Deform, UV, Generate, Cache"),
    ('RIGGING', "Rigging", "Skeleton, Skin, Deform, Constrain, Control, Cache"),
    ('ANIMATION', "Animation", "Key, Playback, Audio, Visualize, Deform, Constrain, Cache"),
    ('FX', "FX", "nParticles, Fluids, nCloth, nHair, Fields/Solvers, Effects, Cache"),
    ('RENDERING', "Rendering", "Lighting/Shading, Texturing, Render, Toon, Stereo"),
)

COMMON_MENUS = ("MAYA_MT_file", "MAYA_MT_edit", "MAYA_MT_create", "MAYA_MT_select", "MAYA_MT_modify",
                "MAYA_MT_display", "MAYA_MT_windows")

SET_MENUS = {
    'MODELING': ("MAYA_MT_mesh", "MAYA_MT_edit_mesh", "MAYA_MT_mesh_tools", "MAYA_MT_mesh_display",
                 "MAYA_MT_curves", "MAYA_MT_surfaces", "MAYA_MT_deform", "MAYA_MT_uv", "MAYA_MT_generate",
                 "MAYA_MT_cache"),
    'RIGGING': ("MAYA_MT_skeleton", "MAYA_MT_skin", "MAYA_MT_deform", "MAYA_MT_constrain", "MAYA_MT_control",
                "MAYA_MT_cache"),
    'ANIMATION': ("MAYA_MT_key", "MAYA_MT_playback", "MAYA_MT_audio", "MAYA_MT_visualize", "MAYA_MT_deform",
                  "MAYA_MT_constrain", "MAYA_MT_cache"),
    'FX': ("MAYA_MT_nparticles", "MAYA_MT_fluids", "MAYA_MT_ncloth", "MAYA_MT_nhair", "MAYA_MT_fields",
           "MAYA_MT_effects", "MAYA_MT_cache"),
    'RENDERING': ("MAYA_MT_lighting_shading", "MAYA_MT_texturing", "MAYA_MT_render", "MAYA_MT_toon",
                  "MAYA_MT_stereo"),
}

_op_exists_cache = {}


def op_exists(idname):
    if idname not in _op_exists_cache:
        mod, name = idname.split(".")
        _op_exists_cache[idname] = hasattr(bpy.ops, mod) and name in dir(getattr(bpy.ops, mod))
    return _op_exists_cache[idname]


def _view3d_override():
    """(window, area, region) of the biggest 3D viewport in the current window."""
    context = bpy.context
    window = context.window
    if window is None:
        return None
    areas = [a for a in window.screen.areas if a.type == 'VIEW_3D']
    if not areas:
        return None
    area = max(areas, key=lambda a: a.width * a.height)
    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
    return window, area, region


def _get_op(idname):
    mod, name = idname.split(".")
    return getattr(getattr(bpy.ops, mod), name)


def _poll_in_view3d(idname, override):
    window, area, region = override
    try:
        with bpy.context.temp_override(window=window, area=area, region=region):
            return _get_op(idname).poll()
    except Exception:
        return True


def op(layout, idname, text, icon='NONE', **props):
    if not op_exists(idname):
        row = layout.row()
        row.enabled = False
        row.label(text=text + "  (not available)", icon=icon)
        return None
    area = bpy.context.area
    override = _view3d_override() if (area is None or area.type != 'VIEW_3D') else None
    if override is not None:
        # Drawn in the top bar: run the command in the 3D viewport, like Maya's main menus do.
        row = layout.row()
        row.enabled = _poll_in_view3d(idname, override)
        o = row.operator("maya.call_in_view3d", text=text, icon=icon)
        o.idname = idname
        o.props = repr(props)
        return None
    o = layout.operator(idname, text=text, icon=icon)
    set_props(o, props)
    return o


def prop(layout, data, name, text):
    """layout.prop that skips properties this Blender version doesn't have."""
    if data is not None and hasattr(data, name):
        layout.prop(data, name, text=text)


def is_edit_mesh(context):
    return context.mode == 'EDIT_MESH'


def view3d_space(context):
    space = context.space_data
    if space is not None and space.type == 'VIEW_3D':
        return space
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            return area.spaces.active
    return None


# ---------------------------------------------------------------------------
# Helper operators used by the menus
# ---------------------------------------------------------------------------

class MAYA_OT_call_in_view3d(bpy.types.Operator):
    """Run a command in the 3D viewport (used by the menu bar)"""
    bl_idname = "maya.call_in_view3d"
    bl_label = "Run in 3D Viewport"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    idname: StringProperty(options={'HIDDEN'})
    props: StringProperty(default="{}", options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        try:
            return _get_op(properties.idname).get_rna_type().description
        except Exception:
            return ""

    def invoke(self, context, event):
        import ast
        props = ast.literal_eval(self.props) if self.props else {}
        override = _view3d_override()
        fn = _get_op(self.idname)
        try:
            if override is None:
                fn('INVOKE_DEFAULT', **props)
            else:
                window, area, region = override
                with context.temp_override(window=window, area=area, region=region):
                    fn('INVOKE_DEFAULT', **props)
        except RuntimeError as ex:
            self.report({'WARNING'}, str(ex).replace("Error: ", "").strip())
            return {'CANCELLED'}
        return {'FINISHED'}


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


class MAYA_OT_delete(bpy.types.Operator):
    """Delete the selection (objects or components)"""
    bl_idname = "maya.delete"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            ts = context.tool_settings
            kind = 'VERT' if ts.mesh_select_mode[0] else 'EDGE' if ts.mesh_select_mode[1] else 'FACE'
            return bpy.ops.mesh.delete(type=kind)
        if context.mode == 'OBJECT':
            return bpy.ops.object.delete()
        return {'CANCELLED'}


class MAYA_OT_cut(bpy.types.Operator):
    """Copy the selected objects to the clipboard and delete them"""
    bl_idname = "maya.cut"
    bl_label = "Cut"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.selected_objects

    def execute(self, context):
        bpy.ops.view3d.copybuffer()
        bpy.ops.object.delete()
        return {'FINISHED'}


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


class MAYA_OT_toggle_region(bpy.types.Operator):
    """Show / hide this part of the 3D viewport (Maya: Display > UI Elements)"""
    bl_idname = "maya.toggle_region"
    bl_label = "Toggle UI Element"

    region: StringProperty()

    def execute(self, context):
        space = view3d_space(context)
        if space is None or not hasattr(space, self.region):
            return {'CANCELLED'}
        setattr(space, self.region, not getattr(space, self.region))
        return {'FINISHED'}


class MAYA_OT_object_display(bpy.types.Operator):
    """Object display options (Maya: Display > Object Display)"""
    bl_idname = "maya.object_display"
    bl_label = "Object Display"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(items=(
        ('TEMPLATE', "Template", "Show as wireframe, not selectable"),
        ('UNTEMPLATE', "Untemplate", ""),
        ('BOUNDING_BOX', "Bounding Box", ""),
        ('NO_BOUNDING_BOX', "No Bounding Box", ""),
        ('XRAY', "X-Ray (In Front)", ""),
        ('LOCAL_AXES', "Local Rotation Axes", ""),
    ))

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        for obj in context.selected_objects:
            if self.mode == 'TEMPLATE':
                obj.display_type = 'WIRE'
                obj.hide_select = True
                obj.select_set(False)
            elif self.mode == 'UNTEMPLATE':
                obj.display_type = 'TEXTURED'
                obj.hide_select = False
            elif self.mode == 'BOUNDING_BOX':
                obj.display_type = 'BOUNDS'
            elif self.mode == 'NO_BOUNDING_BOX':
                obj.display_type = 'TEXTURED'
            elif self.mode == 'XRAY':
                obj.show_in_front = not obj.show_in_front
            elif self.mode == 'LOCAL_AXES':
                obj.show_axis = not obj.show_axis
        return {'FINISHED'}


class MAYA_OT_untemplate_all(bpy.types.Operator):
    """Make every templated (unselectable) object selectable again"""
    bl_idname = "maya.untemplate_all"
    bl_label = "Untemplate All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.scene.objects:
            if obj.hide_select:
                obj.hide_select = False
                if obj.display_type == 'WIRE':
                    obj.display_type = 'TEXTURED'
        return {'FINISHED'}


class MAYA_OT_wireframe_color(bpy.types.Operator):
    """Give the selected objects a display color (shown when Viewport Shading color is 'Object')"""
    bl_idname = "maya.wireframe_color"
    bl_label = "Wireframe Color"
    bl_options = {'REGISTER', 'UNDO'}

    color: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', size=4, min=0, max=1,
                                         default=(0.2, 0.6, 1.0, 1.0))

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        for obj in context.selected_objects:
            obj.color = self.color
        space = view3d_space(context)
        if space is not None:
            space.shading.color_type = 'OBJECT'
            space.shading.wireframe_color_type = 'OBJECT'
        return {'FINISHED'}


class MAYA_OT_open_url(bpy.types.Operator):
    """Open a web page"""
    bl_idname = "maya.open_url"
    bl_label = "Open URL"

    url: StringProperty()

    def execute(self, context):
        bpy.ops.wm.url_open(url=self.url)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# File / Edit
# ---------------------------------------------------------------------------

class MAYA_MT_file(bpy.types.Menu):
    bl_label = "File"

    def draw(self, context):
        lay = self.layout
        op(lay, "wm.read_homefile", "New Scene  (Ctrl+N)", 'FILE_NEW')
        op(lay, "wm.open_mainfile", "Open Scene...  (Ctrl+O)", 'FILE_FOLDER')
        op(lay, "wm.save_mainfile", "Save Scene  (Ctrl+S)", 'FILE_TICK')
        op(lay, "wm.save_as_mainfile", "Save Scene As...  (Ctrl+Shift+S)")
        op(lay, "wm.save_mainfile", "Increment and Save", incremental=True)
        op(lay, "file.pack_all", "Archive Scene (Pack Resources)", 'PACKAGE')
        op(lay, "outliner.orphans_purge", "Optimize Scene Size (Purge Unused)", do_recursive=True)
        lay.separator()
        lay.menu("TOPBAR_MT_file_import", text="Import", icon='IMPORT')
        lay.menu("TOPBAR_MT_file_export", text="Export All", icon='EXPORT')
        op(lay, "export_scene.fbx", "Export Selection (FBX)...", use_selection=True)
        op(lay, "wm.append", "Import Scene (Append .blend)...", 'APPEND_BLEND')
        lay.separator()
        op(lay, "wm.link", "Create Reference (Link .blend)...", 'LINK_BLEND')
        op(lay, "maya.open_editor", "Reference Editor (Blender File view)", 'OUTLINER', ui_type='OUTLINER')
        op(lay, "file.find_missing_files", "File Path Editor: Find Missing Files...")
        op(lay, "file.make_paths_relative", "File Path Editor: Make Paths Relative")
        lay.separator()
        lay.menu("TOPBAR_MT_file_open_recent", text="Recent Files", icon='RECOVER_LAST')
        lay.separator()
        lay.menu("TOPBAR_MT_file", text="Blender File Menu", icon='BLENDER')
        op(lay, "wm.quit_blender", "Exit", 'QUIT')


class MAYA_MT_delete_by_type(bpy.types.Menu):
    bl_label = "Delete by Type"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.delete_by_type", "History", kind='HISTORY')
        op(lay, "maya.delete_by_type", "Channels (Keys)", kind='CHANNELS')
        op(lay, "maya.delete_by_type", "Constraints", kind='CONSTRAINTS')
        op(lay, "maya.delete_by_type", "Motion Paths", kind='MOTION_PATHS')
        op(lay, "maya.delete_by_type", "Rigid Bodies", kind='RIGID_BODIES')
        op(lay, "maya.delete_by_type", "Custom Attributes", kind='ATTRIBUTES')


class MAYA_MT_delete_all_by_type(bpy.types.Menu):
    bl_label = "Delete All by Type"

    def draw(self, context):
        lay = self.layout
        for key, text in (('CAMERA', "Cameras"), ('LIGHT', "Lights"), ('CURVE', "NURBS Curves"),
                          ('SURFACE', "NURBS Surfaces"), ('ARMATURE', "Joints"), ('EMPTY', "Locators / Groups"),
                          ('LATTICE', "Lattices"), ('FONT', "Type")):
            op(lay, "maya.delete_all_by_type", text, object_type=key)


class MAYA_MT_edit(bpy.types.Menu):
    bl_label = "Edit"

    def draw(self, context):
        lay = self.layout
        op(lay, "ed.undo", "Undo  (Ctrl+Z / Z)", 'LOOP_BACK')
        op(lay, "ed.redo", "Redo  (Ctrl+Y / Shift+Z)", 'LOOP_FORWARDS')
        op(lay, "screen.repeat_last", "Repeat Last  (G)")
        op(lay, "screen.repeat_history", "Recent Commands List...")
        op(lay, "ed.undo_history", "Undo History...")
        lay.separator()
        op(lay, "maya.cut", "Cut  (Ctrl+X)")
        op(lay, "view3d.copybuffer", "Copy  (Ctrl+C)", 'COPYDOWN')
        op(lay, "view3d.pastebuffer", "Paste  (Ctrl+V)", 'PASTEDOWN')
        lay.separator()
        op(lay, "maya.delete", "Delete  (Del)", 'X')
        lay.menu("MAYA_MT_delete_by_type")
        lay.menu("MAYA_MT_delete_all_by_type")
        lay.separator()
        op(lay, "wm.tool_set_by_id", "Select Tool  (Q)", 'RESTRICT_SELECT_OFF', name="builtin.select_box")
        op(lay, "wm.tool_set_by_id", "Lasso Tool", name="builtin.select_lasso")
        op(lay, "wm.tool_set_by_id", "Paint Selection Tool", name="builtin.select_circle")
        lay.separator()
        op(lay, "object.duplicate_move", "Duplicate  (Ctrl+D)", 'DUPLICATE')
        op(lay, "object.duplicate_move_linked", "Duplicate Special: Instance  (Ctrl+Shift+D)", 'LINKED')
        op(lay, "maya.duplicate_with_transform", "Duplicate with Transform  (Shift+D)")
        lay.separator()
        op(lay, "maya.group", "Group  (Ctrl+G)", 'GROUP')
        op(lay, "maya.ungroup", "Ungroup")
        op(lay, "object.parent_set", "Parent  (P)", 'LINKED', type='OBJECT', keep_transform=True)
        op(lay, "object.parent_clear", "Unparent  (Shift+P)", 'UNLINKED', type='CLEAR_KEEP_TRANSFORM')
        lay.separator()
        lay.menu("TOPBAR_MT_edit", text="Blender Edit Menu", icon='BLENDER')
        op(lay, "screen.userpref_show", "Preferences...", 'PREFERENCES')


# ---------------------------------------------------------------------------
# Create
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
        op(lay, "mesh.primitive_cone_add", "Pyramid", 'MESH_CONE', vertices=4)
        op(lay, "mesh.primitive_cylinder_add", "Prism", 'MESH_CYLINDER', vertices=3)
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
        op(lay, "surface.primitive_nurbs_surface_circle_add", "Square / Circle Surface", 'SURFACE_NCIRCLE')


class MAYA_MT_create_curves(bpy.types.Menu):
    bl_label = "Curve Tools"

    def draw(self, context):
        lay = self.layout
        op(lay, "curve.primitive_bezier_curve_add", "Bezier Curve", 'CURVE_BEZCURVE')
        op(lay, "curve.primitive_nurbs_curve_add", "CV / EP Curve", 'CURVE_NCURVE')
        op(lay, "curve.primitive_bezier_circle_add", "Circle", 'CURVE_BEZCIRCLE')
        op(lay, "curve.primitive_nurbs_path_add", "Path", 'CURVE_PATH')
        op(lay, "wm.tool_set_by_id", "Pencil Curve Tool (Draw)", 'GREASEPENCIL', name="builtin.draw")


class MAYA_MT_create_lights(bpy.types.Menu):
    bl_label = "Lights"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.light_add", "Directional / Ambient Light", 'LIGHT_SUN', type='SUN')
        op(lay, "object.light_add", "Point Light", 'LIGHT_POINT', type='POINT')
        op(lay, "object.light_add", "Spot Light", 'LIGHT_SPOT', type='SPOT')
        op(lay, "object.light_add", "Area Light", 'LIGHT_AREA', type='AREA')
        op(lay, "object.lightprobe_add", "Light Probe")


class MAYA_MT_create_cameras(bpy.types.Menu):
    bl_label = "Cameras"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.camera_add", "Camera", 'CAMERA_DATA')
        op(lay, "view3d.camera_to_view", "Align Camera to View")
        op(lay, "view3d.object_as_camera", "Look Through Selected Camera")


class MAYA_MT_create(bpy.types.Menu):
    bl_label = "Create"

    def draw(self, context):
        lay = self.layout
        lay.menu("MAYA_MT_create_nurbs", icon='SURFACE_DATA')
        lay.menu("MAYA_MT_create_polygons", icon='MESH_DATA')
        lay.separator()
        lay.menu("MAYA_MT_create_lights", icon='LIGHT')
        lay.menu("MAYA_MT_create_cameras", icon='CAMERA_DATA')
        lay.separator()
        lay.menu("MAYA_MT_create_curves", icon='CURVE_DATA')
        op(lay, "object.text_add", "Type", 'OUTLINER_OB_FONT')
        lay.separator()
        op(lay, "object.empty_add", "Locator", 'OUTLINER_OB_EMPTY', type='PLAIN_AXES')
        op(lay, "maya.group", "Empty Group", 'EMPTY_AXIS')
        op(lay, "object.armature_add", "Joint", 'BONE_DATA')
        op(lay, "object.empty_add", "Annotation / Arrow", 'EMPTY_ARROWS', type='SINGLE_ARROW')
        op(lay, "wm.tool_set_by_id", "Measure Tools", 'DRIVER_DISTANCE', name="builtin.measure")
        op(lay, "object.collection_instance_add", "Scene Assembly / Instance Collection...", 'OUTLINER_OB_GROUP_INSTANCE')


# ---------------------------------------------------------------------------
# Select
# ---------------------------------------------------------------------------

class MAYA_MT_convert_selection(bpy.types.Menu):
    bl_label = "Convert Selection"

    def draw(self, context):
        lay = self.layout
        for key, text in (('VERT', "To Vertices  (Ctrl+F9)"), ('EDGE', "To Edges  (Ctrl+F10)"),
                          ('FACE', "To Faces  (Ctrl+F11)"), ('UV', "To UVs  (Ctrl+F12)"),
                          ('VERT_FACE', "To Vertex Faces"), ('SHELL', "To Shell"), ('BORDER', "To Shell Border"),
                          ('EDGE_LOOP', "To Edge Loop"), ('EDGE_RING', "To Edge Ring"),
                          ('CONTAINED_EDGES', "To Contained Edges"), ('CONTAINED_FACES', "To Contained Faces")):
            op(lay, "maya.convert_selection", text, to=key)


class MAYA_MT_select(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.select_all", "All", action='SELECT')
        if not is_edit_mesh(context):
            lay.operator_menu_enum("object.select_by_type", "type", text="All by Type")
        op(lay, "maya.select_all", "Deselect All", action='DESELECT')
        if not is_edit_mesh(context):
            op(lay, "object.select_grouped", "Hierarchy", type='CHILDREN_RECURSIVE', extend=True)
        op(lay, "maya.select_all", "Inverse  (Ctrl+Shift+I)", action='INVERT')
        if is_edit_mesh(context):
            op(lay, "mesh.select_similar", "Similar")
            lay.separator()
            op(lay, "mesh.select_more", "Grow  (>)")
            op(lay, "mesh.select_less", "Shrink  (<)")
            op(lay, "mesh.select_linked", "Select Shell")
            lay.separator()
            op(lay, "maya.convert_selection", "Select Edge Loop", to='EDGE_LOOP')
            op(lay, "maya.convert_selection", "Select Edge Ring", to='EDGE_RING')
            op(lay, "mesh.region_to_loop", "Select Border Edge")
            op(lay, "wm.tool_set_by_id", "Select Shortest Edge Path Tool (Ctrl+click)", name="builtin.select_box")
            lay.separator()
            op(lay, "mesh.select_nth", "Checker")
            op(lay, "mesh.select_mirror", "Mirror")
            op(lay, "mesh.select_random", "Random")
            op(lay, "mesh.select_non_manifold", "Non-manifold")
            op(lay, "mesh.select_face_by_sides", "Using Constraints: Number of Sides")
            op(lay, "mesh.select_loose", "Using Constraints: Loose")
            op(lay, "mesh.edges_select_sharp", "Using Constraints: Hard Edges")
        else:
            op(lay, "object.select_grouped", "Similar (Same Type)", type='TYPE', extend=True)
            op(lay, "object.select_mirror", "Mirror")
            op(lay, "object.select_random", "Random")
            op(lay, "object.select_linked", "Same Material / Data...", type='MATERIAL')
            op(lay, "object.select_pattern", "Select by Name...")
        lay.separator()
        lay.menu("MAYA_MT_convert_selection")
        op(lay, "object.vertex_group_assign_new", "Quick Select Set: Create from Selection")


# ---------------------------------------------------------------------------
# Modify
# ---------------------------------------------------------------------------

class MAYA_MT_match_transforms(bpy.types.Menu):
    bl_label = "Match Transformations"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.match_transforms", "Match All Transforms", what='ALL')
        op(lay, "maya.match_transforms", "Match Translation", what='TRANSLATE')
        op(lay, "maya.match_transforms", "Match Rotation", what='ROTATE')
        op(lay, "maya.match_transforms", "Match Scaling", what='SCALE')


class MAYA_MT_snap_align(bpy.types.Menu):
    bl_label = "Snap Align Objects"

    def draw(self, context):
        lay = self.layout
        op(lay, "view3d.snap_selected_to_active", "Snap Together (to Last Selected)")
        op(lay, "view3d.snap_selected_to_cursor", "Snap to 3D Cursor")
        op(lay, "view3d.snap_cursor_to_selected", "3D Cursor to Selection")
        op(lay, "object.align", "Align Objects...")


class MAYA_MT_modify(bpy.types.Menu):
    bl_label = "Modify"

    def draw(self, context):
        lay = self.layout
        op(lay, "wm.tool_set_by_id", "Move Tool  (W)", 'ORIENTATION_GLOBAL', name="builtin.move")
        op(lay, "wm.tool_set_by_id", "Rotate Tool  (E)", name="builtin.rotate")
        op(lay, "wm.tool_set_by_id", "Scale Tool  (R)", name="builtin.scale")
        op(lay, "maya.soft_select", "Soft Modification / Soft Select  (B)", 'PROP_ON')
        lay.separator()
        op(lay, "maya.freeze_transforms", "Freeze Transformations", 'FREEZE')
        op(lay, "object.location_clear", "Reset Transformations: Translate")
        op(lay, "object.rotation_clear", "Reset Transformations: Rotate")
        op(lay, "object.scale_clear", "Reset Transformations: Scale")
        lay.menu("MAYA_MT_match_transforms")
        lay.separator()
        op(lay, "maya.center_pivot", "Center Pivot", 'PIVOT_BOUNDBOX')
        op(lay, "object.origin_set", "Pivot to World Origin", type='ORIGIN_CURSOR')
        op(lay, "maya.pivot_edit", "Edit Pivot  (D / Insert)", state='TOGGLE')
        lay.menu("MAYA_MT_snap_align")
        lay.separator()
        op(lay, "maya.add_attribute", "Add Attribute...")
        op(lay, "object.make_links_data", "Replace Objects (Use Last Selected's Shape)", type='OBDATA')
        op(lay, "object.convert", "Convert: NURBS / Curve to Polygons", target='MESH')
        op(lay, "object.convert", "Convert: Polygons Edges to Curve", target='CURVE')
        lay.separator()
        op(lay, "wm.batch_rename", "Search and Replace Names...")
        op(lay, "wm.batch_rename", "Prefix Hierarchy Names...")
        lay.separator()
        op(lay, "object.join", "Combine", 'SELECT_EXTEND')
        op(lay, "maya.delete_history", "Delete History", 'TRASH')


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

class MAYA_MT_display_hud(bpy.types.Menu):
    bl_label = "Heads Up Display"

    def draw(self, context):
        lay = self.layout
        space = view3d_space(context)
        if space is None:
            return
        prop(lay, space.overlay, "show_stats", "Poly Count / Object Details")
        prop(lay, space.overlay, "show_text", "View Name / Frame")
        prop(lay, space.overlay, "show_viewer_text", "Viewer Text")
        prop(lay, space, "show_gizmo_navigate", "View Axis / Navigation")
        prop(lay, space.overlay, "show_axis_x", "Origin Axis X")
        prop(lay, space.overlay, "show_axis_y", "Origin Axis Y")
        prop(lay, space.overlay, "show_axis_z", "Origin Axis Z")


class MAYA_MT_display_ui(bpy.types.Menu):
    bl_label = "UI Elements"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.toggle_region", "Tool Box", region="show_region_toolbar")
        op(lay, "maya.toggle_region", "Shelf / Tool Settings", region="show_region_tool_header")
        op(lay, "maya.toggle_region", "Panel Menus (Header)", region="show_region_header")
        op(lay, "maya.toggle_region", "Sidebar (Channel Box / Modeling Toolkit)", region="show_region_ui")
        op(lay, "screen.screen_full_area", "Hide All UI / Maximize  (Ctrl+Space)", use_hide_panels=True)


class MAYA_MT_display_object(bpy.types.Menu):
    bl_label = "Object Display"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.object_display", "Template", mode='TEMPLATE')
        op(lay, "maya.object_display", "Untemplate", mode='UNTEMPLATE')
        op(lay, "maya.untemplate_all", "Untemplate All")
        op(lay, "maya.object_display", "Bounding Box", mode='BOUNDING_BOX')
        op(lay, "maya.object_display", "No Bounding Box", mode='NO_BOUNDING_BOX')
        op(lay, "maya.object_display", "X-Ray (Toggle)", mode='XRAY')
        op(lay, "maya.object_display", "Local Rotation Axes (Toggle)", mode='LOCAL_AXES')


class MAYA_MT_display_polygons(bpy.types.Menu):
    bl_label = "Polygons"

    def draw(self, context):
        lay = self.layout
        space = view3d_space(context)
        if space is None:
            return
        prop(lay, space.shading, "show_backface_culling", "Backface Culling")
        prop(lay, space.overlay, "show_face_normals", "Face Normals")
        prop(lay, space.overlay, "show_vertex_normals", "Vertex Normals")
        prop(lay, space.overlay, "show_split_normals", "Split / Custom Normals")
        prop(lay, space.overlay, "show_face_center", "Face Centers")
        prop(lay, space.overlay, "show_edge_crease", "Crease Edges")
        prop(lay, space.overlay, "show_edge_sharp", "Hard Edges")
        prop(lay, space.overlay, "show_edge_seams", "Texture Borders (Seams)")
        prop(lay, space.overlay, "show_face_orientation", "Face Orientation")
        prop(lay, space.overlay, "show_extra_indices", "Component IDs (Developer Extras)")


class MAYA_MT_display(bpy.types.Menu):
    bl_label = "Display"

    def draw(self, context):
        lay = self.layout
        space = view3d_space(context)
        if space is not None:
            prop(lay, space.overlay, "show_floor", "Grid")
        lay.menu("MAYA_MT_display_hud")
        lay.menu("MAYA_MT_display_ui")
        lay.separator()
        op(lay, "object.hide_view_set", "Hide Selection  (Ctrl+H)", 'HIDE_ON', unselected=False)
        op(lay, "object.hide_view_clear", "Show All  (Shift+H)", 'HIDE_OFF')
        op(lay, "object.hide_view_set", "Isolate / Hide Unselected  (Alt+H)", unselected=True)
        op(lay, "view3d.localview", "Isolate Select: View Selected", 'ZOOM_SELECTED')
        lay.separator()
        op(lay, "maya.wireframe_color", "Wireframe Color...", 'COLOR')
        lay.menu("MAYA_MT_display_object")
        if space is not None:
            prop(lay, space.overlay, "show_wireframes", "Wireframe on Shaded")
        lay.menu("MAYA_MT_display_polygons")
        lay.separator()
        op(lay, "maya.set_shading", "Wireframe  (4)", 'SHADING_WIRE', shading='WIREFRAME')
        op(lay, "maya.set_shading", "Smooth Shade All  (5)", 'SHADING_SOLID', shading='SOLID')
        op(lay, "maya.set_shading", "Textured  (6)", 'SHADING_TEXTURE', shading='MATERIAL')
        op(lay, "maya.set_shading", "Use All Lights  (7)", 'SHADING_RENDERED', shading='RENDERED')
        op(lay, "maya.smooth_preview", "Smooth Mesh Preview Off  (1)", level='1')
        op(lay, "maya.smooth_preview", "Smooth Mesh Cage + Smooth  (2)", level='2')
        op(lay, "maya.smooth_preview", "Smooth Mesh Preview  (3)", level='3')
        op(lay, "maya.cycle_background", "Cycle Background Color  (Alt+B)")
        lay.separator()
        op(lay, "screen.region_quadview", "Four View / Single View  (Space)", 'VIEW_PERSPECTIVE')
        op(lay, "view3d.view_selected", "Frame Selection  (F)", 'ZOOM_SELECTED')
        op(lay, "view3d.view_all", "Frame All  (A)", 'ZOOM_ALL')


# ---------------------------------------------------------------------------
# Windows / Help
# ---------------------------------------------------------------------------

class MAYA_MT_windows_animation(bpy.types.Menu):
    bl_label = "Animation Editors"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.open_editor", "Graph Editor", 'GRAPH', ui_type='FCURVES')
        op(lay, "maya.open_editor", "Dope Sheet", 'ACTION', ui_type='DOPESHEET')
        op(lay, "maya.open_editor", "Trax / Time Editor (NLA)", 'NLA', ui_type='NLA_EDITOR')
        op(lay, "maya.open_editor", "Expression Editor / Set Driven Key (Drivers)", 'DRIVER', ui_type='DRIVERS')
        op(lay, "maya.show_attributes", "Shape Editor (Shape Keys)", 'SHAPEKEY_DATA', tab='DATA')
        op(lay, "maya.open_editor", "Camera Sequencer (Video Sequencer)", 'SEQUENCE', ui_type='SEQUENCE_EDITOR')


class MAYA_MT_windows_rendering(bpy.types.Menu):
    bl_label = "Rendering Editors"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.open_editor", "Hypershade (Shader Editor)", 'NODE_MATERIAL', ui_type='ShaderNodeTree')
        op(lay, "render.view_show", "Render View", 'RENDER_RESULT')
        op(lay, "maya.show_attributes", "Render Settings", 'PROPERTIES', tab='RENDER')
        op(lay, "maya.open_editor", "Compositor", 'NODE_COMPOSITING', ui_type='CompositorNodeTree')
        op(lay, "maya.open_editor", "Texture Node Editor", 'TEXTURE', ui_type='TextureNodeTree')


class MAYA_MT_windows(bpy.types.Menu):
    bl_label = "Windows"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.setup_maya_ui", "Workspaces: Reset Maya Workspace", 'WORKSPACE')
        lay.separator()
        op(lay, "maya.open_editor", "Outliner", 'OUTLINER', ui_type='OUTLINER')
        op(lay, "maya.toggle_attribute_editor", "Attribute Editor  (Ctrl+A)", 'PROPERTIES')
        op(lay, "maya.open_editor", "Component Editor / Spreadsheet", 'SPREADSHEET', ui_type='SPREADSHEET')
        op(lay, "maya.open_editor", "Content Browser (Asset Browser)", 'ASSET_MANAGER', ui_type='ASSETS')
        lay.separator()
        op(lay, "maya.open_editor", "UV Editor", 'UV', ui_type='UV')
        op(lay, "maya.open_editor", "Node Editor (Geometry Nodes)", 'NODETREE', ui_type='GeometryNodeTree')
        lay.menu("MAYA_MT_windows_animation", icon='ANIM')
        lay.menu("MAYA_MT_windows_rendering", icon='RENDER_STILL')
        lay.separator()
        op(lay, "maya.open_editor", "Script Editor (Python Console)", 'CONSOLE', ui_type='CONSOLE')
        op(lay, "maya.open_editor", "Script Editor (Text Editor)", 'TEXT', ui_type='TEXT_EDITOR')
        op(lay, "maya.open_editor", "Info / History", 'INFO', ui_type='INFO')
        lay.separator()
        op(lay, "screen.userpref_show", "Settings / Preferences", 'PREFERENCES')
        op(lay, "screen.userpref_show", "Hotkey Editor", 'KEYINGSET', section='KEYMAP')
        op(lay, "render.opengl", "Playblast", 'RENDER_ANIMATION', animation=True)


class MAYA_MT_help(bpy.types.Menu):
    bl_label = "Help"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.open_url", "Maya → Blender: What Changed (Korean)", 'HELP',
           url="https://github.com/9amechoung/BlanderToMaya/blob/claude/clever-edison-706sfl/docs/CHANGES_KO.md")
        op(lay, "maya.open_url", "Blender Manual", 'URL', url="https://docs.blender.org/manual/en/latest/")
        lay.separator()
        lay.menu("TOPBAR_MT_help", text="Blender Help Menu", icon='BLENDER')


# ---------------------------------------------------------------------------
# Modeling menu set
# ---------------------------------------------------------------------------

class MAYA_MT_booleans(bpy.types.Menu):
    bl_label = "Booleans"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.boolean", "Union", 'SELECT_EXTEND', operation='UNION')
        op(lay, "maya.boolean", "Difference", 'SELECT_SUBTRACT', operation='DIFFERENCE')
        op(lay, "maya.boolean", "Intersection", 'SELECT_INTERSECT', operation='INTERSECT')
        op(lay, "maya.add_modifier", "Boolean as Modifier (Keep History)", 'MOD_BOOLEAN', modifier='BOOLEAN')


class MAYA_MT_mesh(bpy.types.Menu):
    bl_label = "Mesh"

    def draw(self, context):
        lay = self.layout
        lay.menu("MAYA_MT_booleans", icon='MOD_BOOLEAN')
        op(lay, "object.join", "Combine", 'SELECT_EXTEND')
        op(lay, "mesh.separate", "Separate", 'SELECT_SUBTRACT', type='LOOSE')
        lay.separator()
        op(lay, "maya.add_modifier", "Conform (Shrinkwrap)", 'MOD_SHRINKWRAP', modifier='SHRINKWRAP')
        op(lay, "mesh.fill_holes", "Fill Hole", 'SNAP_FACE')
        op(lay, "maya.add_modifier", "Reduce", 'MOD_DECIM', modifier='DECIMATE')
        op(lay, "maya.add_modifier", "Remesh", 'MOD_REMESH', modifier='REMESH')
        op(lay, "object.quadriflow_remesh", "Retopologize (QuadriFlow)")
        op(lay, "maya.add_modifier", "Smooth", 'MOD_SUBSURF', modifier='SUBSURF')
        op(lay, "maya.add_modifier", "Mirror", 'MOD_MIRROR', modifier='MIRROR')
        lay.separator()
        op(lay, "mesh.quads_convert_to_tris", "Triangulate", 'MOD_TRIANGULATE')
        op(lay, "mesh.tris_convert_to_quads", "Quadrangulate")
        op(lay, "mesh.remove_doubles", "Clean Up (Merge by Distance)", 'AUTOMERGE_OFF')
        op(lay, "mesh.dissolve_limited", "Clean Up (Limited Dissolve)")
        lay.separator()
        op(lay, "object.data_transfer", "Transfer Attributes (Data Transfer)", data_type='CUSTOM_NORMAL')
        op(lay, "maya.add_modifier", "Smooth Proxy (Subdivision)", modifier='SUBSURF')


class MAYA_MT_edit_mesh(bpy.types.Menu):
    bl_label = "Edit Mesh"

    def draw(self, context):
        lay = self.layout
        op(lay, "mesh.subdivide", "Add Divisions", 'MESH_GRID')
        op(lay, "mesh.bevel", "Bevel  (Ctrl+B)", 'MOD_BEVEL')
        op(lay, "mesh.bridge_edge_loops", "Bridge", 'MOD_LATTICE')
        op(lay, "transform.tosphere", "Circularize", value=1.0)
        op(lay, "mesh.merge", "Collapse", type='COLLAPSE')
        op(lay, "mesh.vert_connect_path", "Connect")
        op(lay, "mesh.split", "Detach")
        op(lay, "view3d.edit_mesh_extrude_move_normal", "Extrude  (Ctrl+E)", 'FACESEL')
        op(lay, "mesh.merge", "Merge", 'AUTOMERGE_ON', type='CENTER')
        op(lay, "mesh.merge", "Merge to Center", type='CENTER')
        op(lay, "mesh.flip_normals", "Flip", 'NORMALS_FACE')
        op(lay, "mesh.symmetrize", "Symmetrize", 'MOD_MIRROR')
        lay.separator()
        op(lay, "mesh.vertices_smooth", "Average Vertices", 'MOD_SMOOTH')
        op(lay, "mesh.bevel", "Chamfer Vertex", affect='VERTICES')
        op(lay, "mesh.sort_elements", "Reorder Vertices")
        lay.separator()
        op(lay, "mesh.dissolve_mode", "Delete Edge/Vertex", 'X')
        op(lay, "mesh.delete_edgeloop", "Delete Edge Loop")
        op(lay, "mesh.edge_rotate", "Flip Triangle Edge / Spin Edge")
        op(lay, "mesh.hide", "Assign Invisible Faces", unselected=False)
        lay.separator()
        op(lay, "mesh.duplicate_move", "Duplicate", 'DUPLICATE')
        op(lay, "mesh.separate", "Extract", type='SELECTED')
        op(lay, "mesh.poke", "Poke")
        op(lay, "mesh.spin", "Wedge (Spin)")
        op(lay, "mesh.knife_project", "Split Mesh with Projected Curve (Knife Project)")
        lay.separator()
        op(lay, "transform.edge_slide", "Slide Edge", 'ARROW_LEFTRIGHT')
        op(lay, "mesh.offset_edge_loops_slide", "Offset Edge Loop")
        op(lay, "maya.target_weld", "Target Weld")
        op(lay, "mesh.inset", "Extrude Inward (Inset)", 'FULLSCREEN_EXIT')


class MAYA_MT_mesh_tools(bpy.types.Menu):
    bl_label = "Mesh Tools"

    def draw(self, context):
        lay = self.layout
        op(lay, "mesh.edge_face_add", "Append to Polygon (Fill Face)")
        op(lay, "mesh.vert_connect_path", "Connect")
        op(lay, "transform.edge_crease", "Crease", 'SHARPCURVE')
        op(lay, "wm.tool_set_by_id", "Create Polygon (Poly Build)", name="builtin.poly_build")
        op(lay, "mesh.loopcut_slide", "Insert Edge Loop", 'MOD_MULTIRES')
        op(lay, "mesh.knife_project", "Make Hole (Knife Project)")
        op(lay, "mesh.knife_tool", "Multi-Cut", 'SCULPTMODE_HLT')
        op(lay, "mesh.offset_edge_loops_slide", "Offset Edge Loop")
        op(lay, "maya.quad_draw", "Quad Draw")
        op(lay, "transform.edge_slide", "Slide Edge", 'ARROW_LEFTRIGHT')
        op(lay, "maya.target_weld", "Target Weld")
        lay.separator()
        op(lay, "mesh.bisect", "Slice (Bisect)")
        op(lay, "mesh.fill_grid", "Fill Grid")
        op(lay, "mesh.vertices_smooth", "Relax", 'MOD_SMOOTH')
        op(lay, "mesh.symmetrize", "Symmetrize", 'MOD_MIRROR')


class MAYA_MT_mesh_display(bpy.types.Menu):
    bl_label = "Mesh Display"

    def draw(self, context):
        lay = self.layout
        op(lay, "mesh.normals_make_consistent", "Conform (Recalculate Normals)", inside=False)
        op(lay, "mesh.flip_normals", "Reverse", 'NORMALS_FACE')
        op(lay, "mesh.average_normals", "Average Normals")
        op(lay, "mesh.set_normals_from_faces", "Set to Face")
        op(lay, "mesh.customdata_custom_splitnormals_clear", "Unlock / Reset Normals")
        lay.separator()
        op(lay, "mesh.faces_shade_smooth", "Soften Edge (Smooth Faces)", 'SMOOTHCURVE')
        op(lay, "mesh.faces_shade_flat", "Harden Edge (Flat Faces)", 'SHARPCURVE')
        op(lay, "mesh.mark_sharp", "Mark Hard Edges", clear=False)
        op(lay, "mesh.mark_sharp", "Clear Hard Edges", clear=True)
        op(lay, "object.shade_smooth", "Smooth Shade Object", 'SHADING_RENDERED')
        op(lay, "object.shade_flat", "Flat Shade Object", 'SHADING_SOLID')
        op(lay, "object.shade_smooth_by_angle", "Soften/Harden by Angle")
        lay.separator()
        op(lay, "object.mode_set", "Apply Color (Vertex Paint)", 'VPAINT_HLT', mode='VERTEX_PAINT')
        lay.menu("MAYA_MT_display_polygons", text="Toggle Display")


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
        op(lay, "curve.spline_type_set", "Rebuild (Set Spline Type)...")
        op(lay, "curve.make_segment", "Attach")
        op(lay, "curve.separate", "Detach")
        op(lay, "curve.extrude_move", "Extend")
        lay.separator()
        op(lay, "object.convert", "Convert to Mesh", 'OUTLINER_OB_MESH', target='MESH')
        op(lay, "object.convert", "Convert Mesh to Curve", 'OUTLINER_OB_CURVE', target='CURVE')


class MAYA_MT_surfaces(bpy.types.Menu):
    bl_label = "Surfaces"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.loft", "Loft")
        op(lay, "maya.planar", "Planar")
        op(lay, "maya.revolve", "Revolve")
        op(lay, "maya.extrude_curve", "Extrude (Profile along Path)")
        lay.separator()
        op(lay, "curve.make_segment", "Attach")
        op(lay, "curve.separate", "Detach")
        op(lay, "curve.switch_direction", "Reverse Direction")
        op(lay, "object.convert", "Convert NURBS to Polygons", target='MESH')


class MAYA_MT_deform(bpy.types.Menu):
    bl_label = "Deform"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.shape_key_add", "Blend Shape (Shape Key)", 'SHAPEKEY_DATA', from_mix=False)
        op(lay, "object.hook_add_newob", "Cluster (Hook, in component mode)", 'HOOK')
        op(lay, "maya.add_modifier", "Curve Warp", 'MOD_CURVE', modifier='CURVE')
        op(lay, "maya.add_modifier", "Delta Mush", 'MOD_SMOOTH', modifier='CORRECTIVE_SMOOTH')
        op(lay, "maya.add_lattice", "Lattice", 'MOD_LATTICE')
        op(lay, "maya.add_modifier", "Wrap (Surface Deform)", 'MOD_MESHDEFORM', modifier='SURFACE_DEFORM')
        op(lay, "maya.add_modifier", "Proximity Wrap (Mesh Deform)", 'MOD_MESHDEFORM', modifier='MESH_DEFORM')
        op(lay, "maya.add_modifier", "ShrinkWrap", 'MOD_SHRINKWRAP', modifier='SHRINKWRAP')
        op(lay, "maya.add_modifier", "Solidify", 'MOD_SOLIDIFY', modifier='SOLIDIFY')
        op(lay, "maya.add_modifier", "Texture Deformer (Displace)", 'MOD_DISPLACE', modifier='DISPLACE')
        op(lay, "maya.add_modifier", "Soft Mod (Warp)", 'MOD_WARP', modifier='WARP')
        op(lay, "maya.add_modifier", "Sculpt (Cast)", 'MOD_CAST', modifier='CAST')
        lay.separator()
        op(lay, "maya.nonlinear", "Nonlinear: Bend", 'MOD_SIMPLEDEFORM', deformer='BEND')
        op(lay, "maya.nonlinear", "Nonlinear: Flare", deformer='FLARE')
        op(lay, "maya.nonlinear", "Nonlinear: Sine", deformer='SINE')
        op(lay, "maya.nonlinear", "Nonlinear: Squash", deformer='SQUASH')
        op(lay, "maya.nonlinear", "Nonlinear: Twist", deformer='TWIST')
        op(lay, "maya.nonlinear", "Nonlinear: Wave", 'MOD_WAVE', deformer='WAVE')
        lay.separator()
        op(lay, "object.modifier_add", "Jiggle (Soft Body)", 'MOD_SOFT', type='SOFT_BODY')
        op(lay, "object.mode_set", "Paint Weights", 'WPAINT_HLT', mode='WEIGHT_PAINT')
        op(lay, "maya.show_attributes", "Edit Membership (Vertex Groups)", 'GROUP_VERTEX', tab='DATA')


class MAYA_MT_uv(bpy.types.Menu):
    bl_label = "UV"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.open_uv_editor", "UV Editor", 'UV')
        op(lay, "maya.show_attributes", "UV Set Editor (UV Maps)", 'GROUP_UVS', tab='DATA')
        lay.separator()
        op(lay, "uv.smart_project", "Automatic", 'UV_DATA')
        op(lay, "uv.project_from_view", "Camera-Based / Planar", 'VIEW_CAMERA')
        op(lay, "uv.cube_project", "Cube Projection", 'MESH_CUBE')
        op(lay, "uv.cylinder_project", "Cylindrical", 'MESH_CYLINDER')
        op(lay, "uv.sphere_project", "Spherical", 'MESH_UVSPHERE')
        op(lay, "uv.follow_active_quads", "Contour Stretch (Follow Active Quads)")
        op(lay, "uv.lightmap_pack", "Lightmap Pack")
        lay.separator()
        op(lay, "uv.unwrap", "Unfold", 'UV')
        op(lay, "uv.pack_islands", "Layout")
        op(lay, "uv.average_islands_scale", "Normalize (Average Scale)")
        lay.separator()
        op(lay, "mesh.mark_seam", "Cut", clear=False)
        op(lay, "mesh.mark_seam", "Sew", clear=True)


class MAYA_MT_generate(bpy.types.Menu):
    bl_label = "Generate"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.add_hair", "XGen / Interactive Groom (Hair Curves)", 'CURVES_DATA')
        op(lay, "object.particle_system_add", "Particle Instancer (Particle System)", 'PARTICLES')
        op(lay, "maya.add_modifier", "Instancer / Array", 'MOD_ARRAY', modifier='ARRAY')
        op(lay, "maya.open_editor", "MASH / Bifrost → Geometry Nodes Editor", 'NODETREE', ui_type='GeometryNodeTree')


class MAYA_MT_cache(bpy.types.Menu):
    bl_label = "Cache"

    def draw(self, context):
        lay = self.layout
        op(lay, "wm.alembic_export", "Alembic Cache: Export All...", 'EXPORT')
        op(lay, "wm.alembic_export", "Alembic Cache: Export Selection...", selected=True)
        op(lay, "wm.alembic_import", "Alembic Cache: Import...", 'IMPORT')
        op(lay, "wm.usd_export", "USD: Export...")
        op(lay, "wm.usd_import", "USD: Import...")
        lay.separator()
        op(lay, "ptcache.bake_all", "Create Simulation Cache (Bake All)", bake=True)
        op(lay, "ptcache.free_bake_all", "Delete Simulation Cache")
        op(lay, "nla.bake", "Bake Animation", 'ACTION')


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
        op(lay, "armature.symmetrize", "Mirror Joints", 'MOD_MIRROR')
        op(lay, "armature.calculate_roll", "Orient Joint", type='GLOBAL_POS_Z')
        lay.separator()
        op(lay, "pose.ik_add", "Create IK Handle", 'CON_KINEMATIC')
        op(lay, "pose.constraint_add", "Create IK Spline Handle", 'CON_SPLINEIK', type='SPLINE_IK')
        op(lay, "pose.ik_clear", "Remove IK")
        op(lay, "maya.quick_rig", "Quick Rig (Rigify Human)", 'OUTLINER_OB_ARMATURE')
        op(lay, "object.skin_armature_create", "Create Skeleton from Skin Modifier")
        lay.separator()
        op(lay, "object.mode_set", "Pose Mode", 'POSE_HLT', mode='POSE')
        op(lay, "object.mode_set", "Edit Joints", 'EDITMODE_HLT', mode='EDIT')


class MAYA_MT_skin(bpy.types.Menu):
    bl_label = "Skin"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.parent_set", "Bind Skin", 'MOD_ARMATURE', type='ARMATURE_AUTO')
        op(lay, "object.parent_set", "Bind Skin (Empty Weights)", type='ARMATURE_NAME')
        op(lay, "object.parent_set", "Rigid Bind (Envelope)", type='ARMATURE_ENVELOPE')
        op(lay, "object.parent_clear", "Unbind Skin", type='CLEAR')
        lay.separator()
        op(lay, "object.mode_set", "Paint Skin Weights", 'WPAINT_HLT', mode='WEIGHT_PAINT')
        op(lay, "object.vertex_group_mirror", "Mirror Skin Weights")
        op(lay, "object.data_transfer", "Copy Skin Weights (from Active)", data_type='VGROUP_WEIGHTS')
        op(lay, "object.vertex_group_smooth", "Smooth Skin Weights")
        op(lay, "object.vertex_group_normalize_all", "Normalize Weights")
        op(lay, "object.vertex_group_clean", "Prune Small Weights")
        op(lay, "object.vertex_group_add", "Add Influence (Vertex Group)")


class MAYA_MT_constrain(bpy.types.Menu):
    bl_label = "Constrain"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.constraint_add_with_targets", "Parent", 'CON_CHILDOF', type='CHILD_OF')
        op(lay, "object.constraint_add_with_targets", "Point", 'CON_LOCLIKE', type='COPY_LOCATION')
        op(lay, "object.constraint_add_with_targets", "Orient", 'CON_ROTLIKE', type='COPY_ROTATION')
        op(lay, "object.constraint_add_with_targets", "Scale", 'CON_SIZELIKE', type='COPY_SCALE')
        op(lay, "object.constraint_add_with_targets", "Aim", 'CON_TRACKTO', type='DAMPED_TRACK')
        op(lay, "maya.pole_vector", "Pole Vector", 'CON_LOCKTRACK')
        lay.separator()
        op(lay, "object.constraint_add_with_targets", "Geometry (Shrinkwrap)", 'CON_SHRINKWRAP', type='SHRINKWRAP')
        op(lay, "object.constraint_add_with_targets", "Normal (Track To)", 'CON_TRACKTO', type='TRACK_TO')
        op(lay, "object.constraint_add_with_targets", "Tangent / Motion Path (Follow Path)", 'CON_FOLLOWPATH',
           type='FOLLOW_PATH')
        op(lay, "object.vertex_parent_set", "Point on Poly (Vertex Parent)")
        op(lay, "object.constraint_add_with_targets", "Copy All (Copy Transforms)", 'CON_TRANSLIKE',
           type='COPY_TRANSFORMS')
        lay.separator()
        op(lay, "object.constraints_clear", "Remove Constraints")


class MAYA_MT_control(bpy.types.Menu):
    bl_label = "Control"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.empty_add", "Circle Control", 'MESH_CIRCLE', type='CIRCLE')
        op(lay, "object.empty_add", "Cube Control", 'MESH_CUBE', type='CUBE')
        op(lay, "object.empty_add", "Sphere Control", 'MESH_UVSPHERE', type='SPHERE')
        op(lay, "object.empty_add", "Arrows Control", 'EMPTY_ARROWS', type='ARROWS')
        op(lay, "object.empty_add", "Locator", 'EMPTY_AXIS', type='PLAIN_AXES')
        lay.separator()
        op(lay, "object.parent_set", "Parent to Control", 'LINKED', type='OBJECT', keep_transform=True)
        op(lay, "maya.group", "Group Offset (Zero Out)", 'GROUP')


# ---------------------------------------------------------------------------
# Animation menu set
# ---------------------------------------------------------------------------

class MAYA_MT_key(bpy.types.Menu):
    bl_label = "Key"

    def draw(self, context):
        lay = self.layout
        op(lay, "anim.keyframe_insert", "Set Key  (S)", 'KEY_HLT')
        op(lay, "anim.keyframe_insert_by_name", "Key Translate  (Shift+W)", type='Location')
        op(lay, "anim.keyframe_insert_by_name", "Key Rotate  (Shift+E)", type='Rotation')
        op(lay, "anim.keyframe_insert_by_name", "Key Scale  (Shift+R)", type='Scaling')
        op(lay, "anim.keyframe_insert_menu", "Set Key Options...", type='Location')
        op(lay, "anim.keyframe_delete_v3d", "Delete Key", 'KEY_DEHLT')
        op(lay, "anim.keyframe_clear_v3d", "Delete All Keys")
        lay.separator()
        op(lay, "maya.open_editor", "Graph Editor", 'GRAPH', ui_type='FCURVES')
        op(lay, "maya.open_editor", "Dope Sheet", 'ACTION', ui_type='DOPESHEET')
        op(lay, "maya.open_editor", "Set Driven Key (Drivers Editor)", 'DRIVER', ui_type='DRIVERS')
        op(lay, "anim.keying_set_active_set", "Keying Set...")
        op(lay, "nla.bake", "Bake Simulation", 'ACTION')
        lay.separator()
        lay.prop(context.scene.tool_settings, "use_keyframe_insert_auto", text="Auto Keyframe")


class MAYA_MT_playback(bpy.types.Menu):
    bl_label = "Playback"

    def draw(self, context):
        lay = self.layout
        op(lay, "screen.animation_play", "Play Forwards  (Alt+V)", 'PLAY')
        op(lay, "screen.animation_play", "Play Backwards", 'PLAY_REVERSE', reverse=True)
        op(lay, "screen.animation_cancel", "Stop", 'PAUSE', restore_frame=False)
        lay.separator()
        op(lay, "screen.frame_jump", "Go to Start", 'REW', end=False)
        op(lay, "screen.keyframe_jump", "Previous Key  (,)", 'PREV_KEYFRAME', next=False)
        op(lay, "screen.frame_offset", "Previous Frame  (Alt+,)", delta=-1)
        op(lay, "screen.frame_offset", "Next Frame  (Alt+.)", delta=1)
        op(lay, "screen.keyframe_jump", "Next Key  (.)", 'NEXT_KEYFRAME', next=True)
        op(lay, "screen.frame_jump", "Go to End", 'FF', end=True)
        lay.separator()
        lay.prop(context.scene.render, "fps", text="Frame Rate")
        lay.prop(context.scene, "use_preview_range", text="Range Slider (Preview Range)")
        op(lay, "render.opengl", "Playblast", 'RENDER_ANIMATION', animation=True)


class MAYA_MT_audio(bpy.types.Menu):
    bl_label = "Audio"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.import_audio", "Import Audio...", 'SOUND')
        lay.prop(context.scene, "use_audio_scrub", text="Scrub Audio")
        lay.prop(context.scene, "use_audio", text="Mute")
        op(lay, "maya.open_editor", "Audio Track (Video Sequencer)", 'SEQUENCE', ui_type='SEQUENCE_EDITOR')


class MAYA_MT_visualize(bpy.types.Menu):
    bl_label = "Visualize"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.paths_calculate", "Create Editable Motion Trail", 'IPO_BEZIER')
        op(lay, "object.paths_clear", "Delete Motion Trail")
        op(lay, "object.paths_update", "Update Motion Trail")
        lay.separator()
        op(lay, "render.opengl", "Playblast (Viewport Render Animation)", 'RENDER_ANIMATION', animation=True)
        op(lay, "render.opengl", "Viewport Render Frame", 'RENDER_STILL')


# ---------------------------------------------------------------------------
# FX menu set
# ---------------------------------------------------------------------------

class MAYA_MT_nparticles(bpy.types.Menu):
    bl_label = "nParticles"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.particle_system_add", "Emit from Object (Particle System)", 'PARTICLES')
        op(lay, "maya.show_attributes", "Particle Settings", 'PARTICLE_DATA', tab='PARTICLES')
        op(lay, "rigidbody.objects_add", "Make Collide (Rigid Body)", type='PASSIVE')
        op(lay, "maya.add_modifier", "Make Collide (Collision)", 'MOD_PHYSICS', modifier='COLLISION')


class MAYA_MT_fluids(bpy.types.Menu):
    bl_label = "Fluids"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.quick_smoke", "Smoke / Fire (Quick Smoke)", 'OUTLINER_OB_FORCE_FIELD')
        op(lay, "object.quick_liquid", "Liquid (Quick Liquid)", 'MOD_FLUIDSIM')
        op(lay, "maya.show_attributes", "Fluid Settings (Physics)", 'PHYSICS', tab='PHYSICS')


class MAYA_MT_ncloth(bpy.types.Menu):
    bl_label = "nCloth"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.modifier_add", "Create nCloth (Cloth)", 'MOD_CLOTH', type='CLOTH')
        op(lay, "object.modifier_add", "Create Passive Collider (Collision)", 'MOD_PHYSICS', type='COLLISION')
        op(lay, "maya.show_attributes", "nCloth Settings (Physics)", 'PHYSICS', tab='PHYSICS')


class MAYA_MT_nhair(bpy.types.Menu):
    bl_label = "nHair"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.add_hair", "Create Hair (Hair Curves)", 'CURVES_DATA')
        op(lay, "object.quick_fur", "Quick Fur")


class MAYA_MT_fields(bpy.types.Menu):
    bl_label = "Fields/Solvers"

    def draw(self, context):
        lay = self.layout
        for key, text in (('WIND', "Air / Uniform (Wind)"), ('DRAG', "Drag"), ('FORCE', "Newton / Radial (Force)"),
                          ('TURBULENCE', "Turbulence"), ('VORTEX', "Vortex"), ('MAGNET', "Magnet"),
                          ('HARMONIC', "Harmonic"), ('CHARGE', "Charge"), ('CURVE_GUIDE', "Curve Guide")):
            op(lay, "object.effector_add", text, 'FORCE_' + ('WIND' if key == 'CURVE_GUIDE' else key), type=key)
        lay.separator()
        lay.prop(context.scene, "use_gravity", text="Gravity")
        op(lay, "ptcache.bake_all", "Solver: Bake All", bake=True)
        op(lay, "ptcache.free_bake_all", "Solver: Delete Cache")


class MAYA_MT_effects(bpy.types.Menu):
    bl_label = "Effects"

    def draw(self, context):
        lay = self.layout
        op(lay, "object.quick_explode", "Shatter / Explode")
        op(lay, "object.quick_smoke", "Fire", style='FIRE')
        op(lay, "object.quick_smoke", "Smoke", style='SMOKE')
        op(lay, "object.quick_fur", "Fur")
        op(lay, "object.quick_liquid", "Liquid")


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
        op(lay, "object.material_slot_assign", "Assign to Selected Faces")
        lay.separator()
        lay.menu("MAYA_MT_create_lights", icon='LIGHT')
        op(lay, "maya.show_attributes", "Environment (World)", 'WORLD', tab='WORLD')
        op(lay, "maya.show_attributes", "Light Linking", 'LIGHT', tab='OBJECT')
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
        op(lay, "maya.show_attributes", "Convert to File Texture (Render Settings > Bake)", tab='RENDER')


class MAYA_MT_render(bpy.types.Menu):
    bl_label = "Render"

    def draw(self, context):
        lay = self.layout
        op(lay, "render.render", "Render Current Frame", 'RENDER_STILL', use_viewport=True)
        op(lay, "render.render", "Render Sequence", 'RENDER_ANIMATION', animation=True, use_viewport=True)
        op(lay, "maya.set_shading", "IPR Render (Viewport Rendered)", 'SHADING_RENDERED', shading='RENDERED')
        op(lay, "render.view_show", "Render View", 'RENDER_RESULT')
        lay.separator()
        op(lay, "maya.show_attributes", "Render Settings", 'PROPERTIES', tab='RENDER')
        op(lay, "maya.show_attributes", "Output Settings", 'OUTPUT', tab='OUTPUT')
        op(lay, "maya.show_attributes", "Render Setup / Layers (View Layer)", 'RENDERLAYERS', tab='VIEW_LAYER')
        op(lay, "render.opengl", "Playblast", animation=True)


class MAYA_MT_toon(bpy.types.Menu):
    bl_label = "Toon"

    def draw(self, context):
        lay = self.layout
        lay.prop(context.scene.render, "use_freestyle", text="Assign Outline (Freestyle)")
        if op_exists("object.grease_pencil_add"):
            op(lay, "object.grease_pencil_add", "Line Art Outline", 'MOD_LINEART', type='LINEART_SCENE')
        else:
            op(lay, "object.gpencil_add", "Line Art Outline", 'MOD_LINEART', type='LINEART_SCENE')
        op(lay, "maya.show_attributes", "Toon Settings (View Layer > Freestyle)", tab='VIEW_LAYER')


class MAYA_MT_stereo(bpy.types.Menu):
    bl_label = "Stereo"

    def draw(self, context):
        lay = self.layout
        lay.prop(context.scene.render, "use_multiview", text="Stereo Camera (Stereoscopy)")
        op(lay, "maya.show_attributes", "Stereo Settings (Output)", tab='OUTPUT')


# ---------------------------------------------------------------------------

def draw_menu_bar(layout, context):
    wm = context.window_manager
    for idname in COMMON_MENUS + SET_MENUS[wm.maya_menu_set]:
        layout.menu(idname)
    layout.menu("MAYA_MT_help")


classes = (
    MAYA_OT_call_in_view3d,
    MAYA_OT_open_editor,
    MAYA_OT_select_all,
    MAYA_OT_delete,
    MAYA_OT_cut,
    MAYA_OT_toggle_snap,
    MAYA_OT_toggle_region,
    MAYA_OT_object_display,
    MAYA_OT_untemplate_all,
    MAYA_OT_wireframe_color,
    MAYA_OT_open_url,
    MAYA_MT_file,
    MAYA_MT_delete_by_type,
    MAYA_MT_delete_all_by_type,
    MAYA_MT_edit,
    MAYA_MT_create_polygons,
    MAYA_MT_create_nurbs,
    MAYA_MT_create_curves,
    MAYA_MT_create_lights,
    MAYA_MT_create_cameras,
    MAYA_MT_create,
    MAYA_MT_convert_selection,
    MAYA_MT_select,
    MAYA_MT_match_transforms,
    MAYA_MT_snap_align,
    MAYA_MT_modify,
    MAYA_MT_display_hud,
    MAYA_MT_display_ui,
    MAYA_MT_display_object,
    MAYA_MT_display_polygons,
    MAYA_MT_display,
    MAYA_MT_windows_animation,
    MAYA_MT_windows_rendering,
    MAYA_MT_windows,
    MAYA_MT_help,
    MAYA_MT_booleans,
    MAYA_MT_mesh,
    MAYA_MT_edit_mesh,
    MAYA_MT_mesh_tools,
    MAYA_MT_mesh_display,
    MAYA_MT_curves,
    MAYA_MT_surfaces,
    MAYA_MT_deform,
    MAYA_MT_uv,
    MAYA_MT_generate,
    MAYA_MT_cache,
    MAYA_MT_skeleton,
    MAYA_MT_skin,
    MAYA_MT_constrain,
    MAYA_MT_control,
    MAYA_MT_key,
    MAYA_MT_playback,
    MAYA_MT_audio,
    MAYA_MT_visualize,
    MAYA_MT_nparticles,
    MAYA_MT_fluids,
    MAYA_MT_ncloth,
    MAYA_MT_nhair,
    MAYA_MT_fields,
    MAYA_MT_effects,
    MAYA_MT_lighting_shading,
    MAYA_MT_texturing,
    MAYA_MT_render,
    MAYA_MT_toon,
    MAYA_MT_stereo,
)


def register():
    bpy.types.WindowManager.maya_menu_set = EnumProperty(
        name="Menu Set", description="Maya menu set: changes the menus in the top bar (F2-F6)",
        items=MENU_SETS, default='MODELING',
    )
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.maya_menu_set
