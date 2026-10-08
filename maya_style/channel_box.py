"""Maya-style Channel Box: in the 3D viewport sidebar (N panel) and at the
top of the Properties editor's Object tab (Maya's right-hand panel)."""

import bpy

AXES = ("X", "Y", "Z")


def _channel(col, data, prop, label, index=-1):
    row = col.row(align=True)
    split = row.split(factor=0.45, align=True)
    split.alignment = 'RIGHT'
    split.label(text=label)
    split.prop(data, prop, index=index, text="")


class MAYA_PT_channel_box(bpy.types.Panel):
    bl_idname = "MAYA_PT_channel_box"
    bl_label = "Channel Box"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Channel Box"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        draw_channel_box(self.layout, context.active_object)


def draw_channel_box(layout, obj, show_name=True):
    if show_name:
        layout.prop(obj, "name", text="", icon='OBJECT_DATA')

    col = layout.column(align=True)
    for i, axis in enumerate(AXES):
        _channel(col, obj, "location", "Translate " + axis, i)
    col.separator()
    if obj.rotation_mode == 'QUATERNION':
        for i, axis in enumerate(("W", "X", "Y", "Z")):
            _channel(col, obj, "rotation_quaternion", "Rotate " + axis, i)
    elif obj.rotation_mode == 'AXIS_ANGLE':
        for i, axis in enumerate(("W", "X", "Y", "Z")):
            _channel(col, obj, "rotation_axis_angle", "Rotate " + axis, i)
    else:
        for i, axis in enumerate(AXES):
            _channel(col, obj, "rotation_euler", "Rotate " + axis, i)
    col.separator()
    for i, axis in enumerate(AXES):
        _channel(col, obj, "scale", "Scale " + axis, i)
    col.separator()
    _channel(col, obj, "hide_viewport", "Visibility")

    # Custom attributes (Modify > Add Attribute) are listed under the transforms, like Maya.
    custom = [k for k in obj.keys() if not k.startswith("_") and isinstance(obj[k], (int, float, str))]
    if custom:
        col.separator()
        for key in custom:
            _channel(col, obj, '["%s"]' % key, key)

    if obj.data is not None:
        layout.separator()
        layout.label(text="SHAPES")
        layout.prop(obj.data, "name", text="", icon='MESH_DATA' if obj.type == 'MESH' else 'OBJECT_DATA')

    layout.separator()
    layout.label(text="INPUTS")
    if obj.modifiers:
        col = layout.column(align=True)
        for mod in obj.modifiers:
            row = col.row(align=True)
            row.prop(mod, "show_viewport", text="")
            row.prop(mod, "name", text="")
    else:
        layout.label(text="(no history)", icon='INFO')


class MAYA_OT_create_layer(bpy.types.Operator):
    """Create a new layer (collection) and move the selected objects into it"""
    bl_idname = "maya.create_layer"
    bl_label = "Create Layer from Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layer = bpy.data.collections.new("layer1")
        context.scene.collection.children.link(layer)
        for obj in context.selected_objects:
            for col in list(obj.users_collection):
                col.objects.unlink(obj)
            layer.objects.link(obj)
        return {'FINISHED'}


class MAYA_PT_layer_editor(bpy.types.Panel):
    bl_idname = "MAYA_PT_layer_editor"
    bl_label = "Layer Editor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Channel Box"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        view_layer = context.view_layer

        def draw_children(layer_collection, depth):
            for child in layer_collection.children:
                row = layout.row(align=True)
                for _ in range(depth):
                    row.separator()
                row.prop(child, "hide_viewport", text="", emboss=False)
                row.prop(child.collection, "hide_render", text="", emboss=False)
                row.label(text=child.name, icon='OUTLINER_COLLECTION')
                draw_children(child, depth + 1)

        draw_children(view_layer.layer_collection, 0)
        layout.operator("maya.create_layer", icon='ADD')


def _draw_in_properties(self, context):
    """Channel Box drawn inside the object-name panel, so it is always at the top.

    (A separate panel would be placed after Blender's own Object panels.)"""
    from .prefs import get_prefs
    prefs = get_prefs(context)
    obj = context.object
    if obj is None or (prefs is not None and not prefs.channel_box_in_properties):
        return
    box = self.layout.box()
    box.label(text="Channel Box", icon='PROPERTIES')
    draw_channel_box(box, obj, show_name=False)


class MAYA_PT_layer_editor_properties(MAYA_PT_layer_editor):
    bl_idname = "MAYA_PT_layer_editor_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = set()


classes = (
    MAYA_OT_create_layer,
    MAYA_PT_channel_box,
    MAYA_PT_layer_editor,
    MAYA_PT_layer_editor_properties,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.OBJECT_PT_context_object.append(_draw_in_properties)


def unregister():
    bpy.types.OBJECT_PT_context_object.remove(_draw_in_properties)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
