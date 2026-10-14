"""Maya-style Channel Box: in the 3D viewport sidebar (N panel) and at the
top of the Properties editor's Object tab (Maya's right-hand panel)."""

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty

from .anim_tools import find_fcurve, remove_fcurve

AXES = ("X", "Y", "Z")

# Non-transform channels (Visibility, custom attributes) can't be locked or hidden in Blender
# itself, so the Channel Box remembers that in these (hidden) custom properties.
LOCKED_KEY = "_maya_locked"
HIDDEN_KEY = "_maya_hidden"

# Virtual slider (middle-drag in the viewport) speed per pixel
DRAG_SPEED = {"location": 0.01, "rotation": 0.00872665, "scale": 0.01, "custom": 0.1}


def _rotation_prop(obj):
    if obj.rotation_mode == 'QUATERNION':
        return "rotation_quaternion", ("W", "X", "Y", "Z")
    if obj.rotation_mode == 'AXIS_ANGLE':
        return "rotation_axis_angle", ("W", "X", "Y", "Z")
    return "rotation_euler", AXES


def custom_attributes(obj):
    return [k for k in obj.keys() if not k.startswith("_") and isinstance(obj[k], (int, float, str))]


def channels(obj):
    """The Channel Box rows: (key, label, data_path, index, kind). key is Maya's name (translateX...)."""
    rows = []
    for i, axis in enumerate(AXES):
        rows.append(("translate" + axis, "Translate " + axis, "location", i, "location"))
    prop, axes = _rotation_prop(obj)
    for i, axis in enumerate(axes):
        rows.append(("rotate" + axis, "Rotate " + axis, prop, i, "rotation"))
    for i, axis in enumerate(AXES):
        rows.append(("scale" + axis, "Scale " + axis, "scale", i, "scale"))
    rows.append(("visibility", "Visibility", "hide_viewport", -1, "visibility"))
    for key in custom_attributes(obj):
        rows.append((key, key, '["%s"]' % key, -1, "custom"))
    return rows


def _name_list(obj, key):
    value = obj.get(key, "")
    return set(value.split(",")) - {""} if isinstance(value, str) else set()


def _set_name_list(obj, key, names):
    if names:
        obj[key] = ",".join(sorted(names))
    elif key in obj:
        del obj[key]


def is_locked(obj, key, path, index):
    if path == "location":
        return obj.lock_location[index]
    if path == "scale":
        return obj.lock_scale[index]
    if path.startswith("rotation"):
        if path == "rotation_euler":
            return obj.lock_rotation[index]
        return obj.lock_rotation_w if index == 0 else obj.lock_rotation[index - 1]
    return key in _name_list(obj, LOCKED_KEY)


def set_locked(obj, key, path, index, lock):
    if path == "location":
        obj.lock_location[index] = lock
    elif path == "scale":
        obj.lock_scale[index] = lock
    elif path == "rotation_euler":
        obj.lock_rotation[index] = lock
    elif path.startswith("rotation"):
        if index == 0:
            obj.lock_rotation_w = lock
        else:
            obj.lock_rotation[index - 1] = lock
    else:
        names = _name_list(obj, LOCKED_KEY)
        names.add(key) if lock else names.discard(key)
        _set_name_list(obj, LOCKED_KEY, names)


def selected_channels(context):
    value = context.window_manager.maya_channels
    return [k for k in value.split(",") if k]


def _target_objects(context):
    objs = list(context.selected_objects)
    active = context.active_object
    if active is not None and active not in objs:
        objs.insert(0, active)
    return objs


def _selected_rows(context, obj):
    keys = set(selected_channels(context))
    return [row for row in channels(obj) if row[0] in keys]


def _channel(col, data, prop, label, index=-1):
    row = col.row(align=True)
    split = row.split(factor=0.45, align=True)
    split.alignment = 'RIGHT'
    split.label(text=label)
    split.prop(data, prop, index=index, text="")


def _channel_row(col, obj, key, label, path, index, picked):
    row = col.row(align=True)
    split = row.split(factor=0.45, align=True)
    # Clicking the channel name selects it, like Maya (then middle-drag in the viewport)
    name = split.row(align=True)
    name.alignment = 'RIGHT'
    o = name.operator("maya.channel_select", text=label, emboss=picked, depress=picked)
    o.channel = key
    field = split.row(align=True)
    field.enabled = not is_locked(obj, key, path, index)
    field.prop(obj, path, index=index, text="")


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
        draw_channel_box(self.layout, context.active_object, context=context)


