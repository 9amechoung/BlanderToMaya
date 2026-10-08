"""Maya-style Right-click (hold) menu on objects.

Hold the right mouse button over an object: a component marking menu
(Vertex / Edge / Face / Object Mode / UV / Vertex Face / Multi) appears
around the cursor, with the object menu list (Select, Inputs, Paint,
Assign Material...) underneath. Release over an item to run it, like Maya.
Over empty space Blender's normal context menu opens instead.
"""

import warnings

import bpy
from bpy.props import EnumProperty, IntProperty, StringProperty
from bpy_extras import view3d_utils


def _object_under_mouse(context, event):
    region = context.region
    rv3d = context.region_data
    if region is None or rv3d is None:
        return None
    coord = (event.mouse_region_x, event.mouse_region_y)
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    depsgraph = context.evaluated_depsgraph_get()
    hit, _loc, _normal, _index, obj, _matrix = context.scene.ray_cast(depsgraph, origin, direction)
    if not hit or obj is None:
        return None
    return obj.original


class MAYA_OT_rmb_menu(bpy.types.Operator):
    """Maya-style right-click menu: component marking menu + object menu"""
    bl_idname = "maya.rmb_menu"
    bl_label = "Maya Right-click Menu"

    def invoke(self, context, event):
        if context.mode == 'OBJECT':
            obj = _object_under_mouse(context, event)
            if obj is None:
                # Empty space: let the keymap's normal right-click menu run.
                return {'PASS_THROUGH'}
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.wm.call_menu_pie(name="MAYA_MT_rmb_object")
        elif context.mode == 'EDIT_MESH':
            bpy.ops.wm.call_menu_pie(name="MAYA_MT_rmb_object")
        else:
            return {'PASS_THROUGH'}
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Small operators used by the menu
# ---------------------------------------------------------------------------

class MAYA_OT_show_attributes(bpy.types.Operator):
    """Show this in the Properties editor (like Maya's Attribute Editor)"""
    bl_idname = "maya.show_attributes"
    bl_label = "Show Attributes"

    tab: StringProperty(default='OBJECT')

    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                try:
                    area.spaces.active.context = self.tab
                except TypeError:
                    pass
                area.tag_redraw()
                return {'FINISHED'}
        self.report({'WARNING'}, "No Properties editor in this layout")
        return {'CANCELLED'}


class MAYA_OT_select_only(bpy.types.Operator):
    """Select only the active object"""
    bl_idname = "maya.select_only"
    bl_label = "Select"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object is not None

    def execute(self, context):
        active = context.active_object
        for obj in context.selected_objects:
            obj.select_set(False)
        active.select_set(True)
        return {'FINISHED'}


class MAYA_OT_open_uv_editor(bpy.types.Operator):
    """Switch to the UV Editing workspace"""
    bl_idname = "maya.open_uv_editor"
    bl_label = "UV Editor"

    def execute(self, context):
        ws = bpy.data.workspaces.get("UV Editing")
        if ws is None:
            self.report({'WARNING'}, "No 'UV Editing' workspace in this file")
            return {'CANCELLED'}
        context.window.workspace = ws
        return {'FINISHED'}


class MAYA_OT_set_active_uv(bpy.types.Operator):
    """Make this UV set the active one"""
    bl_idname = "maya.set_active_uv"
    bl_label = "Set Active UV Set"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            return {'CANCELLED'}
        obj.data.uv_layers.active_index = self.index
        return {'FINISHED'}


def _assign_material(context, mat):
    obj = context.active_object
    if context.mode == 'EDIT_MESH':
        # Assign to the selected faces only.
        slot = obj.material_slots.find(mat.name) if obj.material_slots else -1
        if slot < 0:
            obj.data.materials.append(mat)
            slot = len(obj.material_slots) - 1
        obj.active_material_index = slot
        bpy.ops.object.material_slot_assign()
        return
    # Object mode: the whole object gets the material, like Maya.
    for o in context.selected_objects:
        if o.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            o.data.materials.clear()
            o.data.materials.append(mat)


SHADERS = (
    ('LAMBERT', "Lambert", "Matte surface (no specular)"),
    ('BLINN', "Blinn", "Glossy surface with soft highlights"),
    ('PHONG', "Phong", "Shiny surface with sharp highlights"),
    ('STANDARD', "Standard Surface", "Physically based surface (Principled BSDF)"),
)


