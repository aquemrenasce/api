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
    data = request.get_json()
    user = data.get("user", "").upper()
    password = data.get("password")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT nivel FROM tbl_user WHERE UPPER(socionum)=%s AND passatual=%s", (user, password))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({"status": "ok", "nivel": row[0]})
    return jsonify({"status": "error", "msg": "Credenciais inválidas"})

@app.route("/utentes/<id>", methods=["GET"])
def get_utente(id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, ultquota, foto FROM tbl_utentes WHERE id=%s", (id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "Utente não encontrado"}), 404

        nome, ultquota, foto = row
        if not ultquota:
            ultquota = datetime.date(2000, 1, 1)
        else:
            ultquota = datetime.datetime.strptime(str(ultquota), "%Y-%m-%d").date()

        hoje = datetime.date.today()
        meses_em_falta = max((hoje.year - ultquota.year) * 12 + (hoje.month - ultquota.month), 0)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT valor_unit FROM tbl_tipo WHERE id=1")
        valor_unit = cursor.fetchone()[0] or 0
        conn.close()
        total = meses_em_falta * float(valor_unit)

        return jsonify({
            "nome": nome,
            "ultquota": str(ultquota),
            "foto": foto,
            "meses_em_falta": meses_em_falta,
            "total": round(total, 2)
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/quotas/<socio_id>", methods=["GET"])
def get_quotas(socio_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rd.id, rd.data_recibo_det, tt.tipo, rd.subtotal, rd.comentario
        FROM tbl_recibodet rd
        LEFT JOIN tbl_tipo tt ON rd.tipo = tt.id
        WHERE rd.socio = %s AND rd.tipo = 1  -- Apenas registos do tipo 1 (quota)
        ORDER BY rd.data_recibo_det DESC
    """, (socio_id,))
    rows = cursor.fetchall()
    conn.close()
    quotas = [{
        "id": r[0],
        "data": str(r[1])[:10],
        "tipo": r[2],
        "valor": f"{r[3]:.2f}",
        "comentario": r[4] or ""
    } for r in rows]
    return jsonify(quotas)

@app.route("/recibos_pendentes/<socio_id>", methods=["GET"])
def get_recibos_pendentes(socio_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rd.id, rd.data_recibo_det, tt.tipo, rd.subtotal, rd.vpago, rd.comentario
        FROM tbl_recibodet rd
        LEFT JOIN tbl_tipo tt ON rd.tipo = tt.id
        WHERE rd.socio = %s AND rd.subtotal > rd.vpago  -- Apenas recibos onde subtotal > vpago
        ORDER BY rd.data_recibo_det DESC
    """, (socio_id,))
    rows = cursor.fetchall()
    conn.close()
    pendentes = [{
        "id": r[0],
        "data": str(r[1])[:10],
        "tipo": r[2],
        "subtotal": f"{r[3]:.2f}",
        "vpago": f"{r[4]:.2f}",
        "comentario": r[5] or ""
    } for r in rows]
    return jsonify(pendentes)

if __name__ == "__main__":
    app.run(debug=True)
