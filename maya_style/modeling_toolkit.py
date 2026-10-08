"""Maya's Modeling Toolkit, as a 3D viewport sidebar tab (N > Modeling Toolkit)."""

import bpy

from .operators import set_props


def _button(layout, idname, text, icon='NONE', **props):
    op = layout.operator(idname, text=text, icon=icon)
    set_props(op, props)


class MAYA_PT_modeling_toolkit(bpy.types.Panel):
    bl_idname = "MAYA_PT_modeling_toolkit"
    bl_label = "Modeling Toolkit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Modeling Toolkit"

    def draw(self, context):
        layout = self.layout
        ts = context.scene.tool_settings
        obj = context.active_object
        in_edit = context.mode == 'EDIT_MESH'

        # Selection mode row: object / vertex / edge / face / multi
        row = layout.row(align=True)
        mode = tuple(ts.mesh_select_mode) if in_edit else (False, False, False)
        for value, icon, on in (('OBJECT', 'OBJECT_DATAMODE', not in_edit), ('VERT', 'VERTEXSEL', mode == (1, 0, 0)),
                                ('EDGE', 'EDGESEL', mode == (0, 1, 0)), ('FACE', 'FACESEL', mode == (0, 0, 1)),
                                ('MULTI', 'SNAP_VOLUME', mode == (1, 1, 1))):
            op = row.operator("maya.component_mode", text="", icon=icon, depress=on)
            op.mode = value

        # Selection options
        box = layout.box()
        box.label(text="Selection")
        attr = "use_proportional_edit" if in_edit else "use_proportional_edit_objects"
        row = box.row(align=True)
        row.prop(ts, attr, text="Soft Selection (B)", toggle=True)
        sub = row.row(align=True)
        sub.active = getattr(ts, attr)
        sub.prop(ts, "proportional_size", text="Radius")
        box.prop(ts, "proportional_edit_falloff", text="Falloff")
        if obj is not None and obj.type == 'MESH':
            row = box.row(align=True)
            row.label(text="Symmetry:")
            row.prop(obj, "use_mesh_mirror_x", text="X", toggle=True)
            row.prop(obj, "use_mesh_mirror_y", text="Y", toggle=True)
            row.prop(obj, "use_mesh_mirror_z", text="Z", toggle=True)
        row = box.row(align=True)
        _button(row, "mesh.select_more", "Grow")
        _button(row, "mesh.select_less", "Shrink")
        _button(row, "maya.convert_selection", "Edge Loop", to='EDGE_LOOP')
        _button(row, "maya.convert_selection", "Ring", to='EDGE_RING')

        # Mesh
        box = layout.box()
        box.label(text="Mesh")
        grid = box.grid_flow(columns=2, align=True)
        _button(grid, "maya.boolean", "Boolean Union", operation='UNION')
        _button(grid, "maya.boolean", "Boolean Difference", operation='DIFFERENCE')
        _button(grid, "object.join", "Combine")
        _button(grid, "mesh.separate", "Separate", type='LOOSE')
        _button(grid, "mesh.fill_holes", "Fill Hole")
        _button(grid, "mesh.symmetrize", "Mirror (Symmetrize)")

        # Components
        box = layout.box()
        box.label(text="Components")
        grid = box.grid_flow(columns=2, align=True)
        _button(grid, "view3d.edit_mesh_extrude_move_normal", "Extrude", 'FACESEL')
        _button(grid, "mesh.bevel", "Bevel", 'MOD_BEVEL')
        _button(grid, "mesh.bridge_edge_loops", "Bridge", 'MOD_LATTICE')
        _button(grid, "mesh.vert_connect_path", "Connect", 'LINKED')
        _button(grid, "mesh.merge", "Merge", 'AUTOMERGE_ON', type='CENTER')
        _button(grid, "maya.target_weld", "Target Weld", 'PIVOT_ACTIVE')
        _button(grid, "mesh.dissolve_mode", "Delete Edge/Vertex", 'X')
        _button(grid, "mesh.flip_normals", "Flip", 'NORMALS_FACE')

        # Tools
        box = layout.box()
        box.label(text="Tools")
        grid = box.grid_flow(columns=2, align=True)
        _button(grid, "mesh.knife_tool", "Multi-Cut", 'SCULPTMODE_HLT')
        _button(grid, "maya.quad_draw", "Quad Draw", 'MESH_DATA')
        _button(grid, "mesh.loopcut_slide", "Insert Edge Loop", 'MOD_MULTIRES')
        _button(grid, "mesh.offset_edge_loops_slide", "Offset Edge Loop")
        _button(grid, "transform.edge_slide", "Slide Edge", 'ARROW_LEFTRIGHT')
        _button(grid, "transform.tosphere", "Circularize", value=1.0)


def register():
    bpy.utils.register_class(MAYA_PT_modeling_toolkit)


def unregister():
    bpy.utils.unregister_class(MAYA_PT_modeling_toolkit)
