from flask import Flask, request, jsonify
import mysql.connector
import os
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

@app.route("/quotas/<socio_id>", methods=["GET"])
def get_quotas(socio_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT rd.data_recibo_det, tt.tipo, rd.subtotal, rd.comentario
            FROM tbl_recibodet rd
            LEFT JOIN tbl_tipo tt ON rd.tipo = tt.id
            WHERE rd.socio = %s AND rd.tipo = 1
            ORDER BY rd.data_recibo_det DESC
        """, (socio_id,))
        rows = cursor.fetchall()
        conn.close()

        quotas = [
            {"data": str(r[0]), "tipo": r[1], "valor": f"{r[2]:.2f}", "comentario": r[3] or ""}
            for r in rows
        ]
        return jsonify(quotas)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/recibos_pendentes/<socio_id>", methods=["GET"])
def get_recibos_pendentes(socio_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT rd.data_recibo_det, tt.tipo, rd.subtotal, rd.vpago, rd.comentario
            FROM tbl_recibodet rd
            LEFT JOIN tbl_tipo tt ON rd.tipo = tt.id
            WHERE rd.socio = %s AND rd.subtotal > rd.vpago
            ORDER BY rd.data_recibo_det DESC
        """, (socio_id,))
        rows = cursor.fetchall()
        conn.close()

        pendentes = [
            {
                "data": str(r[0]),
                "tipo": r[1],
                "valor": f"{r[2]:.2f} / {r[3]:.2f}",
                "comentario": r[4] or ""
            }
            for r in rows
        ]
        return jsonify(pendentes)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
