"""Maya-style middle mouse drag for the Move / Rotate / Scale tools.

In Maya you click an axis handle on the manipulator (it turns yellow) and
then middle-drag anywhere in the viewport to move along that axis only.
Here, clicking (or dragging) a gizmo handle runs a transform that records
its axis; middle-dragging repeats a transform with that same axis.
"""

import bpy
from bpy.props import EnumProperty

# tool kind -> (transform operator, its RNA id name)
KINDS = {
    'TRANSLATE': ("translate", "TRANSFORM_OT_translate"),
    'ROTATE': ("rotate", "TRANSFORM_OT_rotate"),
    'RESIZE': ("resize", "TRANSFORM_OT_resize"),
}

TOOL_KEYMAPS = (
    ("3D View Tool: Move", 'TRANSLATE'),
    ("3D View Tool: Rotate", 'ROTATE'),
    ("3D View Tool: Scale", 'RESIZE'),
)

TOOL_KINDS = {
    "builtin.move": 'TRANSLATE',
    "builtin.rotate": 'ROTATE',
    "builtin.scale": 'RESIZE',
}


def last_axis_settings(context, kind):
    """Axis settings of the most recent transform of this kind (gizmo click/drag included)."""
    idname = KINDS[kind][1]
    for op in reversed(context.window_manager.operators):
        if op.bl_idname == idname:
            props = op.properties
            settings = {
                "constraint_axis": tuple(props.constraint_axis),
                "orient_type": props.orient_type,
            }
            if kind == 'ROTATE':
                settings["orient_axis"] = props.orient_axis
            return settings
    return None


def axis_label(settings, kind):
    if not settings:
        return "Free"
    axes = "".join(a for a, on in zip("XYZ", settings["constraint_axis"]) if on)
    if kind == 'ROTATE' and not axes:
        axes = settings.get("orient_axis", "")
        if settings["orient_type"] == 'VIEW':
            return "View"
    if not axes:
        return "Free"
    if len(axes) == 2:  # plane handle
        return axes + " plane"
    return axes


def active_tool_kind(context):
    try:
        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    except (AttributeError, TypeError):
        return None
    return TOOL_KINDS.get(tool.idname) if tool else None


class MAYA_OT_mmb_transform(bpy.types.Operator):
    """Middle-drag to move / rotate / scale along the last picked gizmo axis (like Maya)"""
    bl_idname = "maya.mmb_transform"
    bl_label = "Middle-drag Transform"

    kind: EnumProperty(
        items=(
            ('TRANSLATE', "Move", ""),
            ('ROTATE', "Rotate", ""),
            ('RESIZE', "Scale", ""),
        ),
        default='TRANSLATE',
    )

    def invoke(self, context, event):
        op_name, _idname = KINDS[self.kind]
        settings = last_axis_settings(context, self.kind) or {}
        operator = getattr(bpy.ops.transform, op_name)
        try:
            operator('INVOKE_DEFAULT', release_confirm=True, **settings)
        except (RuntimeError, TypeError):
            # e.g. a stored orientation that no longer exists: fall back to a free transform
            operator('INVOKE_DEFAULT', release_confirm=True)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MAYA_OT_mmb_transform)


def unregister():
    bpy.utils.unregister_class(MAYA_OT_mmb_transform)
