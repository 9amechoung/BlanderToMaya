"""Maya-style shelf bar drawn at the top of the 3D viewport.

Pick a shelf from the dropdown (Poly Modeling, Edit Poly, Curves, UV, Rigging,
Animation, Rendering, Custom) and the row of icon buttons next to it changes.

The Custom shelf is your own: right-click any button or menu item > "Add to Shelf",
add a Python command with the + button, or add the script open in the Text Editor
(Text > Add Script to Shelf). It is saved in Blender's config folder, so it is the
same in every file.
"""

import json
import os

import bpy
from bpy.props import EnumProperty, IntProperty, StringProperty

from .operators import set_props
from .prefs import get_prefs

SEP = None

# Each button: (operator idname, icon, label, operator properties)
SHELVES = {
    'POLY': (
        "Poly Modeling", 'MESH_CUBE', (
            ("mesh.primitive_cube_add", 'MESH_CUBE', "Cube", {}),
            ("mesh.primitive_uv_sphere_add", 'MESH_UVSPHERE', "Sphere", {}),
            ("mesh.primitive_cylinder_add", 'MESH_CYLINDER', "Cylinder", {}),
            ("mesh.primitive_cone_add", 'MESH_CONE', "Cone", {}),
            ("mesh.primitive_plane_add", 'MESH_PLANE', "Plane", {}),
            ("mesh.primitive_torus_add", 'MESH_TORUS', "Torus", {}),
            ("mesh.primitive_monkey_add", 'MESH_MONKEY', "Monkey", {}),
            SEP,
            ("object.join", 'SELECT_EXTEND', "Combine", {}),
            ("mesh.separate", 'SELECT_SUBTRACT', "Separate", {"type": 'LOOSE'}),
            ("maya.add_modifier", 'MOD_SUBSURF', "Smooth", {"modifier": 'SUBSURF'}),
            ("maya.add_modifier", 'MOD_MIRROR', "Mirror", {"modifier": 'MIRROR'}),
            ("maya.add_modifier", 'MOD_BOOLEAN', "Boolean", {"modifier": 'BOOLEAN'}),
            ("maya.add_modifier", 'MOD_SOLIDIFY', "Solidify", {"modifier": 'SOLIDIFY'}),
            SEP,
            ("maya.center_pivot", 'PIVOT_BOUNDBOX', "Center Pivot", {}),
            ("maya.freeze_transforms", 'FREEZE', "Freeze", {}),
            ("maya.delete_history", 'TRASH', "Delete History", {}),
            ("object.shade_smooth", 'SHADING_RENDERED', "Smooth Shade", {}),
            ("object.shade_flat", 'SHADING_SOLID', "Flat Shade", {}),
        ),
    ),
    'EDIT': (
        "Edit Poly", 'EDITMODE_HLT', (
            ("maya.component_mode", 'VERTEXSEL', "Vertex", {"mode": 'VERT'}),
            ("maya.component_mode", 'EDGESEL', "Edge", {"mode": 'EDGE'}),
            ("maya.component_mode", 'FACESEL', "Face", {"mode": 'FACE'}),
            SEP,
            ("view3d.edit_mesh_extrude_move_normal", 'FACESEL', "Extrude", {}),
            ("mesh.bevel", 'MOD_BEVEL', "Bevel", {}),
            ("mesh.inset", 'FULLSCREEN_EXIT', "Inset", {}),
            ("mesh.loopcut_slide", 'MOD_MULTIRES', "Insert Edge Loop", {}),
            ("mesh.knife_tool", 'SCULPTMODE_HLT', "Multi-Cut", {}),
            ("mesh.bridge_edge_loops", 'MOD_LATTICE', "Bridge", {}),
            ("mesh.fill", 'SNAP_FACE', "Fill Hole", {}),
            SEP,
            ("mesh.merge", 'AUTOMERGE_ON', "Merge", {"type": 'CENTER'}),
            ("maya.target_weld", 'PIVOT_ACTIVE', "Target Weld", {}),
            ("transform.edge_slide", 'ARROW_LEFTRIGHT', "Edge Slide", {}),
            ("mesh.subdivide", 'MESH_GRID', "Subdivide", {}),
            ("mesh.dissolve_mode", 'X', "Dissolve", {}),
            ("mesh.quads_convert_to_tris", 'MOD_TRIANGULATE', "Triangulate", {}),
            ("mesh.flip_normals", 'NORMALS_FACE', "Reverse Normals", {}),
        ),
    ),
    'CURVES': (
        "Curves", 'CURVE_DATA', (
            ("curve.primitive_bezier_curve_add", 'CURVE_BEZCURVE', "Bezier Curve", {}),
            ("curve.primitive_nurbs_curve_add", 'CURVE_NCURVE', "NURBS Curve", {}),
            ("curve.primitive_bezier_circle_add", 'CURVE_BEZCIRCLE', "Circle", {}),
            ("curve.primitive_nurbs_path_add", 'CURVE_PATH', "Path", {}),
            ("object.text_add", 'OUTLINER_OB_FONT', "Text", {}),
            SEP,
            ("surface.primitive_nurbs_surface_surface_add", 'SURFACE_NSURFACE', "NURBS Surface", {}),
            ("surface.primitive_nurbs_surface_sphere_add", 'SURFACE_NSPHERE', "NURBS Sphere", {}),
            ("surface.primitive_nurbs_surface_cylinder_add", 'SURFACE_NCYLINDER', "NURBS Cylinder", {}),
            SEP,
            ("object.convert", 'OUTLINER_OB_MESH', "Convert to Mesh", {"target": 'MESH'}),
        ),
    ),
    'UV': (
        "UV", 'UV', (
            ("uv.unwrap", 'UV', "Unfold (Unwrap)", {}),
            ("uv.smart_project", 'UV_DATA', "Automatic (Smart UV)", {}),
            ("uv.cube_project", 'MESH_CUBE', "Cube Projection", {}),
            ("uv.cylinder_project", 'MESH_CYLINDER', "Cylindrical Projection", {}),
            ("uv.sphere_project", 'MESH_UVSPHERE', "Spherical Projection", {}),
            ("uv.project_from_view", 'VIEW_CAMERA', "Planar (From View)", {}),
            SEP,
            ("mesh.mark_seam", 'EDGESEL', "Cut UV Edges", {"clear": False}),
            ("mesh.mark_seam", 'X', "Sew (Clear Seam)", {"clear": True}),
        ),
    ),
    'RIGGING': (
        "Rigging", 'ARMATURE_DATA', (
            ("object.armature_add", 'BONE_DATA', "Create Joint", {}),
            ("object.empty_add", 'EMPTY_AXIS', "Locator", {"type": 'PLAIN_AXES'}),
            ("object.empty_add", 'MESH_CIRCLE', "Circle Control", {"type": 'CIRCLE'}),
            SEP,
            ("object.parent_set", 'LINKED', "Parent", {"type": 'OBJECT'}),
            ("object.parent_clear", 'UNLINKED', "Unparent", {"type": 'CLEAR_KEEP_TRANSFORM'}),
            ("object.parent_set", 'MOD_ARMATURE', "Bind Skin", {"type": 'ARMATURE_AUTO'}),
            SEP,
            ("pose.ik_add", 'CON_KINEMATIC', "IK Handle", {}),
            ("object.constraint_add", 'CON_LOCLIKE', "Point Constraint", {"type": 'COPY_LOCATION'}),
            ("object.constraint_add", 'CON_ROTLIKE', "Orient Constraint", {"type": 'COPY_ROTATION'}),
            ("object.constraint_add", 'CON_CHILDOF', "Parent Constraint", {"type": 'CHILD_OF'}),
            ("object.constraint_add", 'CON_TRACKTO', "Aim Constraint", {"type": 'DAMPED_TRACK'}),
            SEP,
            ("object.mode_set", 'POSE_HLT', "Pose Mode", {"mode": 'POSE'}),
            ("object.mode_set", 'WPAINT_HLT', "Paint Skin Weights", {"mode": 'WEIGHT_PAINT'}),
            ("object.mode_set", 'OBJECT_DATAMODE', "Object Mode", {"mode": 'OBJECT'}),
        ),
    ),
    'ANIMATION': (
        "Animation", 'ANIM', (
            ("anim.keyframe_insert", 'KEY_HLT', "Set Key", {}),
            ("anim.keyframe_delete_v3d", 'KEY_DEHLT', "Delete Key", {}),
            SEP,
            ("screen.frame_jump", 'REW', "Go to Start", {"end": False}),
            ("screen.keyframe_jump", 'PREV_KEYFRAME', "Previous Key", {"next": False}),
            ("screen.animation_play", 'PLAY', "Play", {}),
            ("screen.keyframe_jump", 'NEXT_KEYFRAME', "Next Key", {"next": True}),
            ("screen.frame_jump", 'FF', "Go to End", {"end": True}),
            SEP,
            ("object.paths_calculate", 'IPO_BEZIER', "Motion Trail", {}),
            ("nla.bake", 'ACTION', "Bake Animation", {}),
        ),
    ),
    'RENDERING': (
        "Rendering", 'RESTRICT_RENDER_OFF', (
            ("object.camera_add", 'OUTLINER_OB_CAMERA', "Camera", {}),
            ("object.light_add", 'LIGHT_POINT', "Point Light", {"type": 'POINT'}),
            ("object.light_add", 'LIGHT_SUN', "Directional Light", {"type": 'SUN'}),
            ("object.light_add", 'LIGHT_SPOT', "Spot Light", {"type": 'SPOT'}),
            ("object.light_add", 'LIGHT_AREA', "Area Light", {"type": 'AREA'}),
            SEP,
            ("maya.set_shading", 'SHADING_WIRE', "Wireframe (4)", {"shading": 'WIREFRAME'}),
            ("maya.set_shading", 'SHADING_SOLID', "Shaded (5)", {"shading": 'SOLID'}),
            ("maya.set_shading", 'SHADING_TEXTURE', "Textured (6)", {"shading": 'MATERIAL'}),
            ("maya.set_shading", 'SHADING_RENDERED', "Rendered (7)", {"shading": 'RENDERED'}),
            SEP,
            ("render.render", 'RENDER_STILL', "Render Frame", {"use_viewport": True}),
            ("render.render", 'RENDER_ANIMATION', "Render Sequence", {"animation": True, "use_viewport": True}),
        ),
    ),
    'CUSTOM': ("Custom", 'SOLO_ON', ()),
}