def draw_channel_box(layout, obj, show_name=True, context=None):
    context = context or bpy.context
    row = layout.row(align=True)
    for menu in ("MAYA_MT_channels", "MAYA_MT_channel_edit", "MAYA_MT_channel_show"):
        row.menu(menu)
    if show_name:
        layout.prop(obj, "name", text="", icon='OBJECT_DATA')

    picked = set(selected_channels(context))
    hidden = _name_list(obj, HIDDEN_KEY)
    col = layout.column(align=True)
    last_kind = None
    for key, label, path, index, kind in channels(obj):
        if key in hidden:
            continue
        if last_kind is not None and kind != last_kind:
            if last_kind == "rotation":
                sub = col.row(align=True).split(factor=0.45, align=True)
                sub.alignment = 'RIGHT'
                sub.label(text="Rotate Order")
                sub.prop(obj, "rotation_mode", text="")
            col.separator()
        last_kind = kind
        _channel_row(col, obj, key, label, path, index, key in picked)
    if picked:
        layout.label(text="Middle-drag in the viewport to change", icon='MOUSE_MMB_DRAG')

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


# ---------------------------------------------------------------------------
# Channel selection and the Channels / Edit / Show menus
# ---------------------------------------------------------------------------

class MAYA_OT_channel_select(bpy.types.Operator):
    """Select this channel (Ctrl: toggle, Shift: range). Then middle-drag in the viewport to change it,
    or use the Channels menu (Key / Lock / Hide / Break Connections)"""
    bl_idname = "maya.channel_select"
    bl_label = "Select Channel"
    bl_options = {'INTERNAL'}

    channel: StringProperty()
    extend: BoolProperty(default=False, options={'SKIP_SAVE'})
    range: BoolProperty(default=False, options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self.extend = event.ctrl
        self.range = event.shift
        return self.execute(context)

    def execute(self, context):
        wm = context.window_manager
        picked = selected_channels(context)
        if self.range and picked and context.active_object is not None:
            keys = [row[0] for row in channels(context.active_object)]
            if picked[-1] in keys and self.channel in keys:
                a, b = sorted((keys.index(picked[-1]), keys.index(self.channel)))
                picked = picked + [k for k in keys[a:b + 1] if k not in picked]
        elif self.extend:
            if self.channel in picked:
                picked.remove(self.channel)
            else:
                picked.append(self.channel)
        else:
            picked = [] if picked == [self.channel] else [self.channel]
        wm.maya_channels = ",".join(picked)
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}


CHANNEL_ACTIONS = (
    ('KEY', "Key Selected", "Set a key on the selected channels"),
    ('KEY_ALL', "Key All", "Set a key on every channel"),
    ('BREAK', "Break Connections", "Remove the animation and drivers of the selected channels"),
    ('MUTE', "Mute Selected", "Mute the animation of the selected channels"),
    ('UNMUTE', "Unmute Selected", "Unmute the animation of the selected channels"),
    ('LOCK', "Lock Selected", "Lock the selected channels"),
    ('UNLOCK', "Unlock Selected", "Unlock the selected channels"),
    ('HIDE', "Hide Selected", "Hide the selected channels from the Channel Box"),
    ('LOCK_HIDE', "Lock and Hide Selected", "Lock the selected channels and hide them"),
    ('UNHIDE_ALL', "Show All Channels", "Show the hidden channels again"),
    ('DELETE_ATTR', "Delete Attributes", "Delete the selected custom attributes"),
    ('CLEAR', "Deselect Channels", "Deselect all channels"),
)
CHANNEL_ACTION_INFO = {key: (name, desc) for key, name, desc in CHANNEL_ACTIONS}


