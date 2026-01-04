# Cerebrum.spec
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

# --- This is the "smart" part ---
# It automatically finds all the hidden data files for our libraries
customtkinter_datas = collect_data_files('customtkinter', include_py_files=True)
llama_cpp_datas = collect_data_files('llama_cpp', include_py_files=True)
# ----------------------------------

a = Analysis(
    ['app/app.py'],
    pathex=[],
    binaries=[],
    # We add all the collected files here
    datas=customtkinter_datas + llama_cpp_datas,
    hiddenimports=['llama_cpp', 'llama_cpp.lib'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Cerebrum',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # This tells it to be a --windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# This builds the final --onedir folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Cerebrum',
)