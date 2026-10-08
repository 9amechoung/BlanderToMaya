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


class MAYA_OT_space_hotbox(bpy.types.Operator):
    """Tap Space: four view / single view. Hold Space: hotbox with all menus"""
    bl_idname = "maya.space_hotbox"
    bl_label = "Hotbox"

    def invoke(self, context, event):
        if context.area is None or context.area.type != 'VIEW_3D':
            return {'PASS_THROUGH'}  # timeline etc.: Space keeps playing the animation
        self._start = time.monotonic()
        self._timer = context.window_manager.event_timer_add(0.02, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        context.window_manager.event_timer_remove(self._timer)

    def modal(self, context, event):
        if event.type == 'SPACE' and event.value == 'RELEASE':
            self._finish(context)
            bpy.ops.screen.region_quadview()
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
