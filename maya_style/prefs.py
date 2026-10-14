import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty


def get_prefs(context=None):
    context = context or bpy.context
    addon = context.preferences.addons.get(__package__)
    return addon.preferences if addon else None


def _update_shelf(self, context):
    from . import shelf
    shelf.refresh_location()


def _redraw(self, context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


def _update_keymaps(self, context):
    from . import keymaps
    keymaps.unregister_keymaps()
    keymaps.register_keymaps()


def apply_pie_radius(prefs=None):
    """Spread the marking menu items further from the cursor (Blender's pie radius setting).
    Blender's own value is remembered and put back when the add-on is turned off."""
    prefs = prefs or get_prefs()
    view = bpy.context.preferences.view
    if prefs is None:
        return
    if prefs.original_pie_radius < 0:
        prefs.original_pie_radius = view.pie_menu_radius
        prefs.original_pie_threshold = view.pie_menu_threshold
    view.pie_menu_radius = prefs.marking_menu_radius
    view.pie_menu_threshold = max(view.pie_menu_threshold, prefs.marking_menu_radius // 8)


def restore_pie_radius():
    prefs = get_prefs()
    if prefs is None or prefs.original_pie_radius < 0:
        return
    view = bpy.context.preferences.view
    view.pie_menu_radius = prefs.original_pie_radius
    view.pie_menu_threshold = prefs.original_pie_threshold
    prefs.original_pie_radius = -1


def _update_pie_radius(self, context):
    apply_pie_radius(self)


def _update_selection_wire(self, context):
    from . import maya_scene
    maya_scene.update_selection_wire(force=True)


class MAYA_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    auto_apply_keymap: BoolProperty(
        name="Apply Maya keymap on install",
        description="Switch the keymap to Industry Compatible (Maya-like) the first time the add-on is enabled",
        default=True,
    )
    keymap_applied: BoolProperty(
        name="Keymap already applied",
        description="Internal flag: the keymap was switched once already",
        default=False,
    )
    auto_setup_ui: BoolProperty(
        name="Create Maya workspace on install",
        description="The first time the add-on is enabled, create the Maya workspace and Maya colors",
        default=True,
    )
    ui_applied: BoolProperty(
        name="Maya workspace already created",
        description="Internal flag: the Maya workspace was created once already",
        default=False,
    )
    workspace_in_every_file: BoolProperty(
        name="Maya workspace in every file",
        description="Add the Maya workspace to new files and files that don't have it yet "
                    "(workspaces are saved inside each .blend file)",
        default=True,
    )
    use_command_line: BoolProperty(
        name="Command Line",
        description="Add a Python command line under the time slider when the Maya workspace is created "
                    "(like Maya's MEL / Python command line)",
        default=True,
    )
    use_maya_topbar: BoolProperty(
        name="Maya Top Bar",
        description="Maya menu bar (Create, Select, Modify... with menu sets) and status line in the top bar",
        default=True,
        update=_redraw,
    )
    channel_box_in_properties: BoolProperty(
        name="Channel Box in Properties",
        description="Show the Channel Box at the top of the Properties editor's Object tab",
        default=True,
        update=_redraw,
    )
    shelf_style: EnumProperty(
        name="Shelf Style",
        items=(
            ('TABS', "Tabs", "Maya-style shelf tabs (switches to a dropdown by itself when the viewport is too narrow)"),
            ('DROPDOWN', "Dropdown", "Compact dropdown to pick the shelf"),
        ),
        default='TABS',
        update=_redraw,
    )
    shelf_location: EnumProperty(
        name="Shelf Location",
        items=(
            ('TOOL_HEADER', "Tool Header", "Show the shelf in the 3D viewport tool settings bar"),
            ('HEADER', "Header", "Show the shelf in the 3D viewport header"),
            ('NONE', "Hidden", "Do not show the shelf"),
        ),
        default='TOOL_HEADER',
        update=_update_shelf,
    )
    shelf_show_labels: BoolProperty(
        name="Show Button Labels",
        description="Show text next to the shelf icons",
        default=False,
    )
    use_rmb_menu: BoolProperty(
        name="Right-click Menu (hold on object)",
        description="Hold Right-click on an object for Maya's Vertex / Edge / Face / Object Mode menu",
        default=True,
        update=_update_keymaps,
    )
    use_marking_menu: BoolProperty(
        name="Marking Menu (Shift+Right-click)",
        description="Open Maya-style marking menus with Shift+Right-click in the 3D viewport",
        default=True,
        update=_update_keymaps,
    )
    use_tool_menu: BoolProperty(
        name="Tool Settings Menu (Ctrl+Shift+Right-click)",
        description="Maya's tool settings marking menu: orientation, snapping, symmetry...",
        default=True,
        update=_update_keymaps,
    )
    shift_extrude: BoolProperty(
        name="Shift Extrude",
        description="Shift + drag a manipulator handle in component mode extrudes before moving (like Maya)",
        default=True,
    )
    shift_duplicate: BoolProperty(
        name="Shift Duplicate",
        description="Shift + drag a manipulator handle in object mode duplicates before moving (like Maya)",
        default=True,
    )
    use_mmb_transform: BoolProperty(
        name="Middle-drag Along Picked Axis",
        description="With the Move / Rotate / Scale tool, click a gizmo axis, then middle-drag anywhere "
                    "to transform along that axis only (like Maya)",
        default=True,
        update=_update_keymaps,
    )
    show_axis_highlight: BoolProperty(
        name="Highlight Picked Axis",
        description="Draw the picked manipulator handle in yellow, like Maya",
        default=True,
        update=_redraw,
    )
    use_select_through: BoolProperty(
        name="Select Through (no X-ray needed)",
        description="Box / lasso selection also selects hidden objects and the back vertices / edges / faces, "
                    "like Maya, while the viewport stays solid",
        default=True,
    )
    use_maya_hotkeys: BoolProperty(
        name="Maya Hotkeys",
        description="Space quad view, 4~7 shading, F8~F11 components, 1~3 smooth preview, "
                    "X/V/C hold to snap, Shift+H show, Alt+H isolate, Ctrl+Y redo...",
        default=True,
        update=_update_keymaps,
    )

    use_scene_defaults: BoolProperty(
        name="Maya Scene Defaults for New Files",
        description="New files start like Maya: lengths in centimeters, frames 1-120 at 24 fps, "
                    "35 mm camera and viewport",
        default=True,
    )
    use_selection_wire: BoolProperty(
        name="Wireframe on Selected Objects",
        description="Draw the wireframe of the selected objects on top of the shading "
                    "(green lead selection, white others), like Maya",
        default=True,
        update=_update_selection_wire,
    )
    use_option_boxes: BoolProperty(
        name="Option Boxes in Menus",
        description="Maya's option box next to menu items: runs the command and opens its settings",
        default=True,
        update=_redraw,
    )
    use_panel_menus: BoolProperty(
        name="Panel Menus in Viewports",
        description="View / Shading / Lighting / Show / Renderer / Panels menus in each viewport header "
                    "(Blender's own menus move to the Blender menu)",
        default=True,
        update=_redraw,
    )
    use_input_line: BoolProperty(
        name="Input Line",
        description="Select by name / rename / absolute / relative transform field in the status line",
        default=True,
        update=_redraw,
    )
    use_anim_tools: BoolProperty(
        name="Maya Animation Editing",
        description="Tangent buttons in the Graph Editor, time slider right-click menu, Shift+drag range "
                    "selection on the time slider, middle-drag to move keys",
        default=True,
        update=_update_keymaps,
    )

    marking_menu_radius: IntProperty(
        name="Marking Menu Size",
        description="How far the marking menu items sit from the cursor (Blender's pie radius; "
                    "Blender's default is 100)",
        default=170, min=80, max=400, subtype='PIXEL',
        update=_update_pie_radius,
    )
    original_pie_radius: IntProperty(
        name="Blender Pie Radius",
        description="Internal: Blender's own pie radius, put back when the add-on is turned off",
        default=-1,
    )
    original_pie_threshold: IntProperty(
        name="Blender Pie Threshold",
        description="Internal: Blender's own pie threshold, put back when the add-on is turned off",
        default=12,
    )
    use_uv_keys: BoolProperty(
        name="Maya UV Editor Keys",
        description="In the UV Editor: Right-click UV / Edge / Face / Shell menu, Shift+Right-click UV tools, "
                    "Ctrl+Right-click convert, middle-drag transform, hold X / V to snap",
        default=True,
        update=_update_keymaps,
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Keymap", icon='KEYINGSET')
        row = box.row(align=True)
        row.operator("maya.apply_keymap", icon='CHECKMARK')
        row.operator("maya.restore_keymap", icon='LOOP_BACK')
        box.label(text="Current: " + context.preferences.keymap.active_keyconfig)
        box.prop(self, "auto_apply_keymap")

        box = layout.box()
        box.label(text="Interface", icon='WORKSPACE')
        box.prop(self, "use_maya_topbar")
        box.prop(self, "channel_box_in_properties")
        row = box.row(align=True)
        row.operator("maya.setup_maya_ui", icon='WORKSPACE')
        row = box.row(align=True)
        row.operator("maya.apply_theme", icon='COLOR')
        row.operator("maya.reset_theme", icon='LOOP_BACK')
        box.prop(self, "auto_setup_ui")
        box.prop(self, "workspace_in_every_file")
        box.prop(self, "use_command_line")
        box.prop(self, "use_input_line")
        box.prop(self, "use_panel_menus")
        box.prop(self, "use_option_boxes")
        box.prop(self, "use_selection_wire")
        row = box.row(align=True)
        row.prop(self, "use_scene_defaults")
        row.operator("maya.scene_defaults", text="Apply to This Scene", icon='SCENE_DATA')
        box.prop(self, "use_anim_tools")

        box = layout.box()
        box.label(text="Shelf", icon='TOOL_SETTINGS')
        box.prop(self, "shelf_location", expand=True)
        box.prop(self, "shelf_style", expand=True)
        box.prop(self, "shelf_show_labels")
        box.operator("maya.setup_viewport", icon='VIEW3D')

        box = layout.box()
        box.label(text="Hotkeys", icon='EVENT_SHIFT')
        box.prop(self, "use_rmb_menu")
        box.prop(self, "marking_menu_radius")
        box.prop(self, "use_marking_menu")
        box.prop(self, "use_tool_menu")
        box.prop(self, "use_mmb_transform")
        box.prop(self, "show_axis_highlight")
        box.prop(self, "use_select_through")
        row = box.row()
        row.prop(self, "shift_extrude")
        row.prop(self, "shift_duplicate")
        box.prop(self, "use_maya_hotkeys")
        box.prop(self, "use_uv_keys")


def _apply_later():
    try:
        apply_pie_radius()
    except (AttributeError, RuntimeError):
        pass
    return None


def register():
    bpy.utils.register_class(MAYA_AP_preferences)
    bpy.app.timers.register(_apply_later, first_interval=0.3)


def unregister():
    if bpy.app.timers.is_registered(_apply_later):
        bpy.app.timers.unregister(_apply_later)
    try:
        restore_pie_radius()
    except (AttributeError, RuntimeError):
        pass
    bpy.utils.unregister_class(MAYA_AP_preferences)
