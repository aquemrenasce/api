import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from login import LoginScreen
from screens.main_screen import MainScreen

# Carregar arquivos KV
Builder.load_file("login.kv")
Builder.load_file("main.kv")

class MainApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))
        return sm

if __name__ == '__main__':
    MainApp().run()
