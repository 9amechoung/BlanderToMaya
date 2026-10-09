"""Maya projects: File > Project Window / Set Project.

A project is a folder with Maya's standard sub folders (scenes, sourceimages,
images...) and a workspace.mel file, so the same folder works in Maya too.
Once a project is set:
  - Open / Save Scene start in <project>/scenes
  - image textures open from <project>/sourceimages, sounds from <project>/sound
  - renders go to <project>/images, autosaves to <project>/autosave
Opening a .blend that lives inside a project sets that project automatically.
"""

import json
import os
import re

import bpy
from bpy.props import StringProperty

WORKSPACE_FILE = "workspace.mel"

# The "Primary Project Locations" of Maya's Project Window: (rule, label, default folder)
PRIMARY_RULES = (
    ("scene", "Scenes", "scenes"),
    ("templates", "Templates", "assets"),
    ("images", "Images", "images"),
    ("sourceImages", "Source Images", "sourceimages"),
    ("renderData", "Render Data", "renderData"),
    ("clips", "Clips", "clips"),
    ("sound", "Sound", "sound"),
    ("scripts", "Scripts", "scripts"),
    ("diskCache", "Disk Cache", "data"),
    ("movie", "Movies", "movies"),
    ("translatorData", "Translator Data", "data"),
    ("timeEditor", "Time Editor", "Time Editor"),
    ("autoSave", "AutoSave", "autosave"),
    ("sceneAssembly", "Scene Assembly", "sceneAssembly"),
)

# The other rules Maya writes into a new workspace.mel
SECONDARY_RULES = (
    ("mayaAscii", "scenes"), ("mayaBinary", "scenes"), ("offlineEdit", "scenes/edits"),
    ("mel", "scripts"), ("3dPaintTextures", "sourceimages/3dPaintTextures"),
    ("fileCache", "cache/nCache"), ("fluidCache", "cache/nCache/fluid"), ("particles", "cache/particles"),
    ("depth", "renderData/depth"), ("iprImages", "renderData/iprImages"), ("shaders", "renderData/shaders"),
    ("furFiles", "renderData/fur/furFiles"), ("furImages", "renderData/fur/furImages"),
    ("furEqualMap", "renderData/fur/furEqualMap"), ("furAttrMap", "renderData/fur/furAttrMap"),
    ("furShadowMap", "renderData/fur/furShadowMap"), ("teClipExports", "Time Editor/Clip Exports"),
    ("OBJ", "data"), ("eps", "data"), ("illustrator", "data"), ("move", "data"),
)

_RULE_RE = re.compile(r'workspace\s+-fr\s+"([^"]+)"\s+"([^"]*)"\s*;')
_state = {"current": "", "recent": []}


# ---------------------------------------------------------------------------
# workspace.mel and the remembered project
# ---------------------------------------------------------------------------

def _state_file():
    return os.path.join(bpy.utils.user_resource('CONFIG'), "maya_style_project.json")


def _load_state():
    try:
        with open(_state_file(), encoding="utf-8") as f:
            data = json.load(f)
        _state["current"] = data.get("current", "")
        _state["recent"] = [p for p in data.get("recent", []) if isinstance(p, str)]
    except (OSError, ValueError):
        pass


def _save_state():
    try:
        os.makedirs(os.path.dirname(_state_file()), exist_ok=True)
        with open(_state_file(), "w", encoding="utf-8") as f:
            json.dump(_state, f, indent=1)
    except OSError:
        pass


def read_workspace(root):
    """Rules of a project folder ({} when it has no workspace.mel)."""
    try:
        with open(os.path.join(root, WORKSPACE_FILE), encoding="utf-8", errors="replace") as f:
            return dict(_RULE_RE.findall(f.read()))
    except OSError:
        return {}


def default_rules():
    rules = {key: folder for key, _label, folder in PRIMARY_RULES}
    rules.update(SECONDARY_RULES)
    return rules


