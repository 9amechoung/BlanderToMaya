"""Maya-like screen: top bar (menu bar + status line), workspace layout and theme.

Top bar:   [File Edit Create Select Modify Display Windows | menu set menus ...]
           [Modeling v | new open save | undo redo | select modes | snaps | symmetry | render]
           ......................................................  Workspace: [Maya v]
Workspace: Outliner (left) | 3D viewport with toolbox | Properties with
           Channel Box on top (right), timeline across the bottom.
"""

import bpy
from bpy.app.handlers import persistent

from .prefs import get_prefs
from . import maya_menus

WORKSPACE_NAME = "Maya"

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------

_original_draw_left = None
_original_draw_right = None


def _sep(layout):
    """Vertical divider line (Blender 4.2+), plain gap on older versions."""
    try:
        layout.separator(type='LINE')
    except TypeError:
        layout.separator()


def _use_maya_topbar(context):
    prefs = get_prefs(context)
    return prefs is not None and prefs.use_maya_topbar


def _draw_status_line(layout, context):
    wm = context.window_manager
    ts = context.scene.tool_settings
    obj = context.active_object

    sub = layout.row()
    sub.ui_units_x = 5.5
    sub.prop(wm, "maya_menu_set", text="")

    _sep(layout)
    row = layout.row(align=True)
    row.operator("wm.read_homefile", text="", icon='FILE_NEW')
    row.operator("maya.open_scene", text="", icon='FILE_FOLDER')
    row.operator("maya.save_scene", text="", icon='FILE_TICK')
    row = layout.row(align=True)
    row.operator("ed.undo", text="", icon='LOOP_BACK')
    row.operator("ed.redo", text="", icon='LOOP_FORWARDS')

    # Selection mode: object / vertex / edge / face
    _sep(layout)
    row = layout.row(align=True)
    in_edit = context.mode == 'EDIT_MESH'
    select_mode = tuple(ts.mesh_select_mode) if in_edit else (False, False, False)
    for mode, icon, depress in (
        ('OBJECT', 'OBJECT_DATAMODE', not in_edit),
        ('VERT', 'VERTEXSEL', in_edit and select_mode[0]),
        ('EDGE', 'EDGESEL', in_edit and select_mode[1]),
        ('FACE', 'FACESEL', in_edit and select_mode[2]),
    ):
        o = row.operator("maya.component_mode", text="", icon=icon, depress=depress)
        o.mode = mode

    # Snapping: grid / curve (edge) / point (vertex) / surface (face)
    _sep(layout)
    row = layout.row(align=True)
    elements = ts.snap_elements if ts.use_snap else set()
    for element, icon in (('GRID', 'SNAP_GRID'), ('EDGE', 'SNAP_EDGE'), ('VERTEX', 'SNAP_VERTEX'), ('FACE', 'SNAP_FACE')):
        on = element in elements or (element == 'GRID' and 'INCREMENT' in elements)
        o = row.operator("maya.toggle_snap", text="", icon=icon, depress=on)
        o.element = element

    # Symmetry
    if obj is not None and obj.type == 'MESH':
        _sep(layout)
        layout.prop(obj, "use_mesh_mirror_x", text="Symmetry X", toggle=True, icon='MOD_MIRROR')

    # Render
    _sep(layout)
    row = layout.row(align=True)
    o = row.operator("render.render", text="", icon='RENDER_STILL')
    o.use_viewport = True
    row.operator("maya.set_shading", text="", icon='SHADING_RENDERED').shading = 'RENDERED'
    row.operator("maya.show_attributes", text="", icon='PROPERTIES').tab = 'RENDER'


def _draw_left(self, context):
    if not _use_maya_topbar(context):
        return _original_draw_left(self, context)
    layout = self.layout
    screen = context.screen

    layout.menu("TOPBAR_MT_blender", text="", icon='BLENDER')
    maya_menus.draw_menu_bar(layout, context)

    _sep(layout)
    if screen.show_fullscreen:
        layout.operator("screen.back_to_previous", icon='SCREEN_BACK', text="Back to Previous")
    else:
        _draw_status_line(layout, context)


def _draw_right(self, context):
    if not _use_maya_topbar(context):
        return _original_draw_right(self, context)
    layout = self.layout
    window = context.window
    if not context.screen.show_statusbar:
        layout.template_reports_banner()
        layout.template_running_jobs()
    layout.label(text="Workspace:")
    sub = layout.row()
    sub.ui_units_x = 8
    sub.template_ID(window, "workspace", new="workspace.add")