SHELF_ITEMS = tuple(
    (key, name, "Load the %s shelf" % name, icon, i)
    for i, (key, (name, icon, _buttons)) in enumerate(SHELVES.items())
)


# ---------------------------------------------------------------------------
# Custom shelf (saved as JSON in Blender's config folder)
# ---------------------------------------------------------------------------

def _custom_path():
    return os.path.join(bpy.utils.user_resource('CONFIG'), "maya_style_shelf.json")


_custom_cache = None


def load_custom():
    global _custom_cache
    if _custom_cache is None:
        try:
            with open(_custom_path(), encoding="utf-8") as f:
                data = json.load(f)
            _custom_cache = [item for item in data if isinstance(item, dict)]
        except (OSError, ValueError):
            _custom_cache = []
    return _custom_cache


def save_custom(items):
    global _custom_cache
    _custom_cache = items
    path = _custom_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def _idname_from_rna(identifier):
    """'MESH_OT_primitive_cube_add' -> 'mesh.primitive_cube_add'"""
    if "_OT_" not in identifier:
        return None
    module, name = identifier.split("_OT_", 1)
    return module.lower() + "." + name


def _simple(value):
    if isinstance(value, (bool, int, float, str)):
        return value
    try:
        items = list(value)
    except TypeError:
        return None
    if all(isinstance(v, (bool, int, float)) for v in items):
        return items
    if all(isinstance(v, str) for v in items):  # enum flags
        return items
    return None


