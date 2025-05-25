# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Collect all submodules from mspy in case of dynamic imports
hiddenimports = collect_submodules('mspy') + collect_submodules('gui')

a = Analysis(
    ['mmass.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('configs/monomers.xml', 'configs'),
        ('configs/compounds.xml', 'configs'),
        ('configs/config.xml', 'configs'),
        ('configs/enzymes.xml', 'configs'),
        ('configs/mascot.xml', 'configs'),
        ('configs/modifications.xml', 'configs'),
        ('configs/presets.xml', 'configs'),
        ('configs/references.xml', 'configs'),
        ('license.txt', '.'),
        ('readme.md', '.'),
        ('changelog.md', '.'),
        ('User Guide.pdf', '.'),
        ('gui/images/msw/icon.ico', 'gui/images/msw'),
        # You can also glob this like: ('gui/images/msw/*', 'gui/images/msw') if needed
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'Tkinter', 'tcl'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mmassx-6.0.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='gui/images/msw/icon.ico'
)
