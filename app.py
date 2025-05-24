from flask import Flask, request, jsonify, send_file
import mysql.connector
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import datetime
import os

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

@app.route("/utentes/<id>", methods=["GET"])
def get_utente(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, ultquota, foto FROM tbl_utentes WHERE id = %s", (id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            "nome": row[0],
            "ultquota": str(row[1]) if row[1] else "",
            "foto": row[2]
        })
    return jsonify({"error": "Utente não encontrado"}), 404

@app.route("/recibos/<socio_id>", methods=["GET"])
def get_recibos(socio_id):
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

    recibos = [dict(
        data=str(r[0]),
        tipo=r[1],
        valor=f"{r[2]:.2f}",
        comentario=r[3] or ""
    ) for r in rows]

    return jsonify(recibos)

@app.route("/valor_unit", methods=["GET"])
def get_valor_unit():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM tbl_tipo WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"valor_unit": float(row[0])})
    return jsonify({"error": "Não encontrado"}), 404

@app.route("/ficha/<id>", methods=["GET"])
def gerar_pdf(id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT nome, ultquota FROM tbl_utentes WHERE id = %s", (id,))
    utente = cursor.fetchone()
    if not utente:
        return jsonify({"erro": "Utente não encontrado"}), 404

    nome, ultquota = utente

    # Trata a data da última quota
    try:
        ultquota_date = datetime.datetime.strptime(str(ultquota), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        ultquota_date = datetime.date(2007, 1, 1)

    hoje = datetime.date.today()
    meses_em_divida = max((hoje.year - ultquota_date.year) * 12 + (hoje.month - ultquota_date.month), 0)

    cursor.execute("SELECT valor FROM tbl_tipo WHERE id = 1")
    valor_row = cursor.fetchone()
    valor_unit = valor_row[0] if valor_row else 0.0

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

    # Gerar PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, f"Ficha do Utente: {nome}")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 80, f"Última Quota: {ultquota_date}")
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

if __name__ == "__main__":
    app.run(debug=True)

