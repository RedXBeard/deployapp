from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.config import Config
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.properties import (ListProperty, StringProperty,
							 NumericProperty, BooleanProperty)
from kivy.graphics import Canvas, Color, Rectangle
from config import PROJECT_PATH, DB, CALLS, run_syscall
import os


def findparent(curclass, targetclass):
	reqclass = curclass
	if type(targetclass) in [unicode, str]:
		targetclass_name = targetclass
	else:
		targetclass_name = str(targetclass().__class__).\
			split('.')[1].replace("'>", "")

	while True:
		cls = str(reqclass.__class__).split('.')[1].replace("'>", "")
		if cls == targetclass_name:
			break
		elif cls == 'core':
			reqclass = None
			break

		reqclass = reqclass.parent
	return reqclass


class TryAgainButton(Button):
	pass


class CrossButton(Button):
	pass


class CompleteButton(Button):
	pass


class ActionServerItem(BoxLayout):
	name = StringProperty("")
	url = StringProperty("")


	def pressed_but(self):
		images = self.checkbox.children
		if images:
			self.checkbox.remove_widget(images[0])
			self.input_box.name_input.background_color = (1,1,1,1)
			self.input_box.url_input.background_color = (1,1,1,1)
		else:
			image = Image(source = "assets/tick2.png",
						  pos = self.checkbox.pos,
						  size = self.checkbox.size)
			self.checkbox.add_widget(image)
			self.input_box.name_input.background_color = get_color_from_hex('eeeeee')
			self.input_box.url_input.background_color = get_color_from_hex('eeeeee')


class SettingsServerItem(BoxLayout):
	name = StringProperty("")
	url = StringProperty("")


	def add_server(self, *args):
		name = self.input_box.name_input.text.strip()
		url = self.input_box.url_input.text.strip()
		if name and url:
			servers = DB.store_get('servers')
			servers.append({'name': name, 'url': url})
			DB.store_put('servers', servers)
			DB.store_sync()
			root = findparent(self, Deployment)
			root.load_servers()
			root.servers_correction_screenbased('settings')


	def delete_server(self, *args):
		name = self.input_box.name_input.text.strip()
		url = self.input_box.url_input.text.strip()
		tmp = {'name':name, 'url':url}
		servers = DB.store_get('servers')
		if filter(lambda x: x == tmp, servers):
			servers.pop(servers.index(tmp))
			DB.store_put('servers', servers)
			DB.store_sync()
			root = findparent(self, Deployment)
			root.load_servers()
			root.servers_correction_screenbased('settings')