class MAYA_OT_channel_action(bpy.types.Operator):
    """Apply to the selected channels of the selected objects (Maya Channel Box > Channels)"""
    bl_idname = "maya.channel_action"
    bl_label = "Channel Action"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(items=CHANNEL_ACTIONS)

    @classmethod
    def description(cls, context, properties):
        return CHANNEL_ACTION_INFO.get(properties.action, ("", ""))[1]

    def execute(self, context):
        action = self.action
        wm = context.window_manager
        if action == 'CLEAR':
            wm.maya_channels = ""
            return {'FINISHED'}
        objs = _target_objects(context)
        if not objs:
            self.report({'WARNING'}, "Nothing selected")
            return {'CANCELLED'}
        frame = context.scene.frame_current
        done = 0
        for obj in objs:
            if action == 'UNHIDE_ALL':
                _set_name_list(obj, HIDDEN_KEY, set())
                done += 1
                continue
            rows = channels(obj) if action == 'KEY_ALL' else _selected_rows(context, obj)
            for key, _label, path, index, kind in rows:
                done += 1
                if action in {'KEY', 'KEY_ALL'}:
                    try:
                        obj.keyframe_insert(data_path=path, index=index, frame=frame)
                    except (RuntimeError, TypeError):
                        done -= 1
                elif action == 'BREAK':
                    try:
                        obj.driver_remove(path, index)
                    except (RuntimeError, TypeError):
                        pass
                    fc = find_fcurve(obj, path, index)
                    while fc is not None:
                        remove_fcurve(obj, fc)
                        fc = find_fcurve(obj, path, index)
                elif action in {'MUTE', 'UNMUTE'}:
                    fc = find_fcurve(obj, path, index)
                    if fc is not None:
                        fc.mute = action == 'MUTE'
                elif action in {'LOCK', 'UNLOCK', 'LOCK_HIDE'}:
                    set_locked(obj, key, path, index, action != 'UNLOCK')
                if action in {'HIDE', 'LOCK_HIDE'}:
                    hidden = _name_list(obj, HIDDEN_KEY)
                    hidden.add(key)
                    _set_name_list(obj, HIDDEN_KEY, hidden)
                elif action == 'DELETE_ATTR' and kind == "custom" and key in obj:
                    del obj[key]
        if action in {'HIDE', 'LOCK_HIDE', 'DELETE_ATTR'}:
            wm.maya_channels = ""
        if not done:
            self.report({'WARNING'}, "Select a channel name in the Channel Box first")
            return {'CANCELLED'}
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}


class MAYA_MT_channels(bpy.types.Menu):
    bl_label = "Channels"

    def draw(self, context):
        lay = self.layout
        for action, icon in (('KEY', 'KEY_HLT'), ('KEY_ALL', 'KEYFRAME'), (None, None), ('BREAK', 'UNLINKED'),
                             ('MUTE', 'MUTE_IPO_ON'), ('UNMUTE', 'MUTE_IPO_OFF'), (None, None),
                             ('LOCK', 'LOCKED'), ('UNLOCK', 'UNLOCKED'), ('HIDE', 'HIDE_ON'),
                             ('LOCK_HIDE', 'DECORATE_LOCKED')):
            if action is None:
                lay.separator()
            else:
                lay.operator("maya.channel_action", icon=icon,
                             text=_action_name(action)).action = action
        lay.separator()
        lay.operator("maya.channel_action", text="Deselect Channels").action = 'CLEAR'


class MAYA_MT_channel_edit(bpy.types.Menu):
    bl_label = "Edit"

    def draw(self, context):
        lay = self.layout
        lay.operator("maya.add_attribute", text="Add Attribute...", icon='ADD')
        lay.operator("maya.channel_action", text="Delete Attributes", icon='X').action = 'DELETE_ATTR'
        lay.separator()
        lay.operator("maya.open_editor", text="Set Driven Key / Expressions (Drivers)",
                     icon='DRIVER').ui_type = 'DRIVERS'
        lay.operator("maya.open_editor", text="Graph Editor", icon='GRAPH').ui_type = 'FCURVES'


class MAYA_MT_channel_show(bpy.types.Menu):
    bl_label = "Show"

    def draw(self, context):
        self.layout.operator("maya.channel_action", text="Show All Channels", icon='HIDE_OFF').action = 'UNHIDE_ALL'


def _action_name(action):
    return CHANNEL_ACTION_INFO[action][0]


# ---------------------------------------------------------------------------
# Virtual slider: middle-drag in the viewport changes the selected channels
# ---------------------------------------------------------------------------

def channel_drag_available(context):
    if context.mode != 'OBJECT' or not selected_channels(context):
        return False
    obj = context.active_object or (context.selected_objects[0] if context.selected_objects else None)
    return obj is not None and bool(_selected_rows(context, obj))