class MAYA_OT_assign_new_material(bpy.types.Operator):
    """Create a new material and assign it"""
    bl_idname = "maya.assign_new_material"
    bl_label = "Assign New Material"
    bl_options = {'REGISTER', 'UNDO'}

    shader: EnumProperty(items=SHADERS, default='LAMBERT')

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}

    def execute(self, context):
        name = {'LAMBERT': "lambert", 'BLINN': "blinn", 'PHONG': "phong", 'STANDARD': "standardSurface"}[self.shader]
        mat = bpy.data.materials.new(name)
        if mat.node_tree is None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mat.use_nodes = True
        bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is not None:
            roughness, specular = {'LAMBERT': (1.0, 0.0), 'BLINN': (0.35, 0.5), 'PHONG': (0.15, 0.5), 'STANDARD': (0.5, 0.5)}[self.shader]
            bsdf.inputs["Roughness"].default_value = roughness
            spec = bsdf.inputs.get("Specular IOR Level") or bsdf.inputs.get("Specular")
            if spec is not None:
                spec.default_value = specular
            bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
        mat.diffuse_color = (0.5, 0.5, 0.5, 1.0)
        _assign_material(context, mat)
        return {'FINISHED'}


class MAYA_OT_assign_existing_material(bpy.types.Operator):
    """Assign this material"""
    bl_idname = "maya.assign_existing_material"
    bl_label = "Assign Existing Material"
    bl_options = {'REGISTER', 'UNDO'}

    material: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}

    def execute(self, context):
        mat = bpy.data.materials.get(self.material)
        if mat is None:
            return {'CANCELLED'}
        _assign_material(context, mat)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Sub menus (the ▸ items)
# ---------------------------------------------------------------------------

class MAYA_MT_rmb_uv(bpy.types.Menu):
    bl_idname = "MAYA_MT_rmb_uv"
    bl_label = "UV"

    def draw(self, context):
        layout = self.layout
        op = layout.operator("maya.component_mode", text="UV", icon='UV')
        op.mode = 'FACE'
        layout.operator("maya.open_uv_editor", icon='UV_DATA')
        layout.prop(context.tool_settings, "use_uv_select_sync", text="UV Sync Selection")
        layout.separator()
        layout.operator("uv.unwrap", text="Unfold (Unwrap)")
        layout.operator("uv.smart_project", text="Automatic (Smart UV)")


class MAYA_MT_rmb_inputs(bpy.types.Menu):
    bl_idname = "MAYA_MT_rmb_inputs"
    bl_label = "Inputs"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj is None or not obj.modifiers:
            layout.label(text="(no history)")
            return
        for mod in obj.modifiers:
            layout.prop(mod, "show_viewport", text=mod.name)
        layout.separator()
        layout.operator("maya.delete_history", icon='TRASH')


class MAYA_MT_rmb_paint(bpy.types.Menu):
    bl_idname = "MAYA_MT_rmb_paint"
    bl_label = "Paint"

    def draw(self, context):
        layout = self.layout
        for mode, text, icon in (
            ('SCULPT', "Sculpt", 'SCULPTMODE_HLT'),
            ('VERTEX_PAINT', "Vertex Color", 'VPAINT_HLT'),
            ('WEIGHT_PAINT', "Skin Weights", 'WPAINT_HLT'),
            ('TEXTURE_PAINT', "Texture", 'TPAINT_HLT'),
        ):
            layout.operator("object.mode_set", text=text, icon=icon).mode = mode


class MAYA_MT_rmb_uv_sets(bpy.types.Menu):
    bl_idname = "MAYA_MT_rmb_uv_sets"
    bl_label = "UV Sets"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj is None or obj.type != 'MESH' or not obj.data.uv_layers:
            layout.label(text="(no UV sets)")
        else:
            uv_layers = obj.data.uv_layers
            for i, uv in enumerate(uv_layers):
                icon = 'RADIOBUT_ON' if i == uv_layers.active_index else 'RADIOBUT_OFF'
                layout.operator("maya.set_active_uv", text=uv.name, icon=icon).index = i
        layout.separator()
        layout.operator("mesh.uv_texture_add", text="Create Empty UV Set", icon='ADD')


class MAYA_MT_rmb_new_material(bpy.types.Menu):
    bl_idname = "MAYA_MT_rmb_new_material"
    bl_label = "Assign New Material"

    def draw(self, context):
        for key, name, _desc in SHADERS:
            self.layout.operator("maya.assign_new_material", text=name, icon='MATERIAL').shader = key


class MAYA_MT_rmb_existing_material(bpy.types.Menu):
    bl_idname = "MAYA_MT_rmb_existing_material"
    bl_label = "Assign Existing Material"

    def draw(self, context):
        layout = self.layout
        if not bpy.data.materials:
            layout.label(text="(no materials)")
            return
        for mat in bpy.data.materials:
            layout.operator("maya.assign_existing_material", text=mat.name, icon='MATERIAL').material = mat.name


