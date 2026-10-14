"""Maya Edit Mesh > Connect.

Works on what is selected, like Maya:
  Edges     slices a new edge through the selected edges of each face (an edge ring becomes a new
            loop, two edges on a corner are joined straight across). Segments adds more
            edges, Slide moves them along the selected edges.
  Vertices  cuts each face straight between its selected vertices.
  Faces     splits each face through the middle of its edges (Segments: more splits).

Change Segments / Slide afterwards in Adjust Last Operation (F9) or with the option box,
like Maya's Connect settings.
"""

import bmesh
import bpy
import mathutils.kdtree
from bpy.props import FloatProperty, IntProperty


def _ring_directions(edges):
    """For each selected edge, which end is its start, so Slide moves every new edge
    toward the same side across the ring (and across corners)."""
    selected = set(edges)
    start = {}
    for seed in edges:
        if seed in start:
            continue
        start[seed] = seed.verts[0]
        stack = [seed]
        while stack:
            a = stack.pop()
            for la in a.link_loops:
                for lb in la.face.loops:
                    b = lb.edge
                    if b is a or b not in selected or b in start:
                        continue
                    # Going around the face, the start of a lines up with the end of b
                    a_follows_winding = start[a] is la.vert
                    start[b] = lb.link_loop_next.vert if a_follows_winding else lb.vert
                    stack.append(b)
    return start


def _verts_on_segment(bm, kd, a, b):
    """Vertices lying inside the segment a-b, ordered from a (the cuts made on that old edge)."""
    seg = b - a
    length = seg.length
    if length == 0:
        return []
    found = []
    for _co, index, _dist in kd.find_range((a + b) / 2, length / 2 + 1e-6):
        v = bm.verts[index]
        t = (v.co - a).dot(seg) / (length * length)
        if 1e-6 < t < 1 - 1e-6 and (v.co - a.lerp(b, t)).length < length * 1e-4:
            found.append((t, v))
    return [v for _t, v in sorted(found, key=lambda item: item[0])]


def _faces_with_two_edges(edges):
    count = {}
    for e in edges:
        for f in e.link_faces:
            count[f] = count.get(f, 0) + 1
    return [f for f, n in count.items() if n >= 2]


class MAYA_OT_connect(bpy.types.Operator):
    """Connect: slice new edges through the selected edges (an edge ring becomes a new loop),
    between the selected vertices, or across the selected faces. Nothing is merged
    (Maya Edit Mesh > Connect)"""
    bl_idname = "maya.connect"
    bl_label = "Connect"
    bl_options = {'REGISTER', 'UNDO'}

    segments: IntProperty(name="Segments", description="How many new edges", default=1, min=1, soft_max=20)
    slide: FloatProperty(name="Slide", description="Move the new edges along the selected edges",
                         default=0.0, min=-1.0, max=1.0, subtype='FACTOR')

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        mode = tuple(context.tool_settings.mesh_select_mode)
        if mode == (False, False, True):
            return self._faces(context)
        # Decide by what is selected, not by the select mode: an edge ring picked in vertex
        # mode is still sliced through, never joined vertex to vertex along a path.
        if self._has_edge_pairs(context):
            return self._edges(context)
        if mode[1]:
            self.report({'WARNING'}, "Select two or more edges on the same face (an edge ring or a corner)")
            return {'CANCELLED'}
        return self._vertices(context)

    @staticmethod
    def _has_edge_pairs(context):
        for obj in context.objects_in_mode_unique_data:
            if obj.type == 'MESH':
                bm = bmesh.from_edit_mesh(obj.data)
                if _faces_with_two_edges([e for e in bm.edges if e.select]):
                    return True
        return False

    def _edges(self, context):
        made = 0
        for obj in context.objects_in_mode_unique_data:
            if obj.type != 'MESH':
                continue
            bm = bmesh.from_edit_mesh(obj.data)
            edges = [e for e in bm.edges if e.select]
            if not _faces_with_two_edges(edges):
                continue
            starts = _ring_directions(edges)
            # Positions, not BMVerts: the subdivide can rebuild the vertices
            ends = [(starts[e].co.copy(), e.other_vert(starts[e]).co.copy()) for e in edges]
            result = bmesh.ops.subdivide_edges(
                bm, edges=edges, cuts=self.segments, use_grid_fill=False, use_single_edge=False,
                quad_corner_type='STRAIGHT_CUT', use_only_quads=False)
            new_edges = [g for g in result["geom_inner"] if isinstance(g, bmesh.types.BMEdge)]
            if abs(self.slide) > 1e-6:
                bm.verts.ensure_lookup_table()
                kd = mathutils.kdtree.KDTree(len(bm.verts))
                for v in bm.verts:
                    kd.insert(v.co, v.index)
                kd.balance()
                n = self.segments
                shift = self.slide * 0.98 / (n + 1)
                moves = []
                for a, b in ends:
                    for k, v in enumerate(_verts_on_segment(bm, kd, a, b)):
                        moves.append((v, a.lerp(b, (k + 1) / (n + 1) + shift)))
                for v, co in moves:  # move after finding all, so the search sees the cuts unmoved
                    v.co = co
            # Select just the new edges, like Maya (ready to slide or keep working on)
            for f in bm.faces:
                f.select_set(False)
            for e in bm.edges:
                e.select_set(False)
            for e in new_edges:
                e.select_set(True)
            bm.select_flush_mode()
            bmesh.update_edit_mesh(obj.data)
            made += len(new_edges)
        if not made:
            self.report({'WARNING'}, "Select two or more edges on the same face (an edge ring or a corner)")
            return {'CANCELLED'}
        return {'FINISHED'}

    def _vertices(self, context):
        try:
            # Split the faces between the selected vertices (a straight cut, like Maya)
            bpy.ops.mesh.vert_connect()
        except RuntimeError as ex:
            self.report({'WARNING'}, str(ex).replace("Error: ", "").strip() or "Select two or more vertices")
            return {'CANCELLED'}
        return {'FINISHED'}

    def _faces(self, context):
        made = 0
        for obj in context.objects_in_mode_unique_data:
            if obj.type != 'MESH':
                continue
            bm = bmesh.from_edit_mesh(obj.data)
            faces = [f for f in bm.faces if f.select]
            if not faces:
                continue
            edges = list({e for f in faces for e in f.edges})
            result = bmesh.ops.subdivide_edges(
                bm, edges=edges, cuts=self.segments, use_grid_fill=True, use_single_edge=False,
                quad_corner_type='STRAIGHT_CUT', use_only_quads=False)
            new_edges = [g for g in result["geom_inner"] if isinstance(g, bmesh.types.BMEdge)]
            made += len(new_edges)
            bmesh.update_edit_mesh(obj.data)
        if not made:
            self.report({'WARNING'}, "Select some faces")
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (
    MAYA_OT_connect,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
