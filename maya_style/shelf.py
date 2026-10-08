"""Maya-style shelf bar drawn at the top of the 3D viewport.

Pick a shelf from the dropdown (Poly Modeling, Edit Poly, Curves, UV, Rigging,
Animation, Rendering) and the row of icon buttons next to it changes.
"""

import bpy
from bpy.props import EnumProperty

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
            ("mesh.merge", 'PIVOT_ACTIVE', "Target Weld", {"type": 'LAST'}),
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
}

SHELF_ITEMS = tuple(
    (key, name, "Load the %s shelf" % name, icon, i)
    for i, (key, (name, icon, _buttons)) in enumerate(SHELVES.items())
)


def draw_shelf(layout, context):
    prefs = get_prefs(context)
    show_labels = prefs.shelf_show_labels if prefs else False
    wm = context.window_manager

    row = layout.row(align=False)
    row.label(text="", icon='COLLAPSEMENU')
    sub = row.row()
    sub.ui_units_x = 6
    sub.prop(wm, "maya_shelf", text="")

    buttons = row.row(align=True)
    for item in SHELVES[wm.maya_shelf][2]:
        if item is SEP:
            buttons.separator()
            continue
        idname, icon, label, props = item
        op = buttons.operator(idname, text=label if show_labels else "", icon=icon)
        for key, value in props.items():
            setattr(op, key, value)

    # Which axis a middle-drag will use (Maya highlights the picked handle in yellow).
    from .transform_tools import active_tool_kind, last_axis_settings, axis_label
    kind = active_tool_kind(context)
    if kind is not None:
        row.separator()
        row.label(text="MMB: " + axis_label(last_axis_settings(context, kind), kind), icon='MOUSE_MMB_DRAG')


def _draw_tool_header(self, context):
    prefs = get_prefs(context)
    if prefs and prefs.shelf_location == 'TOOL_HEADER':
        draw_shelf(self.layout, context)
        self.layout.separator()


def _draw_header(self, context):
    prefs = get_prefs(context)
    if prefs and prefs.shelf_location == 'HEADER':
        draw_shelf(self.layout, context)


def refresh_location():
    """Redraw all viewports after the shelf location preference changed."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def register():
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
