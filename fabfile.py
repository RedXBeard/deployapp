from __future__ import with_statement
from fabric.api import local, settings, abort, run, cd, env
from fabric.decorators import hosts
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, sed
from fabric.operations import sudo, put
import os,time, httplib

@hosts(['emu.markafoni.net'])
def deploy_zizigo(branch):
	print  "---local zizigo deployment---"
	env.user = "barbaros.yildirim"
	env.password = "89TuBa87"
	sudo('deploy_fila2 %s'%branch)
	print "\n\n"

@hosts(['emu.markafoni.net'])
def deploy_misspera(branch):
	print  "---local misspera deployment---"
	env.user = "barbaros.yildirim"
	env.password = "89TuBa87"
	sudo('deploy_cosmo2 %s'%branch)
	print "\n\n"

@hosts(['emu.markafoni.net'])
def deploy_enmoda(branch):
	print  "---local enmoda deployment---"
	env.user = "barbaros.yildirim"
	env.password = "89TuBa87"
	sudo('deploy_caracas2 %s'%branch)
	print "\n\n"

@hosts(['emu.markafoni.net'])
def deploy_all(branch):
	print  "---local vertical sites deployment---"
	env.user = "barbaros.yildirim"
	env.password = "89TuBa87"
	sudo('deploy2_all %s'%branch)
	print "\n\n"