def operator_button_info(op_props):
    """(idname, props, label) of an operator button, unwrapping the menu bar's call_in_view3d."""
    idname = _idname_from_rna(op_props.bl_rna.identifier)
    if idname is None:
        return None
    if idname == "maya.call_in_view3d":
        import ast
        try:
            props = ast.literal_eval(op_props.props) if op_props.props else {}
        except (ValueError, SyntaxError):
            props = {}
        idname = op_props.idname
    else:
        props = {}
        for prop in op_props.bl_rna.properties:
            name = prop.identifier
            if name == "rna_type" or not op_props.is_property_set(name):
                continue
            value = _simple(getattr(op_props, name))
            if value is not None:
                props[name] = value
    label = idname
    try:
        mod, name = idname.split(".")
        label = getattr(getattr(bpy.ops, mod), name).get_rna_type().name or idname
    except Exception:
        pass
    return idname, props, label


class MAYA_OT_shelf_run(bpy.types.Operator):
    """Run this custom shelf button"""
    bl_idname = "maya.shelf_run"
    bl_label = "Shelf Button"

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        items = load_custom()
        if 0 <= properties.index < len(items):
            item = items[properties.index]
            return item.get("label", "") + ("\n" + item["script"][:200] if item.get("script") else
                                              "\n" + item.get("idname", ""))
        return ""

    def invoke(self, context, event):
        items = load_custom()
        if not 0 <= self.index < len(items):
            return {'CANCELLED'}
        item = items[self.index]
        try:
            if item.get("script"):
                from .script_editor import run_python
                ok = run_python(item["script"], self.report)
                return {'FINISHED'} if ok else {'CANCELLED'}
            mod, name = item["idname"].split(".")
            fn = getattr(getattr(bpy.ops, mod), name)
            known = set(fn.get_rna_type().properties.keys())
            props = {k: v for k, v in item.get("props", {}).items() if k in known}
            fn('INVOKE_DEFAULT', **props)
        except Exception as ex:
            self.report({'ERROR'}, str(ex).replace("Error: ", "").strip())
            return {'CANCELLED'}
        return {'FINISHED'}


