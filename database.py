import mysql.connector

class Database:
    def __init__(self):
        self.connection = None

    def conecta(self):
        try:
            self.connection = mysql.connector.connect(
                host="aquemrenasce.pt",
                port=3306,
                user="aquemrenasce",
                password="Aqu3mr3n@sc3",
                database="aquemrenasce_ardb"
            )
            return self.connection
        except Exception as e:
            print("Erro ao conectar:", e)
            return None

    def check_user(self, usuario, senha):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT nivel FROM tbl_user WHERE UPPER(socionum) = %s AND passatual = %s
            """, (usuario, senha))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print("Erro ao verificar usuário:", e)
            return None
