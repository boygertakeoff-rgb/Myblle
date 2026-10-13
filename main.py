# -*- coding: utf-8 -*-
"""
SISTEMA POS SAAS MOÇAMBIQUE - VERSÃO COMPLETA E UNIFICADA (WEB + MOBILE ANDROID)
Moeda: Meticais (MZN) | Arquitetura: Flask API + Kivy Mobile GUI
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

# =====================================================================
# 1. ATIVAÇÃO DO BANCO DE DADOS CENTRAL (SQLite)
# =====================================================================
DB_NAME = "central_corporate_cloud.db"

def inicializar_banco_dados():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de Filiais / Clientes SaaS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS filiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            localizacao TEXT,
            pacote TEXT,
            valor_mensalidade REAL,
            data_expiracao TEXT,
            estado_licenca TEXT
        )
    """)
    
    # Tabela de Utilizadores (Dono, Gerentes e Caixas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            perfil TEXT,
            filial_id INTEGER,
            FOREIGN KEY(filial_id) REFERENCES filiais(id)
        )
    """)
    
    # Tabela de Produtos (Isolamento por Filial)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT,
            nome TEXT,
            preco REAL,
            stock_atual INTEGER,
            stock_minimo INTEGER,
            filial_id INTEGER,
            FOREIGN KEY(filial_id) REFERENCES filiais(id)
        )
    """)
    
    # Tabela de Vendas / Transações Globais
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filial_id INTEGER,
            operador TEXT,
            total REAL,
            metodo_pagamento TEXT,
            data_hora TEXT,
            FOREIGN KEY(filial_id) REFERENCES filiais(id)
        )
    """)

    # Inserção de dados de simulação padrão (Se a BD estiver vazia)
    cursor.execute("SELECT COUNT(*) FROM filiais")
    if cursor.fetchone()[0] == 0:
        hoje = datetime.now()
        data_ativa = (hoje + timedelta(days=30)).strftime("%Y-%m-%d")
        data_expirada = (hoje - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Inserir Filiais de Teste com os Pacotes em MZN acordados
        cursor.execute("INSERT INTO filiais VALUES (1, 'Maputo Sede', 'Av. Julius Nyerere', '1 Loja', 1000.0, ?, 'Ativa')", (data_ativa,))
        cursor.execute("INSERT INTO filiais VALUES (2, 'Beira Filial', 'Av. Samora Machel', '3 a 4 Lojas', 3500.0, ?, 'Expirada')", (data_expirada,))
        cursor.execute("INSERT INTO filiais VALUES (3, 'Supermercado Nampula', 'Av. Eduardo Mondlane', 'Supermercado', 10000.0, ?, 'Ativa')", (data_ativa,))
        
        # Inserir Utilizadores
        cursor.execute("INSERT INTO utilizadores VALUES (1, 'admin', 'admin', 'Dono', 1)")
        cursor.execute("INSERT INTO utilizadores VALUES (2, 'gerente', 'gerente123', 'Gerente', 1)")
        cursor.execute("INSERT INTO utilizadores VALUES (3, 'caixa1', '1234', 'Caixa', 1)")
        cursor.execute("INSERT INTO utilizadores VALUES (4, 'caixa2', '1234', 'Caixa', 2)")
        
        # Inserir Produtos em Meticais
        cursor.execute("INSERT INTO produtos VALUES (1, '1111', 'Arroz Nacional 1kg', 75.0, 150, 30, 1)")
        cursor.execute("INSERT INTO produtos VALUES (2, '2222', 'Oleo de Cozinha 1L', 130.0, 80, 20, 1)")
        cursor.execute("INSERT INTO produtos VALUES (3, '3333', 'Farinha de Milho 1kg', 55.0, 12, 25, 1)") # Stock baixo para IA acusar
        
    conn.commit()
    conn.close()

# =====================================================================
# 2. ESCRITA AUTOMÁTICA DO FICHEIRO BUILDOZER.SPEC (Android Compilação)
# =====================================================================
def gerar_buildozer_spec():
    conteudo_spec = """[app]
title = Mocambique POS SaaS
package.name = mzpos_saas
package.domain = co.mz.pos
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 1.0.0
requirements = python3,kivy,sqlite3,requests,reportlab,matplotlib

# Permissões do Ecossistema Android para Hardware Comercial
android.permissions = CAMERA, BLUETOOTH, BLUETOOTH_ADMIN, INTERNET, WRITE_EXTERNAL_STORAGE

