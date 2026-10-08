import bpy
from bpy.props import BoolProperty, EnumProperty


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
            ('TABS', "Tabs", "Maya-style shelf tabs"),
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
        description="Shift + middle-drag in component mode extrudes before moving (like Maya)",
        default=True,
    )
    shift_duplicate: BoolProperty(
        name="Shift Duplicate",
        description="Shift + middle-drag in object mode duplicates before moving (like Maya)",
        default=True,
    )
    use_mmb_transform: BoolProperty(
        name="Middle-drag Along Picked Axis",
        description="With the Move / Rotate / Scale tool, click a gizmo axis, then middle-drag anywhere "
                    "to transform along that axis only (like Maya)",
        default=True,
        update=_update_keymaps,
    )
    use_maya_hotkeys: BoolProperty(
        name="Maya Hotkeys",
        description="Space quad view, 4~7 shading, F8~F11 components, 1~3 smooth preview, "
                    "X/V/C hold to snap, Shift+H show, Alt+H isolate, Ctrl+Y redo...",
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

        box = layout.box()
        box.label(text="Shelf", icon='TOOL_SETTINGS')
        box.prop(self, "shelf_location", expand=True)
        box.prop(self, "shelf_style", expand=True)
        box.prop(self, "shelf_show_labels")
        box.operator("maya.setup_viewport", icon='VIEW3D')

        box = layout.box()
        box.label(text="Hotkeys", icon='EVENT_SHIFT')
        box.prop(self, "use_rmb_menu")
        box.prop(self, "use_marking_menu")
        box.prop(self, "use_tool_menu")
        box.prop(self, "use_mmb_transform")
        row = box.row()
        row.prop(self, "shift_extrude")
        row.prop(self, "shift_duplicate")
        box.prop(self, "use_maya_hotkeys")


def register():
    bpy.utils.register_class(MAYA_AP_preferences)


def unregister():
    bpy.utils.unregister_class(MAYA_AP_preferences)