class Deployment(ScreenManager):
	servers = ListProperty([])
	username = StringProperty("")
	password = StringProperty("")

	branch = StringProperty("")
	checked_servers = ListProperty([])
	progress = NumericProperty(0)
	unit_progress = NumericProperty(0)


	def __init__(self, *args, **kwargs):
		super(Deployment, self).__init__(*args, **kwargs)
		self.load_servers()
		self.servers_correction_screenbased('action')
		self.username = DB.store_get('username')
		self.password = DB.store_get('password')


	def load_servers(self):
		server_datas = DB.store_get('servers')
		self.servers = []
		for server in server_datas:
			self.servers.append({'name':server['name'],
								 'url':server['url']})
		self.servers.append({'name':"", 'url':""})


	def switch_screen(self, screen, side='up'):
		self.transition = SlideTransition(direction=side)
		self.current = screen


	def fast_switch_screen(self, obj, screen='action_screen', side='up'):
		self.switch_screen(screen, side)


	def uname_pword_update(self):
		username = self.current_screen.username_input.text.strip()
		password = self.current_screen.password_input.text.strip()

		if username and password:
			DB.store_put('username', username)
			DB.store_put('password', password)
			DB.store_sync()
			self.username = username
			self.password = password


	def servers_correction_screenbased(self, screen):
		emptyslot = filter(lambda x: x['name'].strip() == '' or \
									 x['url'].strip() == '', self.servers)
		if emptyslot:
			for slot in emptyslot:
				self.servers.pop(self.servers.index(slot))

		if screen == 'action':
			pass

		if screen == 'settings':
			self.servers.append({'name': "", 'url': ""})


	def servers_to_items(self, raw_index, item):
		return {
			'name': item['name'],
			'url': item['url']
		}


	def authentication_check(self, name, server):
		def inner_authentication_check():
			result = message = ""
			os.chdir('%(path)s'%{'path': PROJECT_PATH})
			out, err = run_syscall('fab authentication_check:%(username)s,%(password)s,%(server)s'%\
								{'username': self.username, 'password':self.password, 'server': server})
			try:
				result = out.split('DEPLOYMENT:')
				result = result[1].split(":")[0].strip()
				result = True and result == "True" or False
			except:
				result = False
			if not result:
				message = u"%s authentication failed"%name
			return result, message
		return inner_authentication_check


	def branch_check(self, name, branch):
		def inner_branch_check():
			result = message = ""
			os.chdir("/tmp")
			out, err = run_syscall('git archive %(branch)s --prefix=%(branch)s/ --remote=git@gitlab.markafoni.net:dikeyshop/dikeyshop.git | tar -xf -'%{'branch':branch})
			out = out.strip()

			if out.find('tar: Exiting with failure status due to previous errors') != -1 or \
				err.find('tar: Exiting with failure status due to previous errors') != -1:
				result = False
				message = u"Branch not found for %s"%name
			else:
				out, err = run_syscall("rm -rf %s"%branch)
				result = True
			os.chdir(PROJECT_PATH)
			return result, message
		return inner_branch_check


	def display_message(self, screen, message):
		def inner_display_message():
			screen.info.text = message
			return True, ""
		return inner_display_message


	def deploy_server(self, username, password, name, url, branch):
		def inner_deploy_server():
			if name not in CALLS:
				return False, u"Required call cannot be found"
			else:
				out, err = run_syscall("fab %(call)s:%(branch)s,%(username)s,%(password)s,%(server)s"%\
									{'call': CALLS['%s'%name],
									 'branch': branch,
									 'username': username,
									 'password': password,
									 'server': url})
				self.display_message(self.current_screen, u'%s --> %s'%(branch, name))()
				return True, ""
		return inner_deploy_server


	def reset_progess(self):
		def inner_reset_progress(process_count):
			self.unit_progress = 340 / process_count
			self.progress = 0
		return inner_reset_progress


	def deploymentComplition(self, requests, output=False):
		if requests:
			if not output:
				call = requests[0]
				call()
				Clock.schedule_once(lambda dt: self.deploymentComplition(requests[1:]), 1)
			else:
				call = requests[0]
				result, message = call()
				if not result and False:
					self.display_message(self.current_screen, message)()
					self.display_error_buts_deployment()
					return False
				else:
					Clock.schedule_once(lambda dt: self.deploymentComplition(requests[1:], output=True), 1)
					self.progress += self.unit_progress
		else:
			ok_but = CompleteButton(size = (100, 30), pos = (150, 90), text = "[b]COMPLETE[/b]",
										background_color=get_color_from_hex('97BE0D'))
			ok_but.fast_bind('on_release', self.fast_switch_screen, screen='action_screen', side='up')
			self.current_screen.add_widget(ok_but)
			self.progress = 340
			return True


	def collect_deploy_data(self):
		screen = self.current_screen
		servers = screen.server_items.children[0].children[0].children
		self.branch = screen.branch.text.strip()
		self.checked_servers = filter(lambda x: x.checkbox.children, servers)


	def reset_screen(self):
		if self.current == 'deploy_screen':
			children = self.current_screen.children
			buttons = []
			for child in children:
				if str(child.__class__).find('Button') != -1:
					buttons.append(child)
			for button in buttons:
				for child in button.children:
					button.remove_widget(child)
				self.current_screen.remove_widget(button)


	def display_error_buts_deployment(self):
		cross_img = Image(source="assets/cross2.png", size=(20, 20), pos=(370, 270))
		cross_but = CrossButton(size=(20, 20), pos=(370, 270), background_color=get_color_from_hex('404248'))
		cross_but.add_widget(cross_img)
		cross_but.fast_bind('on_release', self.fast_switch_screen, screen='action_screen', side='up')

		tryagain_but = TryAgainButton(size = (100, 30), pos = (150, 90), text = "[b]TRY AGAIN[/b]",
											   background_color=get_color_from_hex('FFCC00'))
		tryagain_but.fast_bind('on_release', self.fast_switch_screen, screen='action_screen', side='up')
		self.current_screen.add_widget(cross_but)
		self.current_screen.add_widget(tryagain_but)

	def deploy(self):
		if self.current == "deploy_screen":
			self.reset_screen()
			screen = self.current_screen
			if not self.branch:
				self.display_message(screen, u"'branch' is empty!")()
				self.display_error_buts_deployment()
			else:
				if not self.checked_servers:
					self.display_message(screen, u"at least check one server please!")()
					self.display_error_buts_deployment()
				else:
					result = True
					requests = []
					for server in self.checked_servers:
						name = server.input_box.name_input.text.strip()
						url = server.input_box.url_input.text.strip()
						tmp = [self.display_message(screen, '%s authentication check'%name),
							   self.authentication_check(name, url),
							   self.display_message(screen, '%s branch check'%self.branch),
							   self.branch_check(name, self.branch)]
						requests.extend(tmp)

					for server in self.checked_servers:
						name = server.input_box.name_input.text.strip()
						url = server.input_box.url_input.text.strip()
						requests.append(self.display_message(screen, '%s deployment...'%name))
						tmp_call = self.deploy_server(self.username,
													  self.password,
													  name, url,
													  self.branch)
						#requests.append(tmp_call)
					requests.append(self.display_message(screen, "Deployment complete for branch; '%s'"%self.branch))
					self.reset_progess()(len(requests))
					self.deploymentComplition(requests, output=True)


class DeploymentApp(App):
	def __init__(self, *args, **kwargs):
		super(DeploymentApp, self).__init__(*args, **kwargs)
		Builder.load_file('%s/assets/style.kv'%PROJECT_PATH)


	def build(self):
		layout = Deployment()
#		layout.switch_screen('action_screen', 'up')
#		layout.load_servers()
#		layout.servers_correction_screenbased('action')
		return layout


if __name__ == "__main__":
    """
    Window sizes and wanted skills are set, then app calls
    """
    Window.size = (400, 300)
    Window.clearcolor = (get_color_from_hex("1C1D20"))
    Window.borderless = False
    Config.set('kivy', 'desktop', 1)
    Config.set('graphics', 'fullscreen', 0)
    Config.set('graphics', 'resizable', 0)

    DeploymentApp().run()