class MAYA_OT_channel_drag(bpy.types.Operator):
    """Middle-drag left / right to change the selected Channel Box channels
    (Ctrl: slower, Shift: faster), like Maya's virtual slider"""
    bl_idname = "maya.channel_drag"
    bl_label = "Channel Box Virtual Slider"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}

    @classmethod
    def poll(cls, context):
        return channel_drag_available(context)

    def invoke(self, context, event):
        self._start_x = event.mouse_x
        self._start = []
        for obj in _target_objects(context):
            for key, _label, path, index, kind in _selected_rows(context, obj):
                if kind == "visibility" or is_locked(obj, key, path, index):
                    continue
                value = self._get(obj, path, index)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    self._start.append((obj, path, index, kind, value))
        if not self._start:
            return {'CANCELLED'}
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    @staticmethod
    def _get(obj, path, index):
        if path.startswith('["'):
            return obj[path[2:-2]]
        value = getattr(obj, path)
        return value[index] if index >= 0 else value

    @staticmethod
    def _set(obj, path, index, value):
        if path.startswith('["'):
            key = path[2:-2]
            obj[key] = int(round(value)) if isinstance(obj[key], int) else value
        elif index >= 0:
            getattr(obj, path)[index] = value
        else:
            setattr(obj, path, value)

    def _apply(self, context, event):
        factor = 0.1 if event.ctrl else 10.0 if event.shift else 1.0
        dx = (event.mouse_x - self._start_x) * factor
        for obj, path, index, kind, start in self._start:
            self._set(obj, path, index, start + dx * DRAG_SPEED.get(kind, 0.01))
        context.area.header_text_set("Virtual slider: %+.3f   (Ctrl: slower, Shift: faster)" %
                                     (dx * DRAG_SPEED.get(self._start[0][3], 0.01)))

    def _finish(self, context):
        context.area.header_text_set(None)
        if context.scene.tool_settings.use_keyframe_insert_auto:
            frame = context.scene.frame_current
            for obj, path, index, _kind, _start in self._start:
                try:
                    obj.keyframe_insert(data_path=path, index=index, frame=frame)
                except (RuntimeError, TypeError):
                    pass

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            self._apply(context, event)
        elif event.type in {'MIDDLEMOUSE', 'LEFTMOUSE', 'RET'} and event.value == 'RELEASE':
            self._finish(context)
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            for obj, path, index, _kind, start in self._start:
                self._set(obj, path, index, start)
            context.area.header_text_set(None)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}


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


LAYER_DISPLAY_KEY = "_maya_display"
PREV_DISPLAY_KEY = "_maya_prev_display"


def _layer_objects(collection):
    return list(collection.all_objects)


def set_layer_display(collection, state):
    """'' normal, 'T' template (grey wireframe, not selectable), 'R' reference (shaded, not selectable)."""
    for obj in _layer_objects(collection):
        if state == 'T':
            if PREV_DISPLAY_KEY not in obj:
                obj[PREV_DISPLAY_KEY] = obj.display_type
            obj.display_type = 'WIRE'
            obj.select_set(False)
        elif PREV_DISPLAY_KEY in obj:
            obj.display_type = obj[PREV_DISPLAY_KEY]
            del obj[PREV_DISPLAY_KEY]
        if state:
            obj.select_set(False)
    collection.hide_select = bool(state)
    if state:
        collection[LAYER_DISPLAY_KEY] = state
    elif LAYER_DISPLAY_KEY in collection:
        del collection[LAYER_DISPLAY_KEY]


class MAYA_OT_layer_display_type(bpy.types.Operator):
    """Layer display type: normal -> T (Template: grey wireframe, not selectable) ->
    R (Reference: shaded, not selectable) -> normal"""
    bl_idname = "maya.layer_display_type"
    bl_label = "Layer Display Type"
    bl_options = {'REGISTER', 'UNDO'}

    collection: StringProperty()

    def execute(self, context):
        collection = bpy.data.collections.get(self.collection)
        if collection is None:
            return {'CANCELLED'}
        state = collection.get(LAYER_DISPLAY_KEY, "")
        set_layer_display(collection, {"": 'T', 'T': 'R'}.get(state, ""))
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
                # Maya's display type column: blank (normal) / T (template) / R (reference)
                state = child.collection.get(LAYER_DISPLAY_KEY, "")
                o = row.operator("maya.layer_display_type", text=state or " ", emboss=bool(state),
                                 depress=bool(state))
                o.collection = child.collection.name
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
    box.label(text="Channel Box (Local)", icon='PROPERTIES')
    draw_channel_box(box, obj, show_name=False, context=context)
    from .transform_panel import draw_components, draw_world_space
    draw_components(self.layout, obj)
    draw_world_space(self.layout, obj)


class MAYA_PT_layer_editor_properties(MAYA_PT_layer_editor):
    bl_idname = "MAYA_PT_layer_editor_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = set()


classes = (
    MAYA_OT_channel_select,
    MAYA_OT_channel_action,
    MAYA_MT_channels,
    MAYA_MT_channel_edit,
    MAYA_MT_channel_show,
    MAYA_OT_channel_drag,
    MAYA_OT_layer_display_type,
    MAYA_OT_create_layer,
    MAYA_PT_channel_box,
    MAYA_PT_layer_editor,
    MAYA_PT_layer_editor_properties,
)


def register():
    bpy.types.WindowManager.maya_channels = StringProperty(
        name="Selected Channels", description="Channel Box channels picked by clicking their names")
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.OBJECT_PT_context_object.append(_draw_in_properties)


def unregister():
    bpy.types.OBJECT_PT_context_object.remove(_draw_in_properties)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.maya_channels
