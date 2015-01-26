from __future__ import with_statement
from fabric.api import local, settings, abort, run, cd, env
from fabric.decorators import hosts
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, sed
from fabric.operations import sudo, put
import os,time, httplib


def authentication_check(username, password, server):
	with settings(warn_only=True, abort_on_prompts=True):
		env.host_string = server
		env.user = username
		env.password = password
		result = True
		try:
			tmp = sudo('ls')
		except:
			result = False
		print "DEPLOYMENT:%s:ENDDEPLOYMENT"%result


def command_check(username, password, server, command):
	with settings(warn_only=True, abort_on_prompts=True):
		env.host_string = server
		env.user = username
		env.password = password
		sudo('which %s'%command)


def deploy(branch, username, password, server, sys_call):
	env.host_string = server
	env.user = username
	env.password = password
	sudo('%s %s'%(sys_call, branch))


