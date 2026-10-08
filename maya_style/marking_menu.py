"""Maya-style marking menus (Shift+Right-click in the 3D viewport).

Pie slot order in Blender: W, E, S, N, NW, NE, SW, SE.
The south slot holds a small grid of extra buttons, like Maya's marking menu.
"""

import bpy


def _op(layout, idname, text, icon, **props):
    op = layout.operator(idname, text=text, icon=icon)
    for key, value in props.items():
        setattr(op, key, value)
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


class MAYA_MT_mesh_marking_menu(bpy.types.Menu):
    bl_idname = "MAYA_MT_mesh_marking_menu"
    bl_label = "Modeling"

    def draw(self, context):
        pie = self.layout.menu_pie()
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
        row = box.row(align=True)
        _op(row, "maya.component_mode", "", 'VERTEXSEL', mode='VERT')
        _op(row, "maya.component_mode", "", 'EDGESEL', mode='EDGE')
        _op(row, "maya.component_mode", "", 'FACESEL', mode='FACE')
        _op(row, "maya.component_mode", "", 'OBJECT_DATAMODE', mode='TOGGLE')

        _op(pie, "mesh.loopcut_slide", "Insert Edge Loop", 'MOD_MULTIRES')  # N
        _op(pie, "mesh.knife_tool", "Multi-Cut", 'SCULPTMODE_HLT')           # NW
        _op(pie, "mesh.merge", "Target Weld", 'PIVOT_ACTIVE', type='LAST')  # NE
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
