import os

import bpy
from bpy.props import EnumProperty, StringProperty


def set_props(operator_props, props):
    """Set operator button properties, skipping ones this Blender version / context rejects
    (dynamic enums like mesh.merge's 'LAST' only exist in some situations)."""
    for key, value in props.items():
        try:
            setattr(operator_props, key, value)
        except (TypeError, AttributeError, ValueError):
            pass


def find_keyconfig_preset(name):
    """Return the path of a bundled keyconfig preset (e.g. 'Industry_Compatible')."""
    for directory in bpy.utils.preset_paths("keyconfig"):
        for filename in os.listdir(directory):
            stem, ext = os.path.splitext(filename)
            if ext == ".py" and stem.lower() == name.lower():
                return os.path.join(directory, filename)
    return None


def activate_keyconfig(name):
    path = find_keyconfig_preset(name)
    if path is None:
        return False
    bpy.ops.preferences.keyconfig_activate(filepath=path)
    return True


class MAYA_OT_apply_keymap(bpy.types.Operator):
    """Switch to the Industry Compatible keymap (Alt+mouse navigation, QWER, F to frame...)"""
    bl_idname = "maya.apply_keymap"
    bl_label = "Apply Maya Keymap"

    def execute(self, context):
        if not activate_keyconfig("Industry_Compatible"):
            self.report({'ERROR'}, "Industry Compatible keymap preset not found")
            return {'CANCELLED'}
        self.report({'INFO'}, "Maya-style (Industry Compatible) keymap applied")
        return {'FINISHED'}


class MAYA_OT_restore_keymap(bpy.types.Operator):
    """Switch back to the default Blender keymap"""
    bl_idname = "maya.restore_keymap"
    bl_label = "Restore Blender Keymap"

    def execute(self, context):
        if not activate_keyconfig("Blender"):
            self.report({'ERROR'}, "Blender keymap preset not found")
            return {'CANCELLED'}
        self.report({'INFO'}, "Default Blender keymap restored")
        return {'FINISHED'}


class MAYA_OT_setup_viewport(bpy.types.Operator):
    """Show the tool header (where the shelf lives) in every 3D viewport"""
    bl_idname = "maya.setup_viewport"
    bl_label = "Show Shelf in All Viewports"

    def execute(self, context):
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.show_region_tool_header = True
        return {'FINISHED'}


class MAYA_OT_component_mode(bpy.types.Operator):
    """Maya-style component mode (F8: toggle, F9: vertex, F10: edge, F11: face)"""
    bl_idname = "maya.component_mode"
    bl_label = "Component Mode"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(
        items=(
            ('TOGGLE', "Object / Component", ""),
            ('VERT', "Vertex", ""),
            ('EDGE', "Edge", ""),
            ('FACE', "Face", ""),
            ('VERT_FACE', "Vertex Face", "Vertex and face selection together"),
            ('MULTI', "Multi", "Vertex, edge and face selection together"),
            ('OBJECT', "Object Mode", ""),
        ),
        default='TOGGLE',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE', 'LATTICE', 'META', 'FONT'}

    def execute(self, context):
        obj = context.active_object
        if self.mode == 'TOGGLE':
            bpy.ops.object.mode_set(mode='OBJECT' if obj.mode == 'EDIT' else 'EDIT')
            return {'FINISHED'}
        if self.mode == 'OBJECT':
            if obj.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            return {'FINISHED'}
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        if obj.type == 'MESH':
            if self.mode == 'VERT_FACE':
                context.tool_settings.mesh_select_mode = (True, False, True)
            elif self.mode == 'MULTI':
                context.tool_settings.mesh_select_mode = (True, True, True)
            else:
                bpy.ops.mesh.select_mode(type=self.mode)
        return {'FINISHED'}


class MAYA_OT_delete_history(bpy.types.Operator):
    """Apply all modifiers of the selected objects (like Maya's Delete History)"""
    bl_idname = "maya.delete_history"
    bl_label = "Delete History"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.selected_objects

    def execute(self, context):
        bpy.ops.object.convert(target='MESH')
        return {'FINISHED'}


class MAYA_OT_center_pivot(bpy.types.Operator):
    """Move the pivot (origin) to the center of the geometry"""
    bl_idname = "maya.center_pivot"
    bl_label = "Center Pivot"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.selected_objects

    def execute(self, context):
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        return {'FINISHED'}


class MAYA_OT_freeze_transforms(bpy.types.Operator):
    """Apply location, rotation and scale (like Maya's Freeze Transformations)"""
    bl_idname = "maya.freeze_transforms"
    bl_label = "Freeze Transformations"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.selected_objects

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}


