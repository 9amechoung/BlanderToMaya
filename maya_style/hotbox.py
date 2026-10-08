"""Maya hotbox (Space) and the Ctrl+Right-click selection conversion marking menu.

Space tapped: toggle four view / single view (like Maya).
Space held:   the hotbox - every menu of the menu bar around the cursor, plus
              view changes (Top / Front / Side / Perspective) like Maya's
              center-zone marking menu.
"""

import time

import bpy

from . import maya_menus

HOLD_SECONDS = 0.2


_VIEW_PROPS = ("view_perspective", "view_rotation", "view_location", "view_distance")

# space pointer -> {"maximized": quad index or None, "views": {index or "persp": saved view}}
_four_view_memory = {}


def _save_view(rv3d):
    view = {name: getattr(rv3d, name) for name in _VIEW_PROPS}
    view["view_rotation"] = view["view_rotation"].copy()
    view["view_location"] = view["view_location"].copy()
    view["side"] = getattr(rv3d, "is_orthographic_side_view", False)
    return view


def _load_view(rv3d, view):
    for name in _VIEW_PROPS:
        setattr(rv3d, name, view[name])
    try:
        rv3d.is_orthographic_side_view = view["side"]  # "Top Orthographic" instead of "User ..."
    except (AttributeError, TypeError):
        pass


def toggle_four_view(context, hovered):
    """Four view <-> single view, like Maya:
    - in four view, the view under the mouse is the one that gets maximized;
    - every view keeps its own camera, so going back to four view puts the perspective
      view back as perspective (and the orthographic views as they were)."""
    space = context.space_data
    key = space.as_pointer()
    if len(space.region_quadviews) > 0:
        quads = list(space.region_quadviews)
        views = {i: _save_view(rv3d) for i, rv3d in enumerate(quads)}
        views["persp"] = _save_view(space.region_3d)
        maximized = None
        if hovered is not None:
            for i, rv3d in enumerate(quads):
                if rv3d.as_pointer() == hovered.as_pointer() and rv3d.as_pointer() != space.region_3d.as_pointer():
                    maximized = i
        _four_view_memory[key] = {"maximized": maximized, "views": views}
        bpy.ops.screen.region_quadview()
        if maximized is not None:
            _load_view(space.region_3d, views[maximized])
        return

    memory = _four_view_memory.get(key)
    if memory is not None and memory["maximized"] is not None:
        # Keep any pan / zoom done while the orthographic view was maximized.
        memory["views"][memory["maximized"]] = _save_view(space.region_3d)
    bpy.ops.screen.region_quadview()
    if memory is None:
        return

    tries = [0]

    def _restore():
        quads = list(space.region_quadviews)
        if not quads:
            tries[0] += 1
            return 0.05 if tries[0] < 20 else None
        views = memory["views"]
        if memory["maximized"] is not None:
            _load_view(space.region_3d, views["persp"])
        for i, rv3d in enumerate(quads):
            if i in views and rv3d.as_pointer() != space.region_3d.as_pointer():
                rv3d.view_location = views[i]["view_location"]
                rv3d.view_distance = views[i]["view_distance"]
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        return None

    if _restore() is not None:
        bpy.app.timers.register(_restore, first_interval=0.05)


class MAYA_OT_space_hotbox(bpy.types.Operator):
    """Tap Space: four view / single view. Hold Space: hotbox with all menus"""
    bl_idname = "maya.space_hotbox"
    bl_label = "Hotbox"

    def invoke(self, context, event):
        if context.area is None or context.area.type != 'VIEW_3D':
            return {'PASS_THROUGH'}  # timeline etc.: Space keeps playing the animation
        self._start = time.monotonic()
        self._hovered = context.region_data  # the view under the mouse (one of the four in four view)
        self._timer = context.window_manager.event_timer_add(0.02, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        context.window_manager.event_timer_remove(self._timer)

    def modal(self, context, event):
        if event.type == 'SPACE' and event.value == 'RELEASE':
            self._finish(context)
            toggle_four_view(context, self._hovered)
            return {'FINISHED'}
        if event.type == 'TIMER' and time.monotonic() - self._start >= HOLD_SECONDS:
            self._finish(context)
            bpy.ops.wm.call_menu_pie(name="MAYA_MT_hotbox")
            return {'FINISHED'}
        if event.type == 'ESC':
            self._finish(context)
            return {'CANCELLED'}
        return {'PASS_THROUGH'}


class MAYA_OT_set_view(bpy.types.Operator):
    """Switch the view (Maya hotbox center marking menu)"""
    bl_idname = "maya.set_view"
    bl_label = "Set View"

    view: bpy.props.StringProperty(default='TOP')

    def execute(self, context):
        if self.view == 'PERSP':
            rv3d = context.region_data
            if rv3d is not None and rv3d.view_perspective != 'PERSP':
                bpy.ops.view3d.view_persportho()
            return {'FINISHED'}
        if self.view == 'CAMERA':
            return bpy.ops.view3d.view_camera()
        return bpy.ops.view3d.view_axis(type=self.view)


class MAYA_MT_hotbox(bpy.types.Menu):
    bl_idname = "MAYA_MT_hotbox"
    bl_label = "Hotbox"

    def draw(self, context):
        pie = self.layout.menu_pie()
        wm = context.window_manager

        pie.operator("maya.set_view", text="Left View", icon='TRIA_LEFT').view = 'LEFT'        # W
        pie.operator("maya.set_view", text="Right View", icon='TRIA_RIGHT').view = 'RIGHT'     # E
        pie.operator("maya.set_view", text="Front View", icon='TRIA_DOWN').view = 'FRONT'      # S

        box = pie.box().column(align=True)                                                     # N
        row = box.row(align=True)
        for idname in maya_menus.COMMON_MENUS:
            row.menu(idname)
        row.menu("MAYA_MT_help")
        row = box.row(align=True)
        for idname in maya_menus.SET_MENUS[wm.maya_menu_set]:
            row.menu(idname)
        row = box.row(align=True)
        row.prop(wm, "maya_menu_set", expand=True)

        pie.operator("maya.set_view", text="Top View", icon='TRIA_UP').view = 'TOP'            # NW
        pie.operator("maya.set_view", text="Perspective", icon='VIEW_PERSPECTIVE').view = 'PERSP'  # NE
        pie.operator("screen.region_quadview", text="Four View / Single View", icon='MESH_GRID')   # SW
        pie.operator("maya.set_view", text="Camera View", icon='VIEW_CAMERA').view = 'CAMERA'  # SE


class MAYA_MT_convert_marking_menu(bpy.types.Menu):
    """Ctrl+Right-click: convert the selection (Maya)"""
    bl_idname = "MAYA_MT_convert_marking_menu"
    bl_label = "Convert Selection"

    def draw(self, context):
        pie = self.layout.menu_pie()

        def item(text, to, icon='NONE'):
            pie.operator("maya.convert_selection", text=text, icon=icon).to = to

        item("To Vertices", 'VERT', 'VERTEXSEL')        # W
        item("To UVs", 'UV', 'UV')                      # E
        item("To Faces", 'FACE', 'FACESEL')             # S
        item("To Edges", 'EDGE', 'EDGESEL')             # N
        item("To Edge Loop", 'EDGE_LOOP')               # NW
        item("To Edge Ring", 'EDGE_RING')               # NE
        item("To Shell", 'SHELL')                       # SW
        item("To Shell Border", 'BORDER')               # SE


classes = (
    MAYA_OT_space_hotbox,
    MAYA_OT_set_view,
    MAYA_MT_hotbox,
    MAYA_MT_convert_marking_menu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
