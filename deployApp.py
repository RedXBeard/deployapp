from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config
from kivy.uix.image import Image
from kivy.utils import get_color_from_hex
from kivy.properties import ListProperty, StringProperty
from config import PROJECT_PATH, DB

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

	def __init__(self, *args, **kwargs):
		super(Deployment, self).__init__(*args, **kwargs)
		self.username = DB.store_get('username')
		self.password = DB.store_get('password')

	def load_servers(self):
		server_datas = DB.store_get('servers')
		self.servers = []
		for server in server_datas:
			self.servers.append({'name':server['name'], 
								 'url':server['url']})
		self.servers.append({'name':"", 'url':""})


	def switch_screen(self, screen, side='left'):
		self.transition = SlideTransition(direction=side)
		self.current = screen


	def uanme_pword_update(self):
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


class DeploymentApp(App):
	def __init__(self, *args, **kwargs):
		super(DeploymentApp, self).__init__(*args, **kwargs)
		Builder.load_file('%s/assets/style.kv'%PROJECT_PATH)


	def build(self):
		layout = Deployment()
		layout.load_servers()
		layout.servers_correction_screenbased('action')
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
