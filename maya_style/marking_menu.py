"""Maya-style marking menus (Shift+Right-click in the 3D viewport).

Pie slot order in Blender: W, E, S, N, NW, NE, SW, SE.
The south slot holds a small grid of extra buttons, like Maya's marking menu.
"""

import bpy

from .operators import set_props


def _op(layout, idname, text, icon, **props):
    op = layout.operator(idname, text=text, icon=icon)
    set_props(op, props)
    return op


class MAYA_MT_object_marking_menu(bpy.types.Menu):
    bl_idname = "MAYA_MT_object_marking_menu"
    bl_label = "Create"

    def draw(self, context):
        pie = self.layout.menu_pie()
        _op(pie, "mesh.primitive_plane_add", "Plane", 'MESH_PLANE')        # W
        _op(pie, "mesh.primitive_uv_sphere_add", "Sphere", 'MESH_UVSPHERE')  # E

        box = pie.box().column(align=True)                                  # S
        box.label(text="Object")
        grid = box.grid_flow(columns=2, align=True)
        _op(grid, "maya.add_modifier", "Smooth", 'MOD_SUBSURF', modifier='SUBSURF')
        _op(grid, "object.join", "Combine", 'SELECT_EXTEND')
        _op(grid, "maya.center_pivot", "Center Pivot", 'PIVOT_BOUNDBOX')
        _op(grid, "maya.freeze_transforms", "Freeze", 'FREEZE')
        _op(grid, "maya.delete_history", "Delete History", 'TRASH')
        _op(grid, "object.duplicate_move", "Duplicate", 'DUPLICATE')
        _op(grid, "object.shade_smooth", "Smooth Shade", 'SHADING_RENDERED')
        _op(grid, "object.shade_flat", "Flat Shade", 'SHADING_SOLID')

        _op(pie, "mesh.primitive_cube_add", "Cube", 'MESH_CUBE')            # N
        _op(pie, "mesh.primitive_cylinder_add", "Cylinder", 'MESH_CYLINDER')  # NW
        _op(pie, "mesh.primitive_cone_add", "Cone", 'MESH_CONE')            # NE
        _op(pie, "mesh.primitive_torus_add", "Torus", 'MESH_TORUS')         # SW
        _op(pie, "maya.component_mode", "Edit Components", 'EDITMODE_HLT', mode='TOGGLE')  # SE


# Shift+Right-click in component mode changes with the component type, like Maya.
# Each entry: (W, E, N, NW, NE, SW, SE, [grid items in the bottom box]); item = (idname, text, icon, props)
_COMPONENT_MENUS = {
    'VERT': (
        ("mesh.remove_doubles", "Merge Vertices", 'AUTOMERGE_ON', {}),
        ("mesh.bevel", "Chamfer Vertex", 'MOD_BEVEL', {"affect": 'VERTICES'}),
        ("mesh.vert_connect_path", "Connect", 'LINKED', {}),
        ("mesh.knife_tool", "Multi-Cut", 'SCULPTMODE_HLT', {}),
        ("maya.target_weld", "Target Weld", 'PIVOT_ACTIVE', {}),
        ("mesh.extrude_vertices_move", "Extrude Vertex", 'VERTEXSEL', {}),
        ("mesh.dissolve_verts", "Delete Vertex", 'X', {}),
        (
            ("mesh.vertices_smooth", "Average Vertices", 'MOD_SMOOTH', {}),
            ("transform.vert_slide", "Slide Vertex", 'ARROW_LEFTRIGHT', {}),
            ("mesh.merge", "Merge to Center", 'NONE', {"type": 'CENTER'}),
            ("mesh.loopcut_slide", "Insert Edge Loop", 'MOD_MULTIRES', {}),
            ("mesh.rip_move", "Detach (Rip)", 'NONE', {}),
            ("mesh.edge_face_add", "Fill (Make Face)", 'SNAP_FACE', {}),
        ),
    ),
    'EDGE': (
        ("mesh.bevel", "Bevel Edge", 'MOD_BEVEL', {"affect": 'EDGES'}),
        ("mesh.bridge_edge_loops", "Bridge", 'MOD_LATTICE', {}),
        ("mesh.loopcut_slide", "Insert Edge Loop", 'MOD_MULTIRES', {}),
        ("mesh.knife_tool", "Multi-Cut", 'SCULPTMODE_HLT', {}),
        ("view3d.edit_mesh_extrude_move_normal", "Extrude Edge", 'EDGESEL', {}),
        ("mesh.dissolve_edges", "Delete Edge", 'X', {}),
        ("transform.edge_slide", "Slide Edge", 'ARROW_LEFTRIGHT', {}),
        (
            ("mesh.merge", "Collapse", 'NONE', {"type": 'COLLAPSE'}),
            ("mesh.fill_holes", "Fill Hole", 'SNAP_FACE', {}),
            ("mesh.offset_edge_loops_slide", "Offset Edge Loop", 'NONE', {}),
            ("transform.edge_crease", "Crease", 'SHARPCURVE', {}),
            ("mesh.edge_rotate", "Spin Edge", 'NONE', {}),
            ("mesh.mark_seam", "Cut UVs (Seam)", 'NONE', {"clear": False}),
        ),
    ),
    'FACE': (
        ("view3d.edit_mesh_extrude_move_normal", "Extrude Face", 'FACESEL', {}),
        ("mesh.bridge_edge_loops", "Bridge", 'MOD_LATTICE', {}),
        ("mesh.poke", "Poke Face", 'NONE', {}),
        ("mesh.knife_tool", "Multi-Cut", 'SCULPTMODE_HLT', {}),
        ("mesh.inset", "Extrude Inward (Inset)", 'FULLSCREEN_EXIT', {}),
        ("mesh.duplicate_move", "Duplicate Face", 'DUPLICATE', {}),
        ("mesh.separate", "Extract", 'NONE', {"type": 'SELECTED'}),
        (
            ("mesh.spin", "Wedge (Spin)", 'NONE', {}),
            ("mesh.quads_convert_to_tris", "Triangulate", 'MOD_TRIANGULATE', {}),
            ("mesh.tris_convert_to_quads", "Quadrangulate", 'NONE', {}),
            ("mesh.subdivide", "Smooth / Add Divisions", 'MESH_GRID', {"smoothness": 1.0}),
            ("mesh.flip_normals", "Reverse Normals", 'NORMALS_FACE', {}),
            ("mesh.delete", "Delete Face", 'X', {"type": 'FACE'}),
        ),
    ),
}


