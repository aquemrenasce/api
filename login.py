from kivy.uix.screenmanager import Screen
from database import Database

class LoginScreen(Screen):
    tentativas = 0

    def check_login(self):
        usuario = self.ids.txt_user.text.upper()
        senha = self.ids.txt_password.text

        db = Database()
        conn = db.conecta()
        if not conn:
            self.ids.lbl_status.text = "Erro de conexão"
            return

        nivel = db.check_user(usuario, senha)

        if nivel and nivel in ["1", "2", "3", "4"]:
            # 👇 Guarda o ID do sócio no MainScreen
            main_screen = self.manager.get_screen("main")
            main_screen.socio_id = usuario  # passa o socionum real

            self.manager.current = "main"
        else:
            self.tentativas += 1
            if self.tentativas >= 3:
                exit()
            else:
                self.ids.lbl_status.text = f"Tentativa {self.tentativas}/3 inválida."