def write_workspace(root, rules):
    merged = default_rules()
    merged.update(read_workspace(root))
    merged.update(rules)
    lines = ["//Maya 2024 Project Definition", ""]
    lines += ['workspace -fr "%s" "%s";' % (key, value.replace("\\", "/")) for key, value in merged.items()]
    with open(os.path.join(root, WORKSPACE_FILE), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def current_project():
    root = _state["current"]
    return root if root and os.path.isdir(root) else ""


def project_dir(rule, create=False):
    """Absolute folder of a rule in the current project ('' without a project)."""
    root = current_project()
    if not root:
        return ""
    value = read_workspace(root).get(rule) or default_rules().get(rule, rule)
    path = value if os.path.isabs(value) else os.path.join(root, value)
    path = os.path.normpath(path)
    if create:
        try:
            os.makedirs(path, exist_ok=True)
        except OSError:
            pass
    return path


def find_project(filepath):
    """The project folder a file lives in (a parent folder with workspace.mel), or ''."""
    folder = os.path.dirname(os.path.abspath(filepath))
    for _ in range(6):
        if os.path.isfile(os.path.join(folder, WORKSPACE_FILE)):
            return folder
        parent = os.path.dirname(folder)
        if parent == folder:
            break
        folder = parent
    return ""


def _is_default_render_path(path):
    return path in {"", "//", "/tmp/", "/tmp\\", "\\tmp\\"} or path.replace("\\", "/").startswith("/tmp/")


def apply_paths(scene=None):
    """Point Blender's default folders at the current project."""
    root = current_project()
    if not root:
        return
    paths = bpy.context.preferences.filepaths
    for attr, rule in (("texture_directory", "sourceImages"), ("render_output_directory", "images"),
                       ("sound_directory", "sound")):
        if hasattr(paths, attr):
            setattr(paths, attr, project_dir(rule) + os.sep)
    autosave = project_dir("autoSave", create=True)
    if autosave and os.path.isdir(autosave):
        paths.temporary_directory = autosave + os.sep
    images = project_dir("images")
    for sc in ([scene] if scene else bpy.data.scenes):
        if sc is not None and _is_default_render_path(sc.render.filepath):
            sc.render.filepath = os.path.join(images, "")


def set_project(root):
    root = os.path.normpath(bpy.path.abspath(root))
    _state["current"] = root
    recent = [p for p in _state["recent"] if os.path.normcase(p) != os.path.normcase(root)]
    _state["recent"] = [root] + recent[:9]
    _save_state()
    apply_paths()
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


# ---------------------------------------------------------------------------
# Project Window
# ---------------------------------------------------------------------------

class MayaProjectSettings(bpy.types.PropertyGroup):
    __annotations__ = {
        "name": StringProperty(name="Current Project", default="new_project"),
        "location": StringProperty(name="Location", subtype='DIR_PATH'),
        **{"rule_" + key: StringProperty(name=label, default=folder) for key, label, folder in PRIMARY_RULES},
    }


def _fill_settings(settings, root):
    rules = default_rules()
    if root:
        rules.update(read_workspace(root))
        settings.name = os.path.basename(root)
        settings.location = os.path.dirname(root) + os.sep
    else:
        settings.name = "new_project"
        settings.location = os.path.join(os.path.expanduser("~"), "")
    for key, _label, _folder in PRIMARY_RULES:
        setattr(settings, "rule_" + key, rules.get(key, ""))


class MAYA_OT_project_new(bpy.types.Operator):
    """Start a new project with Maya's default folders"""
    bl_idname = "maya.project_new"
    bl_label = "New"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        settings = context.window_manager.maya_project
        location = settings.location
        _fill_settings(settings, "")
        if location:
            settings.location = location
        return {'FINISHED'}


class MAYA_OT_project_window(bpy.types.Operator):
    """Create or edit a project: a folder with scenes, sourceimages, images... (like Maya's Project Window)"""
    bl_idname = "maya.project_window"
    bl_label = "Project Window"

    def invoke(self, context, event):
        _fill_settings(context.window_manager.maya_project, current_project())
        try:
            return context.window_manager.invoke_props_dialog(self, width=560, confirm_text="Accept")
        except TypeError:  # Blender 4.0: no confirm_text
            return context.window_manager.invoke_props_dialog(self, width=560)

    def draw(self, context):
        settings = context.window_manager.maya_project
        layout = self.layout
        split = layout.split(factor=0.22)
        split.alignment = 'RIGHT'
        split.label(text="Current Project:")
        row = split.row(align=True)
        row.prop(settings, "name", text="")
        row.operator("maya.project_new", text="New")
        split = layout.split(factor=0.22)
        split.alignment = 'RIGHT'
        split.label(text="Location:")
        split.prop(settings, "location", text="")
        root = os.path.join(bpy.path.abspath(settings.location), settings.name)
        layout.label(text=root, icon='FILE_FOLDER')
        box = layout.box()
        box.label(text="Primary Project Locations", icon='DISCLOSURE_TRI_DOWN')
        col = box.column(align=True)
        col.use_property_split = True
        for key, _label, _folder in PRIMARY_RULES:
            col.prop(settings, "rule_" + key)
        layout.label(text="Accept: creates the folders and workspace.mel, then sets this project", icon='INFO')

    def execute(self, context):
        settings = context.window_manager.maya_project
        name = settings.name.strip()
        location = bpy.path.abspath(settings.location.strip())
        if not name or not location:
            self.report({'ERROR'}, "Enter a project name and a location")
            return {'CANCELLED'}
        root = os.path.normpath(os.path.join(location, name))
        rules = {key: getattr(settings, "rule_" + key).strip() for key, _label, _folder in PRIMARY_RULES}
        try:
            os.makedirs(root, exist_ok=True)
            for folder in rules.values():
                if folder:
                    os.makedirs(folder if os.path.isabs(folder) else os.path.join(root, folder), exist_ok=True)
            write_workspace(root, rules)
        except OSError as ex:
            self.report({'ERROR'}, "Could not create the project: %s" % ex)
            return {'CANCELLED'}
        set_project(root)
        self.report({'INFO'}, "Project set to %s" % root)
        return {'FINISHED'}


class MAYA_OT_set_project(bpy.types.Operator):
    """Pick a project folder; Open / Save / Render / textures then use its folders (like Maya's Set Project)"""
    bl_idname = "maya.set_project"
    bl_label = "Set Project"

    directory: StringProperty(subtype='DIR_PATH')
    filter_folder: bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})

    def invoke(self, context, event):
        root = current_project()
        if root:
            self.directory = os.path.join(os.path.dirname(root), "")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        root = os.path.normpath(bpy.path.abspath(self.directory))
        if not os.path.isdir(root):
            self.report({'ERROR'}, "Folder not found: %s" % root)
            return {'CANCELLED'}
        if not os.path.isfile(os.path.join(root, WORKSPACE_FILE)):
            # Like Maya's "Create Default Workspace"
            try:
                write_workspace(root, {})
            except OSError as ex:
                self.report({'ERROR'}, "Could not write %s: %s" % (WORKSPACE_FILE, ex))
                return {'CANCELLED'}
        set_project(root)
        self.report({'INFO'}, "Project set to %s" % root)
        return {'FINISHED'}


