# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# vosk 的 DLL 从当前环境动态定位（不再写死本机路径）；未安装 vosk 时跳过语音功能
binaries = []
try:
    import vosk
    binaries.append((os.path.join(os.path.dirname(vosk.__file__), '*.dll'), 'vosk'))
except ImportError:
    pass

# 语音模型较大，不随仓库分发；存在时才打包
datas = [('images', 'images')]
if os.path.isdir('models'):
    datas.append(('models', 'models'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'winotify',
        'winreg',
        'pyaudio',
        'pythoncom',
        'win32com',
        'win32com.client',
        'win32com.shell',
        # matplotlib 后端 — 打包 Qt5Agg 避免图表空白
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_qt',
        'matplotlib.backends.qt_compat',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'PyQt5.QtQml',
        'PyQt5.QtQuick',
        'PyQt5.QtWebEngine',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebChannel',
        'PyQt5.QtTest',
        'PyQt5.QtBluetooth',
        'PyQt5.QtNfc',
        'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets',
        'PyQt5.QtSensors',
        'PyQt5.QtPositioning',
        'PyQt5.QtXml',
        'PyQt5.QtXmlPatterns',
        'PyQt5.QtSql',
        'PyQt5.QtHelp',
        'PyQt5.QtNetwork',
        'PyQt5.QtDBus',
        'PyQt5.QtDesigner',
        'PyQt5.uic',
        'PyQt5.QtSerialPort',
        'PyQt5.QtLocation',
        'PyQt5.QtDataVisualization',
        'PyQt5.QtPurchasing',
        'PyQt5.QtScript',
        'PyQt5.QtScriptTools',
        'PyQt5.QtWinExtras',
        'PyQt5.QtX11Extras',
        'PyQt5.QtMacExtras',
        'PyQt5.QtSvg',
        'PyQt5.QtPrintSupport',
        'PyQt5.Qt3DCore',
        'PyQt5.Qt3DRender',
        'PyQt5.Qt3DInput',
        'PyQt5.Qt3DLogic',
        'PyQt5.Qt3DAnimation',
        'PyQt5.Qt3DExtras',
        'notebook',
        'jupyter',
        'jupyter_client',
        'jupyter_core',
        'ipykernel',
        'ipython',
        'pygments',
        'scipy',
        'pandas',
        'sympy',
        'cv2',
        'opencv',
        'tensorflow',
        'torch',
        'caffe2',
        'theano',
        'kivy',
        'wx',
        'PySide2',
        'PySide6',
        'PyQt6',
        'enchant',
        'matplotlib.tests',
        'numpy.testing',
        'numpy.random.tests',
        'numpy.core.tests',
        'numpy.fft.tests',
        'numpy.lib.tests',
        'numpy.linalg.tests',
        'numpy.ma.tests',
        'numpy.matrixlib.tests',
        'numpy.polynomial.tests',
        'numpy.testing.tests',
        'numpy.distutils.tests',
        'numpy.f2py.tests',
        'numpy.polynomial.tests',
        'numpy.distutils',
        'numpy.f2py',
        'matplotlib.tests',
        'pytest',
        'nose',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MT任务助手',
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
    icon='images\\icon.ico',
    version='file_version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MT任务助手',
)
