"""Maya's Input Line (right end of the status line).

Pick a mode, type, press Enter:
  Select by Name   pCube* light1   (wildcards, several names separated by spaces)
  Rename           newName         (several objects: newName1, newName2... ; # marks the number)
  Absolute         1 2 3           (move / rotate / scale to these values, by the active tool)
  Relative         0 1 0           (move / rotate / scale by these values)
"""

import fnmatch
import math
import re

import bpy
from bpy.props import EnumProperty, StringProperty

MODES = (
    ('SELECT', "Select by Name", "Select objects by name (wildcards: * ?)", 'RESTRICT_SELECT_OFF', 0),
    ('RENAME', "Rename", "Rename the selected objects", 'SORTALPHA', 1),
    ('ABSOLUTE', "Absolute Transform", "Move / rotate / scale the selection to these values "
                                       "(uses the active tool, Move when none)", 'ORIENTATION_GLOBAL', 2),
    ('RELATIVE', "Relative Transform", "Move / rotate / scale the selection by these values "
                                       "(uses the active tool, Move when none)", 'ORIENTATION_LOCAL', 3),
)

_busy = False


def _numbers(text):
    """'1 2 3' -> [1.0, 2.0, 3.0]; '. 2' keeps the first value (None)."""
    values = []
    for part in text.replace(",", " ").split():
        try:
            values.append(float(part))
        except ValueError:
            values.append(None)
    return (values + [None, None, None])[:3]


def _tool_kind(context):
    from .transform_tools import active_tool_kind
    return active_tool_kind(context) or 'TRANSLATE'


def select_by_name(context, text):
    patterns = text.split()
    view_layer = context.view_layer
    matches = [o for o in view_layer.objects
               if any(fnmatch.fnmatchcase(o.name, p) for p in patterns) and o.visible_get()]
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for obj in view_layer.objects:
        obj.select_set(False)
    for obj in matches:
        obj.select_set(True)
    if matches:
        view_layer.objects.active = matches[0]
    return len(matches)


def rename(context, text):
    objs = list(context.selected_objects)
    if not objs:
        return 0
    if len(objs) == 1 and "#" not in text:
        objs[0].name = text
        return 1
    # Maya numbers several objects: name1, name2... ('#' marks where the number goes)
    objs.sort(key=lambda o: o.name)
    base = text if "#" in text else text + "#"
    pad = len(re.search(r"#+", base).group())
    for obj in objs:  # free the names first so the new ones don't get .001 suffixes
        obj.name = obj.name + "__maya_tmp"
    for i, obj in enumerate(objs, 1):
        obj.name = re.sub(r"#+", str(i).zfill(pad), base, count=1)
    return len(objs)


def transform(context, text, relative):
    values = _numbers(text)
    kind = _tool_kind(context)
    if context.mode == 'EDIT_MESH':
        # Components: relative moves only (like Maya's Move tool with the relative input line)
        if not relative or kind != 'TRANSLATE':
            return 0
        bpy.ops.transform.translate(value=[v or 0.0 for v in values])
        return 1
    count = 0
    for obj in context.selected_objects:
        if kind == 'ROTATE':
            current = obj.rotation_euler
            convert = math.radians
        elif kind == 'RESIZE':
            current = obj.scale
            convert = float
        else:
            current = obj.location
            convert = float
        for i, value in enumerate(values):
            if value is None:
                continue
            if relative:
                current[i] = current[i] * value if kind == 'RESIZE' else current[i] + convert(value)
            else:
                current[i] = convert(value)
        count += 1
    return count


def _on_enter(self, context):
    global _busy
    if _busy:
        return
    text = self.maya_input_text.strip()
    if not text:
        return
    mode = self.maya_input_mode
    try:
        if mode == 'SELECT':
            count = select_by_name(context, text)
        elif mode == 'RENAME':
            count = rename(context, text)
        else:
            count = transform(context, text, relative=mode == 'RELATIVE')
        if count:
            bpy.ops.ed.undo_push(message="Input Line")
    except Exception as ex:  # never leave an error popup from a text field
        print("Maya Style UI: input line:", ex)
    # Cleared after each command, ready for the next one
    _busy = True
    try:
        self.maya_input_text = ""
    finally:
        _busy = False


def draw_input_line(layout, context):
    wm = context.window_manager
    row = layout.row(align=True)
    row.prop(wm, "maya_input_mode", text="", icon_only=True)
    sub = row.row(align=True)
    sub.ui_units_x = 7
    if _supports_placeholder():
        sub.prop(wm, "maya_input_text", text="", placeholder=_placeholder(wm))
    else:
        sub.prop(wm, "maya_input_text", text="")


def _placeholder(wm):
    return {'SELECT': "Select by name", 'RENAME': "Rename", 'ABSOLUTE': "Absolute: x y z",
            'RELATIVE': "Relative: x y z"}[wm.maya_input_mode]


_placeholder_ok = None


def _supports_placeholder():
    global _placeholder_ok
    if _placeholder_ok is None:
        _placeholder_ok = "placeholder" in bpy.types.UILayout.bl_rna.functions["prop"].parameters
    return _placeholder_ok


def register():
    bpy.types.WindowManager.maya_input_mode = EnumProperty(
        name="Input Line Mode", description="What the input line does with what you type", items=MODES)
    bpy.types.WindowManager.maya_input_text = StringProperty(
        name="Input Line", description="Maya input line: type and press Enter", update=_on_enter)


def unregister():
    del bpy.types.WindowManager.maya_input_text
    del bpy.types.WindowManager.maya_input_mode