# ---------------------------------------------------------------------------
# The marking menu itself
# ---------------------------------------------------------------------------

def _component(layout, text, mode):
    layout.operator("maya.component_mode", text=text).mode = mode


def _draw_object_list(layout, context):
    obj = context.active_object
    col = layout.column()
    col.operator("maya.show_attributes", text=obj.name + "...").tab = 'OBJECT'
    col.separator()
    col.operator("maya.select_only", text="Select")
    col.operator("object.select_all", text="Select All").action = 'SELECT'
    col.operator("object.select_all", text="Deselect All").action = 'DESELECT'
    op = col.operator("object.select_grouped", text="Select Hierarchy")
    op.type = 'CHILDREN_RECURSIVE'
    op.extend = True
    col.operator("object.select_all", text="Invert Selection").action = 'INVERT'
    col.separator()
    op = col.operator("object.select_grouped", text="Select Similar")
    op.type = 'TYPE'
    op.extend = True
    col.separator()
    col.menu("MAYA_MT_rmb_inputs")
    col.menu("MAYA_MT_rmb_paint")
    col.menu("MAYA_MT_rmb_uv_sets")
    col.separator()
    col.operator("maya.show_attributes", text="Material Attributes...").tab = 'MATERIAL'
    col.separator()
    col.menu("MAYA_MT_rmb_new_material")
    col.menu("MAYA_MT_rmb_existing_material")


def _draw_edit_list(layout, context):
    obj = context.active_object
    col = layout.column()
    col.operator("maya.show_attributes", text=obj.name + "...").tab = 'DATA'
    col.separator()
    col.operator("mesh.select_all", text="Select All").action = 'SELECT'
    col.operator("mesh.select_all", text="Deselect All").action = 'DESELECT'
    col.operator("mesh.select_all", text="Invert Selection").action = 'INVERT'
    col.operator("mesh.select_linked", text="Select Shell")
    if "select_edge_loop_multi" in dir(bpy.ops.mesh):  # renamed in newer Blender
        col.operator("mesh.select_edge_loop_multi", text="Select Edge Loop")
        col.operator("mesh.select_edge_ring_multi", text="Select Edge Ring")
    else:
        col.operator("mesh.loop_multi_select", text="Select Edge Loop").ring = False
        col.operator("mesh.loop_multi_select", text="Select Edge Ring").ring = True
    col.operator("mesh.select_more", text="Grow Selection")
    col.operator("mesh.select_less", text="Shrink Selection")
    col.separator()
    col.operator("mesh.select_similar", text="Select Similar")
    col.separator()
    col.menu("MAYA_MT_rmb_inputs")
    col.menu("MAYA_MT_rmb_uv_sets")
    col.separator()
    col.operator("maya.show_attributes", text="Material Attributes...").tab = 'MATERIAL'
    col.separator()
    col.menu("MAYA_MT_rmb_new_material")
    col.menu("MAYA_MT_rmb_existing_material")


class MAYA_MT_rmb_object(bpy.types.Menu):
    bl_idname = "MAYA_MT_rmb_object"
    bl_label = ""

    def draw(self, context):
        pie = self.layout.menu_pie()
        is_mesh = context.active_object is not None and context.active_object.type == 'MESH'

        _component(pie, "Vertex", 'VERT')                           # W
        if is_mesh:                                                # E
            pie.menu("MAYA_MT_rmb_uv", text="UV")
        else:
            pie.separator()

        bottom = pie.column()                                      # S
        _component(bottom, "Face", 'FACE')
        bottom.separator()
        box = bottom.box()
        if context.mode == 'EDIT_MESH':
            _draw_edit_list(box, context)
        else:
            _draw_object_list(box, context)

        _component(pie, "Edge", 'EDGE')                             # N
        pie.separator()                                            # NW
        _component(pie, "Object Mode", 'OBJECT')                    # NE
        _component(pie, "Vertex Face", 'VERT_FACE')                 # SW
        _component(pie, "Multi", 'MULTI')                           # SE


classes = (
    MAYA_OT_rmb_menu,
    MAYA_OT_show_attributes,
    MAYA_OT_select_only,
    MAYA_OT_open_uv_editor,
    MAYA_OT_set_active_uv,
    MAYA_OT_assign_new_material,
    MAYA_OT_assign_existing_material,
    MAYA_MT_rmb_uv,
    MAYA_MT_rmb_inputs,
    MAYA_MT_rmb_paint,
    MAYA_MT_rmb_uv_sets,
    MAYA_MT_rmb_new_material,
    MAYA_MT_rmb_existing_material,
    MAYA_MT_rmb_object,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
