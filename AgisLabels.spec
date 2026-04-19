# -*- mode: python ; coding: utf-8 -*-
"""
AgisLabels.spec — PyInstaller build spec.
Works on Windows, macOS and Linux.
Run: pyinstaller AgisLabels.spec
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect barcode and qrcode data files
barcode_datas  = collect_data_files('barcode')
qrcode_datas   = collect_data_files('qrcode')
pandas_datas   = collect_data_files('pandas')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=barcode_datas + qrcode_datas,
    hiddenimports=[
        'PIL._tkinter_finder',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.pool',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.timedeltas',
        'openpyxl.cell._writer',
        'qrcode.image.pil',
        'barcode.writer',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtSvg',
    ] + collect_submodules('sqlalchemy'),
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy.testing'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AgisLabels Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                  # No terminal window
    icon='docs/icon.ico' if sys.platform == 'win32' else (
         'docs/icon.icns' if sys.platform == 'darwin' else None),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AgisLabels Pro',
)

# macOS: build a .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='AgisLabels Pro.app',
        icon='docs/icon.icns',
        bundle_identifier='com.agislabels.pro',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '2.0.0',
            'CFBundleVersion': '2.0.0',
            'NSPrincipalClass': 'NSApplication',
        },
    )

