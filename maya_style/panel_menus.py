"""Maya panel menus: View, Shading, Lighting, Show, Renderer, Panels in each 3D viewport header.

They replace Blender's View / Select / Add / Object header menus (those are still
there under the "Blender" menu at the end).
"""

import bpy
from bpy.props import StringProperty

from .maya_menus import op, prop
from .prefs import get_prefs

_original_draw = None


def _space(context):
    space = context.space_data
    return space if space is not None and space.type == 'VIEW_3D' else None


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class MAYA_OT_look_through(bpy.types.Operator):
    """Look through this camera ('persp': back to the free perspective view)"""
    bl_idname = "maya.look_through"
    bl_label = "Look Through"

    camera: StringProperty()

    @classmethod
    def poll(cls, context):
        return _space(context) is not None and context.region_data is not None

    def execute(self, context):
        rv3d = context.region_data
        if self.camera == "persp":
            if rv3d.view_perspective == 'CAMERA':
                rv3d.view_perspective = 'PERSP'
            elif rv3d.view_perspective == 'ORTHO':
                rv3d.view_perspective = 'PERSP'
            return {'FINISHED'}
        cam = bpy.data.objects.get(self.camera)
        if cam is None or cam.type != 'CAMERA':
            return {'CANCELLED'}
        context.scene.camera = cam
        rv3d.view_perspective = 'CAMERA'
        return {'FINISHED'}


class MAYA_OT_show_all_types(bpy.types.Operator):
    """Show / hide every object type in this viewport (Maya: Show > All / None)"""
    bl_idname = "maya.show_all_types"
    bl_label = "Show All Types"

    show: bpy.props.BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        return _space(context) is not None

    def execute(self, context):
        space = _space(context)
        for name in space.bl_rna.properties.keys():
            if name.startswith("show_object_viewport_"):
                setattr(space, name, self.show)
        return {'FINISHED'}


LIGHTING_MODES = (
    ('DEFAULT', "Use Default Lighting", "Studio light that follows the camera"),
    ('ALL', "Use All Lights", "Light the scene with its own lights"),
    ('FLAT', "Use Flat Lighting", "No shading at all"),
)


class MAYA_OT_viewport_lighting(bpy.types.Operator):
    """Viewport lighting (Maya: Lighting menu, 7 = Use All Lights)"""
    bl_idname = "maya.viewport_lighting"
    bl_label = "Viewport Lighting"

    mode: bpy.props.EnumProperty(items=LIGHTING_MODES)

    @classmethod
    def poll(cls, context):
        return _space(context) is not None

    def execute(self, context):
        shading = _space(context).shading
        if self.mode == 'ALL':
            if shading.type not in {'MATERIAL', 'RENDERED'}:
                shading.type = 'MATERIAL'
            shading.use_scene_lights = True
        else:
            if shading.type in {'MATERIAL', 'RENDERED'}:
                shading.type = 'SOLID'
            shading.light = 'FLAT' if self.mode == 'FLAT' else 'STUDIO'
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------

class MAYA_MT_panel_view(bpy.types.Menu):
    bl_label = "View"

    def draw(self, context):
        lay = self.layout
        space = _space(context)
        op(lay, "maya.frame", "Frame Selection  (F)", 'ZOOM_SELECTED')
        op(lay, "view3d.view_all", "Frame All  (A)", 'VIEWZOOM', center=False)
        op(lay, "view3d.view_center_cursor", "Look at 3D Cursor")
        op(lay, "view3d.view_persportho", "Perspective / Orthographic")
        lay.separator()
        op(lay, "view3d.view_axis", "Top", type='TOP')
        op(lay, "view3d.view_axis", "Front", type='FRONT')
        op(lay, "view3d.view_axis", "Side (Right)", type='RIGHT')
        op(lay, "view3d.view_axis", "Bottom", type='BOTTOM')
        op(lay, "view3d.view_axis", "Back", type='BACK')
        op(lay, "view3d.view_axis", "Left", type='LEFT')
        lay.separator()
        if context.scene.camera is not None:
            op(lay, "maya.select_object", "Select Camera", 'RESTRICT_SELECT_OFF', name=context.scene.camera.name)
        op(lay, "view3d.camera_to_view", "Align Camera to View")
        if space is not None:
            lay.prop(space, "lens", text="Focal Length")
            lay.prop(space, "clip_start", text="Near Clip Plane")
            lay.prop(space, "clip_end", text="Far Clip Plane")
        lay.separator()
        op(lay, "object.empty_image_add", "Image Plane: Import Image...", 'IMAGE_REFERENCE')
        op(lay, "view3d.toggle_xray", "X-Ray  (Alt+Z)")


