from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty
from database import Database
from urllib.request import urlopen
from kivy.core.image import Image as CoreImage
from datetime import date
from dateutil.relativedelta import relativedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io
import os
import webbrowser

class MainScreen(Screen):
    socio_id = StringProperty("")
    nome = StringProperty("")
    total_quota = StringProperty("")
    meses_em_divida = StringProperty("")
    recibos = ListProperty([])

    def on_pre_enter(self):
        if not self.socio_id:
            print("ID de sócio não definido.")
            return

        self.carregar_nome_usuario()
        self.carregar_dados_recibos()

    def carregar_nome_usuario(self):
        try:
            db = Database()
            conn = db.conecta()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nome, ultquota, foto FROM tbl_utentes WHERE id = %s
            """, (self.socio_id,))
            result = cursor.fetchone()

            if not result:
                self.nome = "Utente não encontrado"
                return

            nome, ultquota, foto = result
            self.nome = nome

            hoje = date.today()
            if not ultquota or str(ultquota).strip() == "":
                ultquota = date(2007, 1, 1)

            if ultquota >= hoje:
                meses = 0
            else:
                diff = relativedelta(hoje, ultquota)
                meses = diff.years * 12 + diff.months

            self.meses_em_divida = str(meses)

            cursor.execute("SELECT valor_unit FROM tbl_tipo WHERE id = 1")
            valor = cursor.fetchone()
            if valor:
                total = valor[0] * meses
                self.total_quota = f"{total:.2f}"
            else:
                self.total_quota = "0.00"

            if foto:
                try:
                    url = f"https://aquemrenasce.pt/imagens/{foto or '000.png'}"
                    raw_data = urlopen(url).read()
                    data = io.BytesIO(raw_data)
                    img = CoreImage(data, ext="png").texture
                    self.ids.img_foto.texture = img
                except Exception as e:
                    print("Erro ao carregar imagem:", e)

        except Exception as e:
            print("Erro ao carregar utente:", e)

    def carregar_dados_recibos(self):
        try:
            db = Database()
            conn = db.conecta()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT rd.data_recibo_det, tt.tipo, rd.subtotal, rd.comentario
                FROM tbl_recibodet rd
                LEFT JOIN tbl_tipo tt ON rd.tipo = tt.id
                WHERE rd.socio = %s
                ORDER BY rd.data_recibo_det DESC
            """, (self.socio_id,))
            rows = cursor.fetchall()

            self.recibos = [dict(
                data=str(row[0]),
                tipo=row[1],
                valor=f"{row[2]:.2f}€",
                comentario=row[3] or ""
            ) for row in rows]

        except Exception as e:
            print("Erro ao carregar recibos:", e)

    def imprimir_ficha_pdf(self):
        try:
            filename_pdf = f"ficha_{self.socio_id}.pdf"
            doc = SimpleDocTemplate(filename_pdf, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            elements.append(Paragraph(f"<b>Ficha do Utente:</b> {self.nome}", styles["Title"]))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"<b>Meses em dívida:</b> {self.meses_em_divida}", styles["Normal"]))
            elements.append(Paragraph(f"<b>Total a pagar:</b> {self.total_quota} €", styles["Normal"]))
            elements.append(Spacer(1, 20))

            if self.recibos:
                table_data = [["Data", "Tipo", "Valor", "Comentário"]]
                for item in self.recibos:
                    table_data.append([
                        item['data'],
                        item['tipo'],
                        item['valor'],
                        item['comentario']
                    ])

                table = Table(table_data, colWidths=[80, 120, 60, 180])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                elements.append(table)
            else:
                elements.append(Paragraph("Nenhum recibo disponível.", styles["Italic"]))

            doc.build(elements)
            webbrowser.open(os.path.abspath(filename_pdf))

        except Exception as e:
            print("Erro ao gerar PDF:", e)

