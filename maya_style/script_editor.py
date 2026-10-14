"""Maya Script Editor: history on top, input below, Ctrl+Enter runs the script.

Windows > General Editors > Script Editor opens a new window with Blender's Info
editor (the history: every command you run is echoed there as Python) above a
Text Editor (the input). In the Text Editor, Ctrl+Enter or numpad Enter runs the
selected lines, or the whole script when nothing is selected, like Maya. What the
script prints shows up in the history.
"""

import contextlib
import io
import traceback

import bpy

# Like Maya, variables defined by one run are still there for the next one.
_namespace = {}


def run_python(code, report, echo=True):
    """Run Python code, sending what it prints (and errors) to the Info history. Returns True on success."""
    ns = _namespace
    ns.setdefault("__name__", "__main__")
    ns["bpy"] = bpy
    ns["C"] = bpy.context
    ns["D"] = bpy.data
    out = io.StringIO()
    error = None
    try:
        with contextlib.redirect_stdout(out):
            exec(compile(code, "<script editor>", "exec"), ns)
    except Exception as ex:
        error = ex
    printed = out.getvalue().rstrip("\n")
    if printed:
        print(printed)
        for line in printed.splitlines():
            report({'INFO'}, line)
    if error is not None:
        # Leave out this function's own frame: the traceback starts in the script
        tb = error.__traceback__.tb_next
        for line in "".join(traceback.format_exception(type(error), error, tb)).rstrip().splitlines():
            report({'ERROR'}, line)
        return False
    if echo and not printed:
        first = code.strip().splitlines()[0] if code.strip() else ""
        report({'INFO'}, "# " + first[:120] + (" ..." if len(code.strip().splitlines()) > 1 else ""))
    return True


def selected_text(text):
    """The selected part of a Blender Text, or '' when nothing is selected."""
    a = (text.current_line_index, text.current_character)
    b = (text.select_end_line_index, text.select_end_character)
    if a == b:
        return ""
    start, end = sorted((a, b))
    lines = [line.body for line in text.lines]
    if start[0] == end[0]:
        return lines[start[0]][start[1]:end[1]]
    parts = [lines[start[0]][start[1]:]]
    parts.extend(lines[start[0] + 1:end[0]])
    parts.append(lines[end[0]][:end[1]])
    return "\n".join(parts)


class MAYA_OT_script_execute(bpy.types.Operator):
    """Run the selected lines, or the whole script when nothing is selected (Maya: Ctrl+Enter)"""
    bl_idname = "maya.script_execute"
    bl_label = "Execute"

    @classmethod
    def poll(cls, context):
        return getattr(context.space_data, "text", None) is not None

    def execute(self, context):
        text = context.space_data.text
        code = selected_text(text) or text.as_string()
        if "\n" not in code.strip():
            code = code.strip()
        run_python(code, self.report)
        return {'FINISHED'}


def _split(window, screen, area, direction, factor):
    before = {a.as_pointer() for a in screen.areas}
    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
    with bpy.context.temp_override(window=window, screen=screen, area=area, region=region):
        bpy.ops.screen.area_split(direction=direction, factor=factor)
    return next((a for a in screen.areas if a.as_pointer() not in before), None)


class MAYA_OT_script_editor(bpy.types.Operator):
    """Open the Script Editor: history (Info) on top, input (Text Editor) below, Ctrl+Enter to run"""
    bl_idname = "maya.script_editor"
    bl_label = "Script Editor"

    def execute(self, context):
        wm = context.window_manager
        before = {w.as_pointer() for w in wm.windows}
        bpy.ops.wm.window_new()
        window = next((w for w in wm.windows if w.as_pointer() not in before), None)
        if window is None:
            return {'CANCELLED'}
        screen = window.screen
        area = screen.areas[0]
        area.ui_type = 'INFO'
        text = bpy.data.texts.get("Script Editor") or bpy.data.texts.new("Script Editor")
        if not text.as_string():
            text.write("# Python. Ctrl+Enter runs the selection, or everything when nothing is selected.\n"
                       "import bpy\n\n")
        try:
            # Blender puts the new area at the bottom when the factor is below 0.5
            bottom = _split(window, screen, area, 'HORIZONTAL', 0.45)
        except RuntimeError:
            bottom = None
        if bottom is None:
            area.ui_type = 'TEXT_EDITOR'
            area.spaces.active.text = text
            return {'FINISHED'}
        bottom.ui_type = 'TEXT_EDITOR'
        space = bottom.spaces.active
        space.text = text
        space.show_line_numbers = True
        space.show_syntax_highlight = True
        return {'FINISHED'}


# (keymap, operator, key, modifiers) - registered by keymaps.py
SCRIPT_KEYS = (
    ("Text", "maya.script_execute", 'RET', {"ctrl": True}),
    ("Text", "maya.script_execute", 'NUMPAD_ENTER', {}),
)


classes = (
    MAYA_OT_script_execute,
    MAYA_OT_script_editor,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