class MAYA_MT_panel_shading(bpy.types.Menu):
    bl_label = "Shading"

    def draw(self, context):
        lay = self.layout
        space = _space(context)
        op(lay, "maya.set_shading", "Wireframe  (4)", 'SHADING_WIRE', shading='WIREFRAME')
        op(lay, "maya.set_shading", "Smooth Shade All  (5)", 'SHADING_SOLID', shading='SOLID')
        op(lay, "maya.set_shading", "Textured  (6)", 'SHADING_TEXTURE', shading='MATERIAL')
        op(lay, "maya.set_shading", "Rendered  (7)", 'SHADING_RENDERED', shading='RENDERED')
        lay.separator()
        op(lay, "maya.wireframe_on_shaded", "Wireframe on Shaded", 'MOD_WIREFRAME')
        if space is not None:
            prop(lay, space.shading, "show_xray", "X-Ray")
            prop(lay, space.overlay, "show_xray_bone", "X-Ray Joints")
            prop(lay, space.shading, "show_backface_culling", "Backface Culling")
            prop(lay, space.shading, "show_cavity", "Ambient Occlusion (Cavity)")
        lay.separator()
        op(lay, "maya.smooth_preview", "Smooth Mesh Preview: Off  (1)", level='1')
        op(lay, "maya.smooth_preview", "Smooth Mesh Preview: Cage + Smooth  (2)", level='2')
        op(lay, "maya.smooth_preview", "Smooth Mesh Preview: Smooth  (3)", level='3')


class MAYA_MT_panel_lighting(bpy.types.Menu):
    bl_label = "Lighting"

    def draw(self, context):
        lay = self.layout
        space = _space(context)
        for (mode, name, _desc), icon in zip(LIGHTING_MODES, ('LIGHT_SUN', 'LIGHT', 'SHADING_SOLID')):
            op(lay, "maya.viewport_lighting", name + ("  (7)" if mode == 'ALL' else ""), icon, mode=mode)
        if space is not None:
            lay.separator()
            prop(lay, space.shading, "show_shadows", "Shadows")
            prop(lay, space.shading, "show_specular_highlight", "Specular Highlights")
            prop(lay, space.shading, "use_scene_world", "Use Scene World (Material Preview)")


class MAYA_MT_panel_show(bpy.types.Menu):
    bl_label = "Show"

    TYPES = (
        ("show_object_viewport_mesh", "Polygons"),
        ("show_object_viewport_surf", "NURBS Surfaces"),
        ("show_object_viewport_curve", "NURBS Curves"),
        ("show_object_viewport_curves", "Hair (XGen)"),
        ("show_object_viewport_armature", "Joints"),
        ("show_object_viewport_lattice", "Deformers (Lattice)"),
        ("show_object_viewport_empty", "Locators"),
        ("show_object_viewport_light", "Lights"),
        ("show_object_viewport_camera", "Cameras"),
        ("show_object_viewport_font", "Type"),
        ("show_object_viewport_volume", "Fluids (Volumes)"),
        ("show_object_viewport_pointcloud", "Particles (Point Clouds)"),
        ("show_object_viewport_grease_pencil", "Grease Pencil"),
    )

    def draw(self, context):
        lay = self.layout
        space = _space(context)
        op(lay, "view3d.localview", "Isolate Select (Local View)", 'HIDE_OFF')
        lay.separator()
        op(lay, "maya.show_all_types", "All", show=True)
        op(lay, "maya.show_all_types", "None", show=False)
        if space is None:
            return
        for name, text in self.TYPES:
            prop(lay, space, name, text)
        lay.separator()
        prop(lay, space.overlay, "show_floor", "Grid")
        prop(lay, space.overlay, "show_stats", "Heads Up Display (Poly Count)")
        prop(lay, space, "show_gizmo", "Manipulators")
        prop(lay, space.overlay, "show_outline_selected", "Selection Highlighting")
        prop(lay, space.overlay, "show_overlays", "Overlays")


