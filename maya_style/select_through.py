"""Drag selection that also picks what is behind (Maya's default), without X-ray display.

Blender only selects hidden objects / vertices / edges / faces with box or lasso
selection when X-ray is on. This turns X-ray on when the mouse button goes down
and back off when it comes up (or, after a drag, once the box / lasso selection
is done), so the viewport keeps looking solid.
Blender's own box / lasso selection does the selecting.
"""

import bpy

from .prefs import get_prefs


def _xray_attr(shading):
    return "show_xray_wireframe" if shading.type == 'WIREFRAME' else "show_xray"


def _last_op_pointer(context):
    ops = context.window_manager.operators
    return ops[-1].as_pointer() if len(ops) else 0


# The X-ray state switched on for the current press, to put back afterwards.
_state = {}


def _restore():
    if not _state:
        return
    try:
        setattr(_state["shading"], _state["attr"], False)
        if _state["alpha"] is not None:
            _state["shading"].xray_alpha = _state["alpha"]
        if _state["area"] is not None:
            _state["area"].tag_redraw()
    except ReferenceError:
        pass  # the viewport was closed meanwhile
    _state.clear()


def _watch():
    """After a drag, Blender's box / lasso eats the button release; once it has finished
    it shows up as the newest operator in the history - then X-ray goes back off."""
    if not _state:
        return None
    if _last_op_pointer(bpy.context) != _state["last_op"]:
        _restore()
        return None
    return 0.05


class MAYA_OT_select_through(bpy.types.Operator):
    """Box / lasso select also selects hidden (back) objects and components, like Maya.
    X-ray is switched on while the mouse button is down and off again once the selection is done"""
    bl_idname = "maya.select_through"
    bl_label = "Select Through"
    bl_options = {'INTERNAL'}

    release: bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})

    def invoke(self, context, event):
        # Never consume the event: Blender's own click / box / lasso selection must still run.
        if self.release:
            _restore()  # before the click is handled, so clicking still picks what is in front
            return {'PASS_THROUGH'}
        prefs = get_prefs(context)
        space = context.space_data
        if (prefs is not None and not prefs.use_select_through) or space is None or space.type != 'VIEW_3D':
            return {'PASS_THROUGH'}
        _restore()
        shading = space.shading
        attr = _xray_attr(shading)
        if getattr(shading, attr):
            return {'PASS_THROUGH'}  # X-ray already on
        alpha = shading.xray_alpha if attr == "show_xray" else None
        _state.update(shading=shading, attr=attr, alpha=alpha, area=context.area,
                      last_op=_last_op_pointer(context))
        setattr(shading, attr, True)
        if alpha is not None and alpha >= 1.0:
            shading.xray_alpha = 0.99  # at 1.0 Blender treats X-ray as off for selection
        if not bpy.app.timers.is_registered(_watch):
            bpy.app.timers.register(_watch, first_interval=0.05)
        return {'PASS_THROUGH'}


def register():
    bpy.utils.register_class(MAYA_OT_select_through)


def unregister():
    if bpy.app.timers.is_registered(_watch):
        bpy.app.timers.unregister(_watch)
    _restore()
    bpy.utils.unregister_class(MAYA_OT_select_through)