orientation = landscape
fullscreen = 1
android.archs = armeabi-v7a, arm64-v8a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
"""
    with open("buildozer.spec", "w", encoding="utf-8") as f:
        f.write(conteudo_spec)
    print("[BUILDOZER] Ficheiro 'buildozer.spec' gerado com sucesso para compilação .APK.")

# =====================================================================
# 3. PILAR WEB CENTRAL: SERVIDOR API (Flask)
# =====================================================================
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/login', methods=['POST'])
def api_login():
    dados = request.json or {}
    utilizador = dados.get("utilizador")
    senha = dados.get("senha")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.perfil, f.nome, f.data_expiracao, f.estado_licenca, f.id 
        FROM utilizadores u 
        JOIN filiais f ON u.filial_id = f.id 
        WHERE u.username=? AND u.password=?
    """, (utilizador, senha))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        perfil, filial_nome, data_exp, estado, filial_id = user
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        # Bloqueio Crítico de Mensalidade SaaS
        if hoje > data_exp or estado == 'Expirada':
            return jsonify({
                "status": "bloqueado", 
                "mensagem": "Acesso Bloqueado: Mensalidade em Atraso de Meticais! Contacte o Dono do Software."
            }), 403
            
        return jsonify({
            "status": "sucesso", "perfil": perfil, "filial": filial_nome, "filial_id": filial_id
        })
    return jsonify({"status": "erro", "mensagem": "Credenciais Inválidas em Moçambique."}), 401

@app.route('/api/caixa/venda', methods=['POST'])
def registar_venda_api():
    dados = request.json or {}
    filial_id = dados.get("filial_id")
    operador = dados.get("operador")
    total = dados.get("total")
    metodo = dados.get("metodo_pagamento") # M-Pesa, e-Mola, Dinheiro, POS
    itens = dados.get("itens", [])
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO vendas (filial_id, operador, total, metodo_pagamento, data_hora) VALUES (?, ?, ?, ?, ?)",
                   (filial_id, operador, total, metodo, agora))
    
    # Abate de stock por artigo vendido na filial
    for item in itens:
        prod_id = item.get("produto_id")
        qtd = item.get("quantidade")
        cursor.execute("UPDATE produtos SET stock_atual = stock_atual - ? WHERE id = ? AND filial_id = ?", 
                       (qtd, prod_id, filial_id))
        
    conn.commit()
    conn.close()
    return jsonify({"status": "sucesso", "mensagem": "Venda integrada e armazenada na nuvem."})

@app.route('/api/admin/mensalidades', methods=['GET'])
def listar_mensalidades():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, pacote, valor_mensalidade, data_expiracao, estado_licenca FROM filiais")
    lojas = cursor.fetchall()
    conn.close()
    
    resultado = []
    for loja in lojas:
        resultado.append({
            "loja": loja[0], "pacote": loja[1], "mensalidade": f"{loja[2]:,.2f} MT", "expira": loja[3], "estado": loja[4]
        })
    return jsonify(resultado)

# =====================================================================
# 4. PILAR MOBILE TÁTIL: INTERFACE GRÁFICA (Kivy)
# =====================================================================
# Condicional para permitir rodar o servidor headless em VPS ou abrir a GUI localmente
try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.textinput import TextInput
    KIVY_LOADED = True
except ImportError:
    KIVY_LOADED = False

if KIVY_LOADED:
    class FrenteCaixaKivy(BoxLayout):
        def __init__(self, **kwargs):
            super().__init__(orientation='vertical', padding=15, spacing=10, **kwargs)
            
            # Cabeçalho do Terminal Android
            self.add_widget(Label(text="MZN MOBILE POS - FRENTE DE CAIXA TÁTIL", size_hint_y=0.1, font_size=20))
            
            # Corpo Principal dividido em duas secções (Produtos à esquerda, Carrinho à direita)
            corpo = BoxLayout(orientation='horizontal', spacing=15)
            
            # Grelha Tátil de Artigos (Esquerda)
            grelha_esquerda = BoxLayout(orientation='vertical', size_hint_x=0.6)
            grelha_esquerda.add_widget(Label(text="Catálogo de Artigos (Toque para Adicionar)", size_hint_y=0.1))
            
            self.grelha_produtos = GridLayout(cols=2, spacing=10)
            self.carregar_catalogo_loja()
            grelha_esquerda.add_widget(self.grelha_produtos)
            
            # Painel do Carrinho e Caixa de Texto (Direita)
            painel_direito = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=10)
            self.lbl_carrinho = Label(text="Carrinho de Compras Vazio\n\nTotal: 0.00 MT", font_size=18, halign='center')
            painel_direito.add_widget(self.lbl_carrinho)
            
            # Métodos de Pagamento Nacionais Rápidos
