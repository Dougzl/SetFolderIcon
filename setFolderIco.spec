# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['__init__.py'],
    pathex=[],
    binaries=[],
    datas=[('utils.py', '.')],  # 添加数据文件
    hiddenimports=['utils'],     # 添加隐藏导入
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='setFolderIco',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['favicon.ico'],
)