class MAYA_OT_add_modifier(bpy.types.Operator):
    """Add a modifier to the active object"""
    bl_idname = "maya.add_modifier"
    bl_label = "Add Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    modifier: StringProperty()

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    @classmethod
    def description(cls, context, properties):
        return "Add a %s modifier to the active object" % properties.modifier.replace("_", " ").title()

    def execute(self, context):
        obj = context.active_object
        mod = obj.modifiers.new(name=self.modifier.replace("_", " ").title(), type=self.modifier)
        if self.modifier == 'SUBSURF':
            mod.levels = 2
            mod.render_levels = 2
        elif self.modifier == 'BEVEL':
            mod.width = 0.05
            mod.segments = 2
        return {'FINISHED'}


class MAYA_OT_set_shading(bpy.types.Operator):
    """Set the 3D viewport shading (Maya: 4 wireframe, 5 shaded, 6 textured, 7 lights)"""
    bl_idname = "maya.set_shading"
    bl_label = "Viewport Shading"

    shading: EnumProperty(
        items=(
            ('WIREFRAME', "Wireframe", ""),
            ('SOLID', "Shaded", ""),
            ('MATERIAL', "Textured", ""),
            ('RENDERED', "Rendered", ""),
        ),
    )

    @classmethod
    def poll(cls, context):
        return context.space_data is not None and context.space_data.type == 'VIEW_3D'

    def execute(self, context):
        context.space_data.shading.type = self.shading
        return {'FINISHED'}


SMOOTH_PREVIEW_NAME = "Smooth Preview"


class MAYA_OT_smooth_preview(bpy.types.Operator):
    """Maya smooth mesh preview (1: off, 2: cage + smooth, 3: smooth)"""
    bl_idname = "maya.smooth_preview"
    bl_label = "Smooth Mesh Preview"
    bl_options = {'REGISTER', 'UNDO'}

    level: EnumProperty(
        items=(
            ('1', "Off", "Show the original polygons"),
            ('2', "Cage + Smooth", "Show the smoothed mesh with the original cage"),
            ('3', "Smooth", "Show only the smoothed mesh"),
        ),
        default='3',
    )

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in cls._targets(context))

    @staticmethod
    def _targets(context):
        objs = set(context.selected_objects)
        if context.active_object is not None:
            objs.add(context.active_object)
        return [o for o in objs if o.type == 'MESH']

    def execute(self, context):
        for obj in self._targets(context):
            mod = obj.modifiers.get(SMOOTH_PREVIEW_NAME)
            if self.level == '1':
                if mod is not None:
                    obj.modifiers.remove(mod)
                obj.show_wire = False
                continue
            if mod is None:
                mod = obj.modifiers.new(SMOOTH_PREVIEW_NAME, 'SUBSURF')
                mod.levels = 2
                mod.render_levels = 2
            mod.show_viewport = True
            mod.show_in_editmode = True
            cage = self.level == '2'
            # Level 2 keeps the original cage visible (edit mode cage, wire overlay in object mode).
            mod.show_on_cage = not cage
            obj.show_wire = cage
            if hasattr(mod, "use_limit_surface"):
                mod.use_limit_surface = True
        return {'FINISHED'}


_snap_saved = None


def _grid_snap_element(tool_settings):
    items = tool_settings.bl_rna.properties["snap_elements"].enum_items.keys()
    return 'GRID' if 'GRID' in items else 'INCREMENT'


class MAYA_OT_snap_hold(bpy.types.Operator):
    """Maya-style snapping while the key is held (X: grid, V: vertex, C: curve/edge)"""
    bl_idname = "maya.snap_hold"
    bl_label = "Hold to Snap"

    element: EnumProperty(
        items=(
            ('GRID', "Grid", ""),
            ('VERTEX', "Vertex", ""),
            ('EDGE', "Curve / Edge", ""),
        ),
        default='GRID',
    )
    release: bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})

    def execute(self, context):
        global _snap_saved
        ts = context.scene.tool_settings
        if self.release:
            if _snap_saved is not None:
                ts.use_snap, ts.snap_elements, ts.use_snap_grid_absolute = _snap_saved
                _snap_saved = None
            return {'FINISHED'}
        # Only remember the user's own state, not one left over by a missed key release.
        if _snap_saved is None:
            _snap_saved = (ts.use_snap, set(ts.snap_elements), ts.use_snap_grid_absolute)
        element = self.element
        if element == 'GRID':
            element = _grid_snap_element(ts)
            ts.use_snap_grid_absolute = True
        ts.snap_elements = {element}
        ts.use_snap = True
        return {'FINISHED'}


classes = (
    MAYA_OT_apply_keymap,
    MAYA_OT_restore_keymap,
    MAYA_OT_setup_viewport,
    MAYA_OT_component_mode,
    MAYA_OT_delete_history,
    MAYA_OT_center_pivot,
    MAYA_OT_freeze_transforms,
    MAYA_OT_add_modifier,
    MAYA_OT_set_shading,
    MAYA_OT_smooth_preview,
    MAYA_OT_snap_hold,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
