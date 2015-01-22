from kivy.storage.jsonstore import JsonStore
from subprocess import Popen, PIPE
import os

def run_syscall(cmd):
    """
    run_syscall; handle sys calls this function used as shortcut.

    ::cmd: String, shell command is expected.
    """
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    return out.rstrip()

PATH_SEPERATOR = '\\' if os.path.realpath(__file__).find('\\') != -1 else '/'
PROJECT_PATH = PATH_SEPERATOR.join(os.path.realpath(__file__).
                                   split(PATH_SEPERATOR)[:-1])

if PATH_SEPERATOR == '/':
    cmd = "echo $HOME"
else:
    cmd = "echo %USERPROFILE%"
out = run_syscall(cmd)
DATAFILE = "%(out)s%(ps)s.kivydeployapp%(ps)sdeployapp" % {'out': out.rstrip(),
                                                           'ps': PATH_SEPERATOR}

DB = JsonStore(DATAFILE)
directory = os.path.dirname(DATAFILE)
if not os.path.exists(directory):
	os.makedirs(directory)
	DB.store_put('servers', [])
	DB.store_put('username', "")
	DB.store_put('password', "")
	DB.store_sync()
if not DB.store_exists('servers'):
	DB.store_put('servers', [])
	DB.store_sync()
if not DB.store_exists('username'):
	DB.store_put('username', "")
	DB.store_sync()
if not DB.store_exists('password'):
	DB.store_put('password', "")
	DB.store_sync()
