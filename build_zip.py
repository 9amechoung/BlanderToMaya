"""Build the installable add-on zip: python build_zip.py -> dist/maya_style_v<version>.zip

Old versions stay in dist/ so every release can still be downloaded.
"""
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "maya_style")
with open(os.path.join(SRC, "blender_manifest.toml"), encoding="utf-8") as f:
    VERSION = re.search(r'^version = "([^"]+)"', f.read(), re.M).group(1)
OUT = os.path.join(ROOT, "dist", "maya_style_v%s.zip" % VERSION)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirnames, filenames in os.walk(SRC):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            zf.write(path, os.path.relpath(path, ROOT))
print("Wrote", OUT)
