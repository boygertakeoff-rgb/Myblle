import os, sqlite3, uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, session, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "myblle_v3_2024"
app.config['UPLOAD_FOLDER'] = 'static/produtos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

USUARIOS = {
    "admin": {"senha": "myblle123", "papel": "gerente", "loja": "Todas"},
    "gerente": {"senha": "gerente123", "papel": "gerente", "loja": "Matola"},
    "caixa": {"senha": "caixa123", "papel": "operador", "loja": "Matola"},
    "operador": {"senha": "op123", "papel": "operador", "loja": "Maputo"}
}

def init_db():
    conn = sqlite3.connect('mzn_pos.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT, preco REAL, stock INTEGER, categoria TEXT, codigo_barras TEXT, imagem TEXT, loja TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY, produto_id INTEGER, produto_nome TEXT, qtd INTEGER, total REAL, data TEXT, loja TEXT, vendedor TEXT)')
    conn.commit()
    conn.close()

init_db()

# ... COLA AQUI O RESTO DO CÓDIGO V3 QUE TE MANDEI ANTES (LOGIN_HTML, GERENTE_HTML, OPERADOR_HTML e todas as rotas /api/ ) ...
# IMPORTANTE: no final do arquivo deixa SÓ isso:

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
