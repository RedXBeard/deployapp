from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.config import Config
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.properties import (
    ListProperty, StringProperty,
    NumericProperty)
from config import PROJECT_PATH, DB, run_syscall
import os


def findparent(curclass, targetclass):
    """find wanted widget from selected or current one"""
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
    cmd = StringProperty("")

    def pressed_but(self):
        images = self.checkbox.children
        if images:
            self.checkbox.remove_widget(images[0])
            self.input_box.name_input.background_color = (1, 1, 1, 1)
            self.input_box.url_input.background_color = (1, 1, 1, 1)
        else:
            image = Image(source="assets/tick2.png",
                          pos=self.checkbox.pos,
                          size=self.checkbox.size)
            self.checkbox.add_widget(image)
            name_input = self.input_box.name_input
            url_input = self.input_box.url_input
            name_input.background_color = get_color_from_hex('eeeeee')
            url_input.background_color = get_color_from_hex('eeeeee')


class SettingsServerItem(BoxLayout):
    name = StringProperty("")
    url = StringProperty("")
    cmd = StringProperty("")

    def add_server(self, *args):
        name = self.input_box.name_input.text.strip()
        url = self.input_box.url_input.text.strip()
        cmd = self.input_box.cmd_input.text.strip()
        if name and url and cmd:
            servers = DB.store_get('servers')
            servers.append({'name': name, 'url': url, 'cmd': cmd})
            DB.store_put('servers', servers)
            DB.store_sync()
            root = findparent(self, Deployment)
            root.load_servers()
            root.servers_correction_screenbased('settings')

    def delete_server(self, *args):
        name = self.input_box.name_input.text.strip()
        url = self.input_box.url_input.text.strip()
        cmd = self.input_box.cmd_input.text.strip()
        tmp = {'name': name, 'url': url, 'cmd': cmd}
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
            name = 'name' in server and server['name'] or ''
            url = 'url' in server and server['url'] or ''
            cmd = 'cmd' in server and server['cmd'] or ''
            self.servers.append({'name': name, 'url': url, 'cmd': cmd})
        self.servers.append({'name': '', 'url': '', 'cmd': ''})

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
        emptyslot = filter(
            lambda x: x['name'].strip() == '' or (
                x['url'].strip() == '' or x['cmd'].strip() == ''),
            self.servers)
        if emptyslot:
            for slot in emptyslot:
                self.servers.pop(self.servers.index(slot))

        if screen == 'action':
            pass

        if screen == 'settings':
            self.servers.append({'name': "", 'url': "", 'cmd': ""})

    def servers_to_items(self, raw_index, item):
        return {
            'name': item['name'],
            'url': item['url'],
            'cmd': item['cmd']
        }

    def authentication_check(self, name, server):
        def inner_authentication_check():
            result = message = ""
            sys_call = 'fab authentication_check:%(username)s,'
            sys_call += '%(password)s,%(server)s'
            os.chdir('%(path)s' % {'path': PROJECT_PATH})
            out, err = run_syscall(
                sys_call % {
                    'username': self.username,
                    'password': self.password,
                    'server': server})
            try:
                result = out.split('DEPLOYMENT:')
                result = result[1].split(":")[0].strip()
                result = True and result == "True" or False
            except:
                result = False
            if not result:
                message = u"%s authentication failed" % name
            return result, message
        return inner_authentication_check

    def branch_check(self, name, branch):
        def inner_branch_check():
            sys_call = 'git archive %(branch)s --prefix=%(branch)s/ '
            sys_call += '--remote=git@gitlab.markafoni.net:'
            sys_call += 'dikeyshop/dikeyshop.git | tar -xf -'

            result = message = ""
            os.chdir("/tmp")
            out, err = run_syscall(sys_call % {'branch': branch})
            out = out.strip()

            error = 'tar: Exiting with failure status due to previous errors'

            if not filter(lambda x: x.find(error) != -1, [out, err]):
                result = False
                message = u"Branch not found for %s" % name
            else:
                out, err = run_syscall("rm -rf %s" % branch)
                result = True
            os.chdir(PROJECT_PATH)
            return result, message
        return inner_branch_check

    def command_check(self, server, command):
        def inner_command_check():
            sys_call = 'fab command_check:%(username)s,%(password)s,'
            sys_call += '%(server)s,%(command)s'
            out, err = run_syscall(sys_call % {
                'username': self.username, 'password': self.password,
                'server': server, 'command': command})
            if err.strip():
                return False, '%s command not found on server' % command
            else:
                out = out.replace('which %s' % command, ' ')
                if out.find(command) != -1:
                    return True, ""
                else:
                    return False, '%s command not found on server' % command
        return inner_command_check

    def display_message(self, screen, message):
        def inner_display_message():
            screen.info.text = message
            return True, ""
        return inner_display_message

    def deploy_server(self, username, password, name, url, command, branch):
        def inner_deploy_server():
            sys_call = "fab deploy:%(branch)s,%(username)s,"
            sys_call += "%(password)s,%(server)s,%(call)s"
            out, err = run_syscall(
                sys_call % {
                    'call': command,
                    'branch': branch,
                    'username': username,
                    'password': password,
                    'server': url
                }
            )
            self.display_message(
                self.current_screen, u'%s --> %s' % (branch, name))()
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
                Clock.schedule_once(
                    lambda dt: self.deploymentComplition(requests[1:]), 1)
            else:
                call = requests[0]
                result, message = call()
                if not result:
                    self.display_message(self.current_screen, message)()
                    self.display_error_buts_deployment()
                    return False
                else:
                    Clock.schedule_once(
                        lambda dt: self.deploymentComplition(
                            requests[1:], output=True), 1)
                    anim = Animation(
                        progress=self.progress + self.unit_progress,
                        t='linear', duration=.5)
                    anim.start(self)
        else:
            ok_but = Button(
                size=(100, 30), pos=(200, 150), text="[b]COMPLETE[/b]",
                background_color=get_color_from_hex('97BE0D'),
                switch_screen='action_screen')
            ok_but.bind(on_release=self.fast_switch_screen)
            self.current_screen.add_widget(ok_but)
            self.progress = 440
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
        cross_img = Image(
            source="assets/cross2.png", size=(20, 20), pos=(470, 370))
        cross_but = Button(
            size=(20, 20), pos=(470, 370), switch_screen='action_screen',
            background_color=get_color_from_hex('404248'))
        cross_but.add_widget(cross_img)
        cross_but.bind(on_release=self.fast_switch_screen)

        tryagain_but = Button(
            size=(100, 30), pos=(200, 150), text="[b]TRY AGAIN[/b]",
            background_color=get_color_from_hex('FFCC00'),
            switch_screen='action_screen',)
        tryagain_but.bind(on_release=self.fast_switch_screen)
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
                    self.display_message(
                        screen, u"at least check one server please!")()
                    self.display_error_buts_deployment()
                else:
                    requests = []
                    for server in self.checked_servers:
                        name = server.input_box.name_input.text.strip()
                        url = server.input_box.url_input.text.strip()
                        cmd = server.input_box.cmd_input.text.strip()
                        tmp = [
                            self.display_message(
                                screen, '%s authentication check' % name),
                            self.authentication_check(name, url),
                            self.display_message(
                                screen, '%s branch check' % self.branch),
                            self.branch_check(name, self.branch),
                            self.display_message(
                                screen, '%s command check' % cmd),
                            self.command_check(url, cmd)
                        ]
                        requests.extend(tmp)

                    for server in self.checked_servers:
                        name = server.input_box.name_input.text.strip()
                        url = server.input_box.url_input.text.strip()
                        cmd = server.input_box.cmd_input.text.strip()
                        requests.append(self.display_message(
                            screen, '%s deployment...' % name))
                        tmp_call = self.deploy_server(self.username,
                                                      self.password,
                                                      name, url, cmd,
                                                      self.branch)
                        requests.append(tmp_call)
                    requests.append(self.display_message(
                        screen,
                        "Deployment complete for branch; '%s'" % self.branch))
                    self.reset_progess()(len(requests))
                    self.deploymentComplition(requests, output=True)


class DeploymentApp(App):
    def __init__(self, *args, **kwargs):
        super(DeploymentApp, self).__init__(*args, **kwargs)
        Builder.load_file('%s/assets/style.kv' % PROJECT_PATH)

    def build(self):
        layout = Deployment()
        return layout


if __name__ == "__main__":
    """
    Window sizes and wanted skills are set, then app calls
    """
    Window.size = (500, 400)
    Window.clearcolor = (get_color_from_hex("1C1D20"))
    Window.borderless = False
    Config.set('kivy', 'desktop', 1)
    Config.set('kivy', 'exit_on_escape', 0)
    Config.set('graphics', 'fullscreen', 0)
    Config.set('graphics', 'resizable', 0)

    DeploymentApp().run()
