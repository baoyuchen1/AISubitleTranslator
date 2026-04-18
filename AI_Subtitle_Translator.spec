# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules


project_dir = Path.cwd()
src_dir = project_dir / "src"

hiddenimports = []
hiddenimports += collect_submodules("av")
hiddenimports += collect_submodules("faster_whisper")
hiddenimports += collect_submodules("rapidocr_onnxruntime")
hiddenimports += collect_submodules("PIL")
hiddenimports += collect_submodules("tokenizers")

binaries = []
binaries += collect_dynamic_libs("av")
binaries += collect_dynamic_libs("ctranslate2")
datas = []
datas += collect_data_files("faster_whisper")
datas += collect_data_files("rapidocr_onnxruntime")
datas += collect_data_files("tokenizers")


a = Analysis(
    ["launch_gui.pyw"],
    pathex=[str(src_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AI Subtitle Translator",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AI Subtitle Translator",
)
