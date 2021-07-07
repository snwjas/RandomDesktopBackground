# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

src_path = os.path.abspath(os.path.dirname(os.getcwd()))


def get_module_path(filename):
    return os.path.join(src_path, filename)


a = Analysis([get_module_path('application.py'),
              get_module_path('app_menu.py'),
              get_module_path('args_definition.py'),
              get_module_path('app_run_type.py'),
              get_module_path('configurator.py'),
              get_module_path('const_config.py'),
              get_module_path('mylogger.py'),
              get_module_path('utils.py'),
              get_module_path('task_timer.py'),
              get_module_path('get_background.py'),
              get_module_path('set_background.py'),
              ],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='随机桌面背景',
          version='version.rc',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          icon='favicon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='随机桌面背景')