class MAYA_OT_shelf_add(bpy.types.Operator):
    """Add this command to the Custom shelf (Maya: Ctrl+Shift+click a menu item)"""
    bl_idname = "maya.shelf_add"
    bl_label = "Add to Shelf"

    label: StringProperty(name="Label")
    idname: StringProperty(options={'HIDDEN'})
    props: StringProperty(default="{}", options={'HIDDEN'})
    script: StringProperty(name="Python", options={'HIDDEN'})

    def execute(self, context):
        import ast
        item = {"label": self.label or self.idname or "Script", "icon": 'NONE'}
        if self.script:
            item["script"] = self.script
        elif self.idname:
            item["idname"] = self.idname
            try:
                item["props"] = ast.literal_eval(self.props) if self.props else {}
            except (ValueError, SyntaxError):
                item["props"] = {}
        else:
            return {'CANCELLED'}
        save_custom(load_custom() + [item])
        context.window_manager.maya_shelf = 'CUSTOM'
        self.report({'INFO'}, "Added to the Custom shelf: " + item["label"])
        return {'FINISHED'}


class MAYA_OT_shelf_add_command(bpy.types.Operator):
    """Add a Python command button to the Custom shelf"""
    bl_idname = "maya.shelf_add_command"
    bl_label = "New Shelf Button"

    label: StringProperty(name="Label", default="Script")
    command: StringProperty(name="Python", default="bpy.ops.mesh.primitive_cube_add()")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=420)

    def execute(self, context):
        if not self.command.strip():
            return {'CANCELLED'}
        return bpy.ops.maya.shelf_add(label=self.label, script=self.command)


