
from flask import Flask, request, jsonify
import mysql.connector
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
        return jsonify({"nome": row[0], "ultquota": str(row[1]), "foto": row[2]})
    return jsonify({"error": "Utente não encontrado"})

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

    recibos = [{
        "data": str(r[0]),
        "tipo": r[1],
        "valor": f"{r[2]:.2f}",
        "comentario": r[3] or ""
    } for r in rows]

    return jsonify(recibos)

@app.route("/valor_unit", methods=["GET"])
def get_valor_unit():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT valor_unit FROM tbl_tipo WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"valor_unit": float(row[0])})
    return jsonify({"error": "Não encontrado"}), 404

if __name__ == "__main__":
    app.run(debug=True)
