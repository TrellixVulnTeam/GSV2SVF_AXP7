# (c) Continuum Analytics, Inc. / http://continuum.io
# All Rights Reserved
# This file is under the BSD license

# Helper script which is called from within the nsis install process
# on Windows.  The fact that we put this file into the standard library
# directory is merely a convenience.  This way, functionally can easily
# be tested in an installation.

import os
import sys
import traceback
from os.path import abspath, basename, dirname, join, exists

ROOT_PREFIX = sys.prefix

# Install an exception hook which pops up a message box.
# Ideally, exceptions will get returned to NSIS and logged there,
# etc, but this is a stopgap solution for now.
old_excepthook = sys.excepthook

def gui_excepthook(exctype, value, tb):
    try:
        import ctypes, traceback
        MB_ICONERROR = 0x00000010
        title = u'Installation Error'
        msg = u''.join(traceback.format_exception(exctype, value, tb))
        ctypes.windll.user32.MessageBoxW(0, msg, title, MB_ICONERROR)
    finally:
        # Also call the old exception hook to let it do
        # its thing too.
        old_excepthook(exctype, value, tb)
sys.excepthook = gui_excepthook

# If pythonw is being run, there may be no write function
if sys.stdout and sys.stdout.write:
    out = sys.stdout.write
    err = sys.stderr.write
else:
    def write(x):
        pass
    out = write
    err = write


def mk_menus(remove=False):
    try:
        import menuinst
    except ImportError:
        return
    menu_dir = join(ROOT_PREFIX, 'Menu')
    if exists(menu_dir):
        for fn in os.listdir(menu_dir):
            if fn.endswith('.json'):
                shortcut = join(menu_dir, fn)
                try:
                    menuinst.install(shortcut, remove)
                except Exception as e:
                    out("Failed to process %s...\n" % shortcut)
                    err("Error: %s\n" % str(e))
                    err("Traceback:\n%s\n" % traceback.format_exc(20))
                else:
                    out("Processed %s successfully.\n" % shortcut)


def mk_dirs():
    envs_dir = join(ROOT_PREFIX, 'envs')
    if not exists(envs_dir):
        os.mkdir(envs_dir)

    # some cleanup
    try:
        os.unlink(join(ROOT_PREFIX, 'preconda.tar.bz2'))
    except:
        pass


allusers = (not exists(join(ROOT_PREFIX, '.nonadmin')))

def remove_from_path():
    from _system_path import (remove_from_system_path,
                              broadcast_environment_settings_change)
    for path in [ROOT_PREFIX,
                 join(ROOT_PREFIX, 'Library\\bin'),
                 join(ROOT_PREFIX, 'Scripts'), ]:
        remove_from_system_path(path, allusers)
    broadcast_environment_settings_change()


def add_to_path():
    from _system_path import (add_to_system_path,
                              broadcast_environment_settings_change)
    # if previous Anaconda installs left remnants, remove those
    remove_from_path()
    # add Anaconda to the path
    add_to_system_path([ROOT_PREFIX,
                        join(ROOT_PREFIX, 'Scripts'),
                        join(ROOT_PREFIX, "Library\\bin")], allusers)
    broadcast_environment_settings_change()


def main():
    global ROOT_PREFIX

    if (basename(sys.prefix) == '_conda' and
              basename(dirname(sys.prefix)) == 'envs'):
        ROOT_PREFIX = abspath(join(sys.prefix, '..', '..'))

    cmd = sys.argv[1].strip()
    if cmd == 'mkmenus':
        mk_menus(remove=False)
    elif cmd == 'rmmenus':
        mk_menus(remove=True)
    elif cmd == 'mkdirs':
        mk_dirs()
    elif cmd == 'addpath':
        add_to_path()
    elif cmd == 'rmpath':
        remove_from_path()
    else:
        sys.exit("ERROR: did not expect %r" % cmd)


if __name__ == '__main__':
    main()
