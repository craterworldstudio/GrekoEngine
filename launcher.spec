# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hidden_imports = collect_submodules('core.behaviours')
hidden_imports += [
    'core.behaviours.blinker',
    'core.behaviours.breather',
    'core.behaviours.lookAt',
    'core.behaviours.mouthSequencer',
    'core.BehaviourBaseClasses',
    'core.glb_parser',
    'core.skeleton',
    'core.behaviours_manager',
    'core.mesh_data',
    'core.animator',
    'core.scene',
    'core.entity',
    'core.components.transform',
    'core.components.camera',
    'core.components.mesh',
    'core.gltf_accessors',
    'core.vrm_adapter',
    'greko_run',
    'numpy',
    'tkinter',
]

binaries = [
    ('core/greko_native.cpython-313-x86_64-linux-gnu.so', 'core'),
    # On Windows this would be: ('core/greko_native.pyd', 'core')
]

datas = [
    #('shaders/', 'shaders'),
    ('core/behaviours/__init__.py', 'core/behaviours'),
    ('core/__init__.py', 'core'),
    ('GEN_PHENOME_SEQ/', 'GEN_PHENOME_SEQ'),
]

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,   # Set False to hide terminal on Windows; keep True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

