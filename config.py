from kivy.storage.jsonstore import JsonStore
from subprocess import Popen, PIPE
from os import path, makedirs
from kivy import __version__


def run_command(command):
    process = Popen(command, stdout=PIPE)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print output.strip()
    rc = process.poll()
    return rc


def run_syscall(cmd, serve_output=False):
    """
    run_syscall; handle sys calls this function used as shortcut.

    ::cmd: String, shell command is expected.
    """
    # import time
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    # out, err = "", ""
    # print "COMMAND: ", cmd
    # while p.poll() in (None, 0, 1):
    #     print "BARBAROS"
    #     output = p.stdout.readline()
    #     error = p.stderr.readline()
    #     out += output
    #     err += error
    #     print output, error
    #     if output == "":
    #         print "FUCKED"
    #         break
    #     time.sleep(1)
    # print "exited", p.poll()
    # try:
    #     p.terminate()
    # except OSError:
    #     pass
    return out.rstrip(), err.rstrip()

PATH_SEPERATOR = '\\' if path.realpath(__file__).find('\\') != -1 else '/'
PROJECT_PATH = PATH_SEPERATOR.join(
    path.realpath(__file__).split(PATH_SEPERATOR)[:-1]
)

if PATH_SEPERATOR == '/':
    cmd = "echo $HOME"
else:
    cmd = "echo %USERPROFILE%"
out, err = run_syscall(cmd)
DATAFILE = "%(out)s%(ps)s.kivydeployapp%(ps)sdeployapp" % {
    'out': out.rstrip(),
    'ps': PATH_SEPERATOR
}

KIVY_VERSION = __version__

DB = JsonStore(DATAFILE)
directory = path.dirname(DATAFILE)
if not path.exists(directory):
    makedirs(directory)
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
