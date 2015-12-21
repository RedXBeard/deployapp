from __future__ import with_statement

from fabric.api import settings, env
from fabric.operations import sudo


def authentication_check(username, password, server):
    with settings(warn_only=True, abort_on_prompts=True):
        env.host_string = server
    env.user = username
    env.password = password
    result = True
    try:
        sudo('ls')
    except:
        result = False
    print "DEPLOYMENT:%s:ENDDEPLOYMENT" % result


def command_check(username, password, server, command):
    with settings(warn_only=True, abort_on_prompts=True):
        env.host_string = server
        env.user = username
        env.password = password
        sudo('which %s' % command)


def start_deployment(branch, username, password, server, sys_call):
    with settings(warn_only=True, abort_on_prompts=True):
        print "?????"
        env.host_string = server
        env.user = username
        env.password = password
        print "deployment process run!", '{} {} {} {}'.format(sys_call, branch, username, password)
        sudo('{} {} {} {}'.format(sys_call, branch, username, password))
