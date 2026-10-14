from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

USUARIOS = {
    "admin": {"senha": "myblle123", "cargo": "admin", "nome": "Administrador"},
    "caixa": {"senha": "caixa123", "cargo": "caixa", "nome": "Caixa Nampula"},
    "caixa1": {"senha": "123", "cargo": "caixa", "nome": "Caixa 1"}
}

produtos = []
vendas = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = data.get("user","").strip()
        pwd = str(data.get("pass","")).strip()
        print(f"Login tentado: {user}")
        if user in USUARIOS and USUARIOS[user]["senha"] == pwd:
            u = USUARIOS[user]
            return jsonify({"ok": True, "cargo": u["cargo"], "nome": u["nome"], "user": user})
        return jsonify({"ok": False, "erro": "usuario ou senha"}), 401
    except Exception as e:
        print(f"ERRO LOGIN: {e}")
        return jsonify({"ok": False, "erro": str(e)}), 500

@app.route('/api/produtos', methods=['GET','POST'])
def prod():
    global produtos
    if request.method == 'POST':
        p = request.get_json()
        p["id"] = len(produtos)+1
        produtos.append(p)
        return jsonify(p)
    return jsonify(produtos)

@app.route('/api/vendas', methods=['POST'])
def vend():
    global vendas
    v = request.get_json()
    vendas.append(v)
    return jsonify({"ok": True})

@app.route('/api/status')
def status():
    total = sum(v.get("total",0) for v in vendas)
    return jsonify({"filiais":3, "vendas_hoje": total, "total_vendas": len(vendas)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