class MAYA_MT_panel_renderer(bpy.types.Menu):
    bl_label = "Renderer"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.set_shading", "Viewport 2.0 (Solid)", 'SHADING_SOLID', shading='SOLID')
        op(lay, "maya.set_shading", "Material Preview (EEVEE)", 'SHADING_TEXTURE', shading='MATERIAL')
        op(lay, "maya.set_shading", "Rendered", 'SHADING_RENDERED', shading='RENDERED')
        lay.separator()
        lay.prop(context.scene.render, "engine", text="Render Engine")


class MAYA_MT_panel_perspective(bpy.types.Menu):
    bl_label = "Perspective"

    def draw(self, context):
        lay = self.layout
        op(lay, "maya.look_through", "persp", 'VIEW_PERSPECTIVE', camera="persp")
        for obj in context.scene.objects:
            if obj.type == 'CAMERA':
                op(lay, "maya.look_through", obj.name, 'OUTLINER_OB_CAMERA', camera=obj.name)


class MAYA_MT_panel_ortho(bpy.types.Menu):
    bl_label = "Orthographic"

    def draw(self, context):
        lay = self.layout
        op(lay, "view3d.view_axis", "top", 'VIEW_ORTHO', type='TOP')
        op(lay, "view3d.view_axis", "front", 'VIEW_ORTHO', type='FRONT')
        op(lay, "view3d.view_axis", "side", 'VIEW_ORTHO', type='RIGHT')


class MAYA_MT_panel_panels(bpy.types.Menu):
    bl_label = "Panels"

    def draw(self, context):
        lay = self.layout
        lay.menu("MAYA_MT_panel_perspective", icon='VIEW_PERSPECTIVE')
        lay.menu("MAYA_MT_panel_ortho", icon='VIEW_ORTHO')
        op(lay, "view3d.object_as_camera", "Look Through Selected", 'CAMERA_DATA')
        lay.separator()
        op(lay, "screen.region_quadview", "Layouts: Single / Four Panes  (Space)", 'VIEW3D')
        op(lay, "screen.area_dupli", "Tear Off Copy", 'WINDOW')
        op(lay, "screen.screen_full_area", "Maximize Panel  (Ctrl+Space)", 'FULLSCREEN_ENTER')


class MAYA_MT_panel_blender(bpy.types.Menu):
    bl_label = "Blender"

    def draw(self, context):
        if _original_draw is not None:
            _original_draw(self, context)


class MAYA_OT_select_object(bpy.types.Operator):
    """Select this object"""
    bl_idname = "maya.select_object"
    bl_label = "Select Object"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.name)
        if obj is None or context.mode != 'OBJECT':
            return {'CANCELLED'}
        for other in context.selected_objects:
            other.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {'FINISHED'}


PANEL_MENUS = ("MAYA_MT_panel_view", "MAYA_MT_panel_shading", "MAYA_MT_panel_lighting", "MAYA_MT_panel_show",
               "MAYA_MT_panel_renderer", "MAYA_MT_panel_panels")


def _draw_editor_menus(self, context):
    prefs = get_prefs(context)
    if prefs is not None and not prefs.use_panel_menus:
        return _original_draw(self, context)
    layout = self.layout
    for idname in PANEL_MENUS:
        layout.menu(idname)
    layout.menu("MAYA_MT_panel_blender", icon='BLENDER')


classes = (
    MAYA_OT_look_through,
    MAYA_OT_show_all_types,
    MAYA_OT_viewport_lighting,
    MAYA_OT_select_object,
    MAYA_MT_panel_view,
    MAYA_MT_panel_shading,
    MAYA_MT_panel_lighting,
    MAYA_MT_panel_show,
    MAYA_MT_panel_renderer,
    MAYA_MT_panel_perspective,
    MAYA_MT_panel_ortho,
    MAYA_MT_panel_panels,
    MAYA_MT_panel_blender,
)


def register():
    global _original_draw
    for cls in classes:
        bpy.utils.register_class(cls)
    menus = bpy.types.VIEW3D_MT_editor_menus
    if _original_draw is None:
        _original_draw = menus.draw
    menus.draw = _draw_editor_menus


def unregister():
    global _original_draw
    if _original_draw is not None:
        bpy.types.VIEW3D_MT_editor_menus.draw = _original_draw
        _original_draw = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