def _item(layout, entry):
    idname, text, icon, props = entry
    _op(layout, idname, text, icon, **props)


class MAYA_MT_mesh_marking_menu(bpy.types.Menu):
    bl_idname = "MAYA_MT_mesh_marking_menu"
    bl_label = "Modeling"

    def draw(self, context):
        pie = self.layout.menu_pie()
        mode = tuple(context.tool_settings.mesh_select_mode)
        kind = {(True, False, False): 'VERT', (False, True, False): 'EDGE', (False, False, True): 'FACE'}.get(mode)
        if kind is None:  # several component types at once: the general menu
            MAYA_MT_mesh_marking_menu._draw_general(pie)
            return
        w, e, n, nw, ne, sw, se, grid_items = _COMPONENT_MENUS[kind]
        _item(pie, w)                                                            # W
        _item(pie, e)                                                            # E
        box = pie.box().column(align=True)                                       # S
        box.ui_units_x = 16  # room for the full labels
        box.label(text={'VERT': "Vertex", 'EDGE': "Edge", 'FACE': "Face"}[kind] + " Tools")
        grid = box.grid_flow(columns=2, align=True)
        for entry in grid_items:
            _item(grid, entry)
        row = box.row(align=True)
        _op(row, "maya.component_mode", "", 'VERTEXSEL', mode='VERT')
        _op(row, "maya.component_mode", "", 'EDGESEL', mode='EDGE')
        _op(row, "maya.component_mode", "", 'FACESEL', mode='FACE')
        _op(row, "maya.component_mode", "", 'OBJECT_DATAMODE', mode='TOGGLE')
        _item(pie, n)                                                            # N
        _item(pie, nw)                                                           # NW
        _item(pie, ne)                                                           # NE
        _item(pie, sw)                                                           # SW
        _item(pie, se)                                                           # SE

    @staticmethod
    def _draw_general(pie):
        _op(pie, "view3d.edit_mesh_extrude_move_normal", "Extrude", 'FACESEL')  # W
        _op(pie, "mesh.bevel", "Bevel", 'MOD_BEVEL')                             # E
        box = pie.box().column(align=True)                                       # S
        box.label(text="Edit Mesh")
        grid = box.grid_flow(columns=2, align=True)
        _op(grid, "mesh.bridge_edge_loops", "Bridge", 'MOD_LATTICE')
        _op(grid, "mesh.fill", "Fill Hole", 'SNAP_FACE')
        _op(grid, "mesh.merge", "Merge", 'AUTOMERGE_ON', type='CENTER')
        _op(grid, "mesh.dissolve_mode", "Dissolve", 'X')
        _op(grid, "mesh.subdivide", "Subdivide", 'MESH_GRID')
        _op(grid, "mesh.quads_convert_to_tris", "Triangulate", 'MOD_TRIANGULATE')
        _op(grid, "mesh.flip_normals", "Reverse Normals", 'NORMALS_FACE')
        _op(grid, "mesh.duplicate_move", "Duplicate Face", 'DUPLICATE')
        _op(pie, "mesh.loopcut_slide", "Insert Edge Loop", 'MOD_MULTIRES')  # N
        _op(pie, "mesh.knife_tool", "Multi-Cut", 'SCULPTMODE_HLT')           # NW
        _op(pie, "maya.target_weld", "Target Weld", 'PIVOT_ACTIVE')  # NE
        _op(pie, "mesh.inset", "Inset", 'FULLSCREEN_EXIT')                  # SW
        _op(pie, "transform.edge_slide", "Edge Slide", 'ARROW_LEFTRIGHT')   # SE


classes = (
    MAYA_MT_object_marking_menu,
    MAYA_MT_mesh_marking_menu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
