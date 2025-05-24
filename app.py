from flask import Flask, request, jsonify, send_file
import mysql.connector
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import datetime

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "aquemrenasce.pt"),
        user=os.environ.get("DB_USER", "aquemrenasce"),
        password=os.environ.get("DB_PASSWORD", "Aqu3mr3n@sc3"),
        database=os.environ.get("DB_NAME", "aquemrenasce_ardb"),
        port=int(os.environ.get("DB_PORT", 3306))
    )

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        socionum = data.get("user", "").upper()
        passwd = data.get("password")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT nivel FROM tbl_user WHERE UPPER(socionum) = %s AND passatual = %s", (socionum, passwd))
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify({"status": "ok", "nivel": row[0]})
        return jsonify({"status": "error", "msg": "Credenciais inválidas"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/utentes/<id>", methods=["GET"])
def get_utente(id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, ultquota, foto FROM tbl_utentes WHERE id = %s", (id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify({"nome": row[0], "ultquota": str(row[1]), "foto": row[2]})
        return jsonify({"error": "Utente não encontrado"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/recibos/<socio_id>", methods=["GET"])
def get_recibos(socio_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rd.data_recibo_det, tt.tipo, rd.subtotal, rd.comentario
            FROM tbl_recibodet rd
            LEFT JOIN tbl_tipo tt ON rd.tipo = tt.id
            WHERE rd.socio = %s
            ORDER BY rd.data_recibo_det DESC
        """, (socio_id,))
        rows = cursor.fetchall()
        conn.close()

        recibos = [{
            "data": str(r[0]),
            "tipo": r[1],
            "valor": f"{r[2]:.2f}",
            "comentario": r[3] or ""
        } for r in rows]

        return jsonify(recibos)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/valor_unit", methods=["GET"])
def get_valor_unit():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM tbl_tipo WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify({"valor_unit": float(row[0])})
        return jsonify({"error": "Não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/ficha/<id>", methods=["GET"])
def gerar_pdf(id):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT nome, ultquota FROM tbl_utentes WHERE id = %s", (id,))
        utente = cursor.fetchone()
        if not utente:
            return jsonify({"erro": "Utente não encontrado"}), 404

        nome, ultquota = utente
        if not ultquota:
            ultquota = datetime.date(2007, 1, 1)
        else:
            ultquota = datetime.datetime.strptime(str(ultquota), "%Y-%m-%d").date()

        hoje = datetime.date.today()
        meses_em_divida = max((hoje.year - ultquota.year) * 12 + (hoje.month - ultquota.month), 0)

        cursor.execute("SELECT valor FROM tbl_tipo WHERE id = 1")
        row = cursor.fetchone()
        valor_unit = float(row[0]) if row else 0.0
        total = meses_em_divida * valor_unit

        cursor.execute("""
            SELECT rd.data_recibo_det, tt.tipo, rd.subtotal, rd.comentario
            FROM tbl_recibodet rd
            LEFT JOIN tbl_tipo tt ON rd.tipo = tt.id
            WHERE rd.socio = %s
            ORDER BY rd.data_recibo_det DESC
        """, (id,))
        recibos = cursor.fetchall()
        conn.close()

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, height - 50, f"Ficha do Utente: {nome}")

        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, height - 80, f"Última Quota: {ultquota}")
        pdf.drawString(50, height - 100, f"Meses em Dívida: {meses_em_divida}")
        pdf.drawString(50, height - 120, f"Total a Pagar: {total:.2f} €")

        y = height - 160
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Recibos:")
        y -= 20

        pdf.setFont("Helvetica", 10)
        for r in recibos:
            linha = f"{r[0]} | {r[1]} | {r[2]:.2f} € | {r[3] or ''}"
            pdf.drawString(50, y, linha)
            y -= 15
            if y < 50:
                pdf.showPage()
                y = height - 50

        pdf.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="ficha.pdf", mimetype="application/pdf")

    except Exception as e:
        print("Erro ao gerar PDF:", e)
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