def _install_topbar():
    global _original_draw_left, _original_draw_right
    cls = bpy.types.TOPBAR_HT_upper_bar
    if _original_draw_left is None:
        _original_draw_left = cls.draw_left
        _original_draw_right = cls.draw_right
    cls.draw_left = _draw_left
    cls.draw_right = _draw_right


def _uninstall_topbar():
    global _original_draw_left, _original_draw_right
    if _original_draw_left is not None:
        cls = bpy.types.TOPBAR_HT_upper_bar
        cls.draw_left = _original_draw_left
        cls.draw_right = _original_draw_right
        _original_draw_left = _original_draw_right = None


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

MAYA_GREY = (0.267, 0.267, 0.267)       # panels #444444
MAYA_VIEWPORT = (0.365, 0.365, 0.365)   # viewport background
MAYA_GRID = (0.22, 0.22, 0.22, 1.0)
MAYA_ACTIVE = (0.26, 1.0, 0.64)         # lead selection (green)
MAYA_SELECTED = (1.0, 1.0, 1.0)         # other selection (white)


def _set(owner, attr, value):
    """Set a theme colour if this Blender version has it."""
    if owner is None or not hasattr(owner, attr):
        return
    try:
        current = getattr(owner, attr)
        setattr(owner, attr, value[:len(current)])
    except (TypeError, AttributeError, ValueError):
        pass


def apply_theme():
    theme = bpy.context.preferences.themes[0]
    v3d = theme.view_3d
    gradients = getattr(v3d.space, "gradients", None)
    if gradients is not None:
        gradients.background_type = 'SINGLE_COLOR'
        _set(gradients, "high_gradient", MAYA_VIEWPORT)
        _set(gradients, "gradient", MAYA_VIEWPORT)
    _set(v3d, "grid", MAYA_GRID)
    _set(v3d, "object_active", MAYA_ACTIVE)
    _set(v3d, "object_selected", MAYA_SELECTED)
    _set(v3d, "wire", (0.0, 0.0, 0.0))
    for editor in ("outliner", "properties", "dopesheet_editor", "topbar", "statusbar"):
        space = getattr(getattr(theme, editor, None), "space", None)
        _set(space, "back", MAYA_GREY)
        if editor in ("topbar", "statusbar"):
            _set(space, "header", MAYA_GREY)


class MAYA_OT_apply_theme(bpy.types.Operator):
    """Maya-like viewport colours: grey background, green lead selection"""
    bl_idname = "maya.apply_theme"
    bl_label = "Apply Maya Colors"

    def execute(self, context):
        apply_theme()
        return {'FINISHED'}


class MAYA_OT_reset_theme(bpy.types.Operator):
    """Go back to Blender's default theme"""
    bl_idname = "maya.reset_theme"
    bl_label = "Reset Blender Colors"

    def execute(self, context):
        bpy.ops.preferences.reset_default_theme()
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Workspace layout
# ---------------------------------------------------------------------------

def _override(window, screen, area):
    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
    return bpy.context.temp_override(window=window, screen=screen, area=area, region=region)


def _split(window, screen, area, direction, factor):
    """Split an area and return (first, second): bottom/top or left/right.

    Blender makes the new area the smaller piece: bottom/left when factor < 0.5,
    top/right when factor > 0.5. Coordinates are only updated on the next
    redraw, so they can't be used to tell the two apart.
    """
    before = {a.as_pointer() for a in screen.areas}
    with _override(window, screen, area):
        bpy.ops.screen.area_split(direction=direction, factor=factor)
    new = next((a for a in screen.areas if a.as_pointer() not in before), None)
    if new is None:
        return None
    return (new, area) if factor < 0.5 else (area, new)


def _close_extra_areas(window, screen):
    """Join everything back into one big area (keeps the largest one)."""
    for _attempt in range(20):
        if len(screen.areas) <= 1:
            return True
        main = max(screen.areas, key=lambda a: a.width * a.height)
        progress = False
        for area in list(screen.areas):
            if area.as_pointer() == main.as_pointer():
                continue
            count = len(screen.areas)
            try:
                with _override(window, screen, area):
                    bpy.ops.screen.area_close()
            except RuntimeError:
                continue
            if len(screen.areas) < count:
                progress = True
                break
        if not progress:
            return False
    return len(screen.areas) <= 1


