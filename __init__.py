import platform
import os
import sys
import subprocess
import shutil
import pathlib
import hashlib
import base64
from textwrap import dedent
import tomllib

_needs_reload = "bpy" in locals()

import bpy
import addon_utils

from . import luxloader

if _needs_reload:
    import importlib
    luxloader = importlib.reload(luxloader)

# Check first if Blender and OS versions are compatible
if bpy.app.version < (4, 2, 0):
    raise Exception("\n\nUnsupported Blender version. 4.2 or higher is required by BlendLuxCore.")

if platform.system() in {"Linux", "Darwin"}:
    # Required for downloads from the LuxCore Online Library
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Load version information from blender_manifest.toml.
# Replaced the old "bl_info" dictionary.
manifest_path = pathlib.Path(__file__).parent.resolve() / 'blender_manifest.toml'
with open(manifest_path, "rb") as f:
    manifest_data = tomllib.load(f)
version_string = manifest_data['version']

# Load/download pyluxcore
if luxloader.am_in_extension:
    # We'll invoke download_pyluxcore at each init
    # We rely on pip local cache for this call to be transparent,
    # after the wheels have been downloaded once, unless an update is required
    download_status = luxloader.download_pyluxcore()
    if download_status == 0:
        # Ask Blender to do the install
        addon_utils.extensions_refresh(ensure_wheels=True)
    elif download_status == 1:
        # There was an error during download
        print(
            "[BLC] WARNING: Download of pyluxcore not successful... "
            "Import will be attempted, but may be unsuccessful..."
        )
    elif download_status == 2:
        # The version to be downloaded was already installed. Nothing to do.
        pass
    else:
        # Unknown error
        print(
            "[BLC] WARNING: Unknown return code received from download_pyluxcore()... "
            "Import will be attempted, but may be unsuccessful..."
        )

try:
    import pyluxcore
except ImportError as error:
    msg = "\n\nCould not import pyluxcore."
    # Raise from None to suppress the unhelpful
    # "during handling of the above exception, ..."
    raise RuntimeError(msg + "\n\nImportError: %s" % error) from None
else:
    if luxloader.blc_offline_install:
        # remove the install_offline_folder because we want a normal startup next time
        luxloader.delete_install_offline()

if luxloader.blc_dev_path and luxloader.am_in_extension:
    print('[BLC] USING LOCAL DEV VERSION OF BlendLuxCore')
    sys.path.insert(0, blc_dev_path)
    from BlendLuxCore import *
else:
    from . import properties, engine, handlers, operators, ui, nodes, utils
    from .utils.log import LuxCoreLog

def register():
    engine.register()
    handlers.register()
    operators.register()
    properties.register()
    ui.register()
    nodes.register()

    pyluxcore.Init(LuxCoreLog.add)
    print(f"BlendLuxCore {version_string} registered (with pyluxcore {pyluxcore.Version()})")

def unregister():
    engine.unregister()
    handlers.unregister()
    operators.unregister()
    properties.unregister()
    ui.unregister()
    nodes.unregister()
