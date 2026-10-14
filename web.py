from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os, json, datetime

app = Flask(__name__)
CORS(app)

# Banco simples em arquivo
DB_FILE = "myblle_db.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"produtos": [], "vendas": []}, f)

def get_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data.get("user") == "admin" and data.get("pass") == "myblle123":
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 401

@app.route('/api/produtos', methods=['GET', 'POST'])
def produtos():
    db = get_db()
    if request.method == 'POST':
        p = request.json
        p["id"] = len(db["produtos"])+1
        db["produtos"].append(p)
        save_db(db)
        return jsonify(p)
    return jsonify(db["produtos"])

@app.route('/api/vendas', methods=['POST'])
def vendas():
    db = get_db()
    venda = request.json
    venda["data"] = str(datetime.datetime.now())
    venda["id"] = len(db["vendas"])+1
    db["vendas"].append(venda)
    save_db(db)
    return jsonify({"ok": True, "id": venda["id"]})

@app.route('/api/status')
def status():
    db = get_db()
    total = sum(v["total"] for v in db["vendas"])
    return jsonify({"filiais":3, "vendas_hoje": total, "total_vendas": len(db["vendas"])})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