def build_layout(window):
    """Arrange the window's current screen like Maya. Returns True on success."""
    screen = window.screen
    if not _close_extra_areas(window, screen):
        return False
    main = screen.areas[0]
    main.type = 'VIEW_3D'

    # Timeline across the bottom
    prefs = get_prefs()
    command_line = prefs is None or prefs.use_command_line
    pair = _split(window, screen, main, 'HORIZONTAL', 0.115 if command_line else 0.08)
    if pair is None:
        return False
    timeline, main = pair
    timeline.type = 'DOPESHEET_EDITOR'
    timeline.ui_type = 'TIMELINE'

    # Command line under the time slider (Maya's MEL/Python line -> Python console)
    if command_line:
        pair = _split(window, screen, timeline, 'HORIZONTAL', 0.35)
        if pair is not None:
            console, timeline = pair
            console.type = 'CONSOLE'

    # Outliner on the left
    pair = _split(window, screen, main, 'VERTICAL', 0.14)
    if pair is None:
        return False
    outliner, main = pair
    outliner.type = 'OUTLINER'

    # Channel Box / Attribute Editor (Properties) on the right
    pair = _split(window, screen, main, 'VERTICAL', 0.80)
    if pair is None:
        return False
    main, properties = pair
    properties.type = 'PROPERTIES'
    try:
        properties.spaces.active.context = 'OBJECT'
    except TypeError:
        pass

    screen.show_statusbar = True

    # A freshly split area has no regions until the next redraw; changing its
    # region settings right away crashes Blender, so do it a moment later.
    def _configure_viewport():
        for area in screen.areas:
            space = area.spaces.active
            if area.type == 'VIEW_3D':
                space.show_region_toolbar = True
                space.show_region_tool_header = True
                space.show_region_ui = False
            elif area.type == 'DOPESHEET_EDITOR' and hasattr(space, "show_region_channels"):
                space.show_region_channels = False  # Maya's time slider has no channel list
            elif area.type == 'CONSOLE':
                space.show_region_header = False  # just the input line, like Maya's command line
        return None

    bpy.app.timers.register(_configure_viewport, first_interval=0.3)
    return True


def setup_maya_workspace(window, on_done=None):
    """Create (or reuse) the 'Maya' workspace and switch to it.

    Switching workspaces only takes effect on the next event loop, so the
    layout is built from a timer once the new screen is active.
    """
    ws = bpy.data.workspaces.get(WORKSPACE_NAME)
    if ws is None:
        before = set(bpy.data.workspaces)
        with bpy.context.temp_override(window=window):
            bpy.ops.workspace.duplicate()
        new = [w for w in bpy.data.workspaces if w not in before]
        if not new:
            return False
        ws = new[0]
        ws.name = WORKSPACE_NAME
        need_layout = True
    else:
        need_layout = False
    window.workspace = ws

    if not need_layout:
        if on_done:
            on_done(True)
        return True

    tries = [0]

    def _build():
        if window.workspace != ws or window.screen not in ws.screens[:]:
            tries[0] += 1
            return 0.1 if tries[0] < 30 else None
        try:
            ok = build_layout(window)
        except Exception as ex:  # never leave a half-finished error popup
            print("Maya Style UI: layout failed:", ex)
            ok = False
        if on_done:
            on_done(ok)
        return None

    bpy.app.timers.register(_build, first_interval=0.1)
    return True


@persistent
def _on_file_loaded(_dummy):
    """Workspaces live inside each .blend file: add the Maya one to files that don't have it
    (File > New, files from other people...)."""
    prefs = get_prefs()
    if prefs is None or not prefs.workspace_in_every_file or not prefs.ui_applied:
        return
    if WORKSPACE_NAME in bpy.data.workspaces:
        return

    def _later():
        windows = bpy.context.window_manager.windows
        if windows and WORKSPACE_NAME not in bpy.data.workspaces:
            setup_maya_workspace(windows[0])
        return None

    bpy.app.timers.register(_later, first_interval=0.2)


class MAYA_OT_setup_maya_ui(bpy.types.Operator):
    """Create the Maya workspace: Outliner left, Channel Box right, timeline bottom"""
    bl_idname = "maya.setup_maya_ui"
    bl_label = "Create Maya Workspace"

    def execute(self, context):
        old = bpy.data.workspaces.get(WORKSPACE_NAME)
        if old is not None:
            # Rebuild from scratch: rename the old one so a fresh copy is made.
            old.name = WORKSPACE_NAME + " (old)"
        if not setup_maya_workspace(context.window):
            self.report({'ERROR'}, "Could not create the Maya workspace")
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (
    MAYA_OT_apply_theme,
    MAYA_OT_reset_theme,
    MAYA_OT_setup_maya_ui,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    _install_topbar()
    bpy.app.handlers.load_post.append(_on_file_loaded)


def unregister():
    if _on_file_loaded in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_file_loaded)
    _uninstall_topbar()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