class MAYA_OT_set_recent_project(bpy.types.Operator):
    """Set this project again"""
    bl_idname = "maya.set_recent_project"
    bl_label = "Set Recent Project"
    bl_options = {'INTERNAL'}

    path: StringProperty()

    def execute(self, context):
        if not os.path.isdir(self.path):
            self.report({'ERROR'}, "Folder not found: %s" % self.path)
            return {'CANCELLED'}
        set_project(self.path)
        return {'FINISHED'}


class MAYA_MT_recent_projects(bpy.types.Menu):
    bl_label = "Recent Projects"

    def draw(self, context):
        layout = self.layout
        if not _state["recent"]:
            layout.label(text="(no recent projects)")
        for path in _state["recent"]:
            layout.operator("maya.set_recent_project", text=path, icon='FILE_FOLDER').path = path


# ---------------------------------------------------------------------------
# Open / Save in <project>/scenes
# ---------------------------------------------------------------------------

def _blend_name():
    return bpy.path.basename(bpy.data.filepath) or "untitled.blend"


class MAYA_OT_open_scene(bpy.types.Operator):
    """Open a scene, starting in the project's scenes folder (Ctrl+O)"""
    bl_idname = "maya.open_scene"
    bl_label = "Open Scene..."

    def execute(self, context):
        scenes = project_dir("scene", create=True)
        if scenes:
            bpy.ops.wm.open_mainfile('INVOKE_DEFAULT', filepath=os.path.join(scenes, ""))
        else:
            bpy.ops.wm.open_mainfile('INVOKE_DEFAULT')
        return {'FINISHED'}


class MAYA_OT_save_scene(bpy.types.Operator):
    """Save the scene; a new scene is saved into the project's scenes folder (Ctrl+S)"""
    bl_idname = "maya.save_scene"
    bl_label = "Save Scene"

    save_as: bpy.props.BoolProperty(name="Save As", default=False, options={'SKIP_SAVE'})

    def execute(self, context):
        if bpy.data.filepath and not self.save_as:
            bpy.ops.wm.save_mainfile('INVOKE_DEFAULT')
            return {'FINISHED'}
        scenes = project_dir("scene", create=True)
        if scenes and (not bpy.data.filepath or find_project(bpy.data.filepath) != current_project()):
            bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT', filepath=os.path.join(scenes, _blend_name()))
        else:
            bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT')
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Drawing helpers and handlers
# ---------------------------------------------------------------------------

def draw_project_status(layout):
    root = current_project()
    layout.operator("maya.project_window", text=os.path.basename(root) if root else "No Project",
                    icon='FILE_FOLDER')


@bpy.app.handlers.persistent
def _on_load(_dummy):
    path = bpy.data.filepath
    if path:
        root = find_project(path)
        if root and os.path.normcase(root) != os.path.normcase(current_project()):
            set_project(root)
            return
    apply_paths()


classes = (
    MayaProjectSettings,
    MAYA_OT_project_new,
    MAYA_OT_project_window,
    MAYA_OT_set_project,
    MAYA_OT_set_recent_project,
    MAYA_MT_recent_projects,
    MAYA_OT_open_scene,
    MAYA_OT_save_scene,
)


def _apply_on_start():
    try:
        apply_paths()
    except Exception:
        pass
    return None


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.maya_project = bpy.props.PointerProperty(type=MayaProjectSettings)
    _load_state()
    bpy.app.handlers.load_post.append(_on_load)
    bpy.app.timers.register(_apply_on_start, first_interval=0.5)


def unregister():
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    del bpy.types.WindowManager.maya_project
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