class MAYA_OT_shelf_add_script(bpy.types.Operator):
    """Add the script open in the Text Editor to the Custom shelf
    (Maya: middle-drag a script to the shelf)"""
    bl_idname = "maya.shelf_add_script"
    bl_label = "Add Script to Shelf"

    @classmethod
    def poll(cls, context):
        return getattr(context.space_data, "text", None) is not None

    def execute(self, context):
        text = context.space_data.text
        label = os.path.splitext(text.name)[0]
        return bpy.ops.maya.shelf_add(label=label, script=text.as_string())


class MAYA_OT_shelf_remove(bpy.types.Operator):
    """Remove this button from the Custom shelf"""
    bl_idname = "maya.shelf_remove"
    bl_label = "Remove from Shelf"

    index: IntProperty()

    def execute(self, context):
        items = list(load_custom())
        if 0 <= self.index < len(items):
            del items[self.index]
            save_custom(items)
        return {'FINISHED'}


class MAYA_OT_shelf_move(bpy.types.Operator):
    """Move this button left / right on the Custom shelf"""
    bl_idname = "maya.shelf_move"
    bl_label = "Move Shelf Button"

    index: IntProperty()
    offset: IntProperty(default=1)

    def execute(self, context):
        items = list(load_custom())
        new = self.index + self.offset
        if 0 <= self.index < len(items) and 0 <= new < len(items):
            items.insert(new, items.pop(self.index))
            save_custom(items)
        return {'FINISHED'}


def _draw_button_context(self, context):
    op_props = getattr(context, "button_operator", None)
    if op_props is None:
        return
    layout = self.layout
    identifier = op_props.bl_rna.identifier
    if identifier == "MAYA_OT_shelf_run":
        layout.separator()
        layout.operator("maya.shelf_remove", icon='X').index = op_props.index
        o = layout.operator("maya.shelf_move", text="Move Left", icon='TRIA_LEFT')
        o.index, o.offset = op_props.index, -1
        o = layout.operator("maya.shelf_move", text="Move Right", icon='TRIA_RIGHT')
        o.index, o.offset = op_props.index, 1
        return
    info = operator_button_info(op_props)
    if info is None or info[0].startswith("maya.shelf_"):
        return
    idname, props, label = info
    layout.separator()
    o = layout.operator("maya.shelf_add", text="Add to Shelf (Custom)", icon='SOLO_ON')
    o.idname = idname
    o.props = repr(props)
    o.label = label


def _draw_text_menu(self, context):
    self.layout.separator()
    self.layout.operator("maya.shelf_add_script", icon='SOLO_ON')


def _custom_buttons(row, show_labels):
    buttons = row.row(align=True)
    for i, item in enumerate(load_custom()):
        icon = item.get("icon", 'NONE')
        try:
            buttons.operator("maya.shelf_run", text=item.get("label", "?"), icon=icon).index = i
        except TypeError:
            buttons.operator("maya.shelf_run", text=item.get("label", "?")).index = i
    row.operator("maya.shelf_add_command", text="", icon='ADD')


def _text_width(text):
    try:
        import blf
        ui = bpy.context.preferences.view.ui_scale
        blf.size(0, 11 * ui)
        return blf.dimensions(0, text)[0]
    except Exception:
        return len(text) * 7 * bpy.context.preferences.view.ui_scale


