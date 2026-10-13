# -*- coding: utf-8 -*-
# SISTEMA POS SAAS MOÇAMBIQUE - VERSÃO WEB
import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- BANCO: Usa Postgres se tiver DATABASE_URL, se não SQLite ---
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = DATABASE_URL is not None

def get_conn():
    if USE_POSTGRES:
        import psycopg2
        # Render usa postgres:// mas precisa de postgresql://
        url = DATABASE_URL.replace("postgres://", "postgresql://")
        return psycopg2.connect(url)
    else:
        return sqlite3.connect("central_corporate_cloud.db")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # Suas tabelas originais
    cur.execute("""
    CREATE TABLE IF NOT EXISTS filiais (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        localizacao TEXT,
        pacote TEXT,
        valor_mensal REAL,
        data_expiracao TEXT,
        estado_licenca TEXT
    )""".replace("SERIAL", "INTEGER PRIMARY KEY AUTOINCREMENT" if not USE_POSTGRES else "SERIAL"))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS utilizadores (
        id SERIAL PRIMARY KEY,
        filial_id INTEGER,
        nome TEXT,
        utilizador TEXT UNIQUE,
        senha TEXT,
        perfil TEXT
    )""".replace("SERIAL", "INTEGER PRIMARY KEY AUTOINCREMENT" if not USE_POSTGRES else "SERIAL"))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id SERIAL PRIMARY KEY,
        filial_id INTEGER,
        nome TEXT,
        codigo_barras TEXT,
        preco REAL,
        stock INTEGER
    )""".replace("SERIAL", "INTEGER PRIMARY KEY AUTOINCREMENT" if not USE_POSTGRES else "SERIAL"))

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return jsonify({
        "app": "Myblle POS SaaS",
        "status": "online",
        "versao": "Moçambique MZN",
        "web": "OK",
        "android": "Use main.py com Buildozer",
        "endpoints": ["/api/filiais", "/api/produtos", "/api/login"]
    })

@app.route('/api/filiais')
def listar_filiais():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, pacote, estado_licenca FROM filiais")
    filiais = cur.fetchall()
    conn.close()
    return jsonify([{"id": f[0], "nome": f[1], "pacote": f[2], "estado": f[3]} for f in filiais])

@app.route('/api/produtos')
def listar_produtos():
    filial_id = request.args.get('filial_id', 1)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, preco, stock FROM produtos WHERE filial_id=%s" if USE_POSTGRES else "SELECT id, nome, preco, stock FROM produtos WHERE filial_id=?", (filial_id,))
    prods = cur.fetchall()
    conn.close()
    return jsonify([{"id": p[0], "nome": p[1], "preco": p[2], "stock": p[3]} for p in prods])

@app.route('/api/login', methods=['POST'])
def login():
    dados = request.get_json()
    utilizador = dados.get('utilizador')
    senha = dados.get('senha')
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, perfil, filial_id FROM utilizadores WHERE utilizador=%s AND senha=%s" if USE_POSTGRES else "SELECT id, nome, perfil, filial_id FROM utilizadores WHERE utilizador=? AND senha=?", (utilizador, senha))
    user = cur.fetchone()
    conn.close()
    if user:
        return jsonify({"sucesso": True, "user": {"id": user[0], "nome": user[1], "perfil": user[2], "filial_id": user[3]}})
    return jsonify({"sucesso": False, "mensagem": "Utilizador não encontrado"}), 401

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
