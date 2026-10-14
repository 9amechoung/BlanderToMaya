"""Maya Quick Select Sets: Create > Sets > Quick Select Set, Edit > Quick Select Sets.

A set remembers a list of objects by name (saved in the scene). Picking it from
the menu selects those objects again. In component mode a set is made from the
selected vertices instead (stored as a vertex group of the same name).
"""

import bpy
from bpy.props import BoolProperty, CollectionProperty, StringProperty

SEP = "\n"


class MAYA_PG_select_set(bpy.types.PropertyGroup):
    members: StringProperty(name="Members")


def _sets(scene):
    return scene.maya_select_sets


class MAYA_OT_create_select_set(bpy.types.Operator):
    """Create a Quick Select Set from the selection (Maya: Create > Sets > Quick Select Set)"""
    bl_idname = "maya.create_select_set"
    bl_label = "Create Quick Select Set"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Name", default="set1")

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            return True
        return bool(context.selected_objects)

    def invoke(self, context, event):
        existing = {s.name for s in _sets(context.scene)}
        if context.active_object is not None:
            existing |= {g.name for g in context.active_object.vertex_groups}
        i = 1
        while "set%d" % i in existing:
            i += 1
        self.name = "set%d" % i
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            obj = context.edit_object
            group = obj.vertex_groups.new(name=self.name)
            obj.vertex_groups.active_index = group.index
            bpy.ops.object.vertex_group_assign()
            self.report({'INFO'}, "Component set (vertex group): " + group.name)
            return {'FINISHED'}
        item = _sets(context.scene).get(self.name) or _sets(context.scene).add()
        item.name = self.name
        item.members = SEP.join(o.name for o in context.selected_objects)
        return {'FINISHED'}


class MAYA_OT_select_set(bpy.types.Operator):
    """Select the members of this Quick Select Set"""
    bl_idname = "maya.select_set"
    bl_label = "Select Set"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()
    add: BoolProperty(name="Add to Selection", default=False)
    component: BoolProperty(default=False, options={'HIDDEN'})

    def invoke(self, context, event):
        self.add = event.shift
        return self.execute(context)

    def execute(self, context):
        if self.component:
            obj = context.edit_object
            group = obj.vertex_groups.get(self.name) if obj else None
            if group is None:
                return {'CANCELLED'}
            if not self.add:
                bpy.ops.mesh.select_all(action='DESELECT')
            obj.vertex_groups.active_index = group.index
            bpy.ops.object.vertex_group_select()
            return {'FINISHED'}
        item = _sets(context.scene).get(self.name)
        if item is None:
            return {'CANCELLED'}
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        view_layer = context.view_layer
        if not self.add:
            for obj in view_layer.objects:
                obj.select_set(False)
        found = [view_layer.objects.get(n) for n in item.members.split(SEP)]
        found = [o for o in found if o is not None]
        for obj in found:
            obj.select_set(True)
        if found:
            view_layer.objects.active = found[0]
        missing = len(item.members.split(SEP)) - len(found)
        if missing:
            self.report({'WARNING'}, "%d object(s) of %s are gone or renamed" % (missing, self.name))
        return {'FINISHED'}


class MAYA_OT_delete_select_set(bpy.types.Operator):
    """Delete this Quick Select Set (the objects stay)"""
    bl_idname = "maya.delete_select_set"
    bl_label = "Delete Set"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()

    def execute(self, context):
        sets = _sets(context.scene)
        index = sets.find(self.name)
        if index < 0:
            return {'CANCELLED'}
        sets.remove(index)
        return {'FINISHED'}


class MAYA_MT_select_sets(bpy.types.Menu):
    bl_label = "Quick Select Sets"

    def draw(self, context):
        lay = self.layout
        lay.operator("maya.create_select_set", text="Create Quick Select Set...", icon='ADD')
        sets = _sets(context.scene)
        obj = context.edit_object
        groups = obj.vertex_groups if obj is not None and context.mode == 'EDIT_MESH' else ()
        if not sets and not groups:
            lay.label(text="(no sets yet)")
            return
        lay.separator()
        for item in sets:
            lay.operator("maya.select_set", text=item.name, icon='RESTRICT_SELECT_OFF').name = item.name
        for group in groups:
            o = lay.operator("maya.select_set", text=group.name + "  (vertices)", icon='GROUP_VERTEX')
            o.name = group.name
            o.component = True
        if sets:
            lay.separator()
            lay.menu("MAYA_MT_delete_select_sets", icon='X')


class MAYA_MT_delete_select_sets(bpy.types.Menu):
    bl_label = "Delete Set"

    def draw(self, context):
        for item in _sets(context.scene):
            self.layout.operator("maya.delete_select_set", text=item.name).name = item.name


classes = (
    MAYA_PG_select_set,
    MAYA_OT_create_select_set,
    MAYA_OT_select_set,
    MAYA_OT_delete_select_set,
    MAYA_MT_select_sets,
    MAYA_MT_delete_select_sets,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.maya_select_sets = CollectionProperty(type=MAYA_PG_select_set)


def unregister():
    del bpy.types.Scene.maya_select_sets
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