def _fits(context, wm, show_labels, reserve_units):
    """Estimate whether the shelf with tabs still leaves room for the rest of the header."""
    region = context.region
    if region is None:
        return True
    unit = 20 * context.preferences.view.ui_scale
    tabs = sum(_text_width(name) + unit * 1.6 for name, _icon, _b in SHELVES.values())
    buttons = 0
    if wm.maya_shelf == 'CUSTOM':
        buttons = sum(_text_width(item.get("label", "")) + unit for item in load_custom()) + unit
    for item in SHELVES[wm.maya_shelf][2]:
        if item is SEP:
            buttons += unit * 0.3
        else:
            buttons += unit + (_text_width(item[2]) + unit * 0.5 if show_labels else 0)
    return tabs + buttons + reserve_units * unit <= region.width


def draw_shelf(layout, context, reserve_units=28):
    prefs = get_prefs(context)
    show_labels = prefs.shelf_show_labels if prefs else False
    wm = context.window_manager

    row = layout.row(align=False)
    # Tabs when there is room; a dropdown when the viewport is too narrow, so the tool settings
    # (orientation, symmetry...) on the right are not pushed out of the header.
    use_tabs = prefs is None or prefs.shelf_style == 'TABS'
    if use_tabs and not _fits(context, wm, show_labels, reserve_units):
        use_tabs = False
    if use_tabs:
        tabs = row.row(align=True)
        tabs.prop(wm, "maya_shelf", expand=True)
    else:
        row.label(text="", icon='COLLAPSEMENU')
        sub = row.row()
        sub.ui_units_x = 6
        sub.prop(wm, "maya_shelf", text="")

    if wm.maya_shelf == 'CUSTOM':
        _custom_buttons(row, show_labels)
    buttons = row.row(align=True)
    for item in SHELVES[wm.maya_shelf][2]:
        if item is SEP:
            buttons.separator()
            continue
        idname, icon, label, props = item
        op = buttons.operator(idname, text=label if show_labels else "", icon=icon)
        set_props(op, props)

    # Which axis a middle-drag will use (Maya highlights the picked handle in yellow).
    from .transform_tools import active_tool_kind, last_axis_settings, axis_label
    kind = active_tool_kind(context)
    if kind is not None:
        row.separator()
        row.label(text=axis_label(last_axis_settings(context, kind), kind), icon='MOUSE_MMB_DRAG')


def _draw_tool_header(self, context):
    prefs = get_prefs(context)
    if prefs and prefs.shelf_location == 'TOOL_HEADER':
        draw_shelf(self.layout, context)
        self.layout.separator()


def _draw_header(self, context):
    prefs = get_prefs(context)
    if prefs and prefs.shelf_location == 'HEADER':
        draw_shelf(self.layout, context, reserve_units=60)
    # Maya's "Wireframe on Shaded" button, next to the shading buttons
    space = context.space_data
    if space is not None and space.type == 'VIEW_3D':
        self.layout.operator("maya.wireframe_on_shaded", text="", icon='MOD_WIREFRAME',
                             depress=space.overlay.show_wireframes and space.overlay.show_overlays)


def refresh_location():
    """Redraw all viewports after the shelf location preference changed."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


classes = (
    MAYA_OT_shelf_run,
    MAYA_OT_shelf_add,
    MAYA_OT_shelf_add_command,
    MAYA_OT_shelf_add_script,
    MAYA_OT_shelf_remove,
    MAYA_OT_shelf_move,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.UI_MT_button_context_menu.append(_draw_button_context)
    bpy.types.TEXT_MT_text.append(_draw_text_menu)
    bpy.types.WindowManager.maya_shelf = EnumProperty(
        name="Shelf",
        description="Load Shelf",
        items=SHELF_ITEMS,
        default='POLY',
    )
    bpy.types.VIEW3D_HT_tool_header.prepend(_draw_tool_header)
    bpy.types.VIEW3D_HT_header.append(_draw_header)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(_draw_header)
    bpy.types.VIEW3D_HT_tool_header.remove(_draw_tool_header)
    del bpy.types.WindowManager.maya_shelf
    bpy.types.TEXT_MT_text.remove(_draw_text_menu)
    bpy.types.UI_MT_button_context_menu.remove(_draw_button_context)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
