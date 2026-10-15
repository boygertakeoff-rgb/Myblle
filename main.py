import os, sqlite3, uuid, sys
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, session, redirect

app = Flask(__name__)
app.secret_key = "mzn_pos_v3_matola_2024"
app.config['UPLOAD_FOLDER'] = 'static/produtos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

USUARIOS = {
    "admin": {"senha": "myblle123", "papel": "gerente", "loja": "Todas"},
    "gerente": {"senha": "gerente123", "papel": "gerente", "loja": "Matola"},
    "caixa": {"senha": "caixa123", "papel": "operador", "loja": "Matola"},
    "operador": {"senha": "op123", "papel": "operador", "loja": "Maputo"}
}

def inicializar_banco_dados():
    conn = sqlite3.connect('mzn_pos.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY, nome TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produtos
        (id INTEGER PRIMARY KEY, nome TEXT, preco REAL, stock INTEGER,
         categoria TEXT, codigo_barras TEXT UNIQUE, imagem TEXT, loja TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS vendas
        (id INTEGER PRIMARY KEY, produto_id INTEGER, produto_nome TEXT, qtd INTEGER, total REAL, data TEXT, loja TEXT, vendedor TEXT)''')
    for cat in ["Polos", "Camisas", "T-Shirts", "Calças", "Acessórios"]:
        try: c.execute("INSERT INTO categorias (nome) VALUES (?)", (cat,))
        except: pass
    conn.commit()
    conn.close()

def gerar_buildozer_spec(): return True

LOGIN_HTML = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="font-family:Arial;padding:30px;background:#0e0e0e;color:white">
<h2>🔒 MZN POS - myblle</h2>
<p>Matola | Maputo | Porto</p>
<form method="POST">
<input name="user" placeholder="Usuário" required style="width:100%;padding:14px;border-radius:8px;margin-top:10px">
<input name="senha" type="password" placeholder="Senha" required style="width:100%;padding:14px;border-radius:8px;margin-top:10px">
<button style="width:100%;padding:14px;background:#1a8a1a;color:white;border:none;border-radius:8px;margin-top:15px;font-weight:bold">ENTRAR</button>
</form>
<div style="margin-top:30px;background:#222;padding:15px;border-radius:10px;font-size:13px">
<b>Teste:</b><br>👔 Gerente: admin / myblle123 (vê tudo)<br>💵 Caixa: caixa / caixa123 (só vende)
</div>
</body></html>
"""

GERENTE_HTML = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;padding:10px;background:#f4f4f4}.card{background:white;padding:15px;border-radius:12px;margin-bottom:10px} input,select,button{width:100%;padding:12px;margin:5px 0;border-radius:8px;border:1px solid #ccc} button{background:#1a8a1a;color:white;font-weight:bold;border:none}.prod{display:flex;gap:10px;align-items:center}.prod img{width:60px;height:60px;object-fit:cover;border-radius:8px}</style>
</head><body>
<div style="display:flex;justify-content:space-between"><b>👔 GERENTE: {{user}}</b><a href='/logout'>Sair</a></div>
<div class="card" style="background:#0a5c0a;color:white"><div>Vendas HOJE - Tempo Real</div><h1 id="totalDia">MZN 0.00</h1><div id="qtdDia">0 vendas</div><div id="hora"></div></div>
<div class="card"><h3>📊 Relatório Detalhado Hoje</h3><div id="relatorio"></div><button onclick="relatorio()">🔄 Atualizar Relatório</button></div>
<div class="card"><h3>➕ Cadastro Produto (com imagem, categoria, barras)</h3>
<form id="formProd" enctype="multipart/form-data">
<input name="nome" placeholder="Nome" required><input name="preco" type="number" step="0.01" placeholder="Preço MZN" required>
<input name="stock" type="number" placeholder="Stock" required><select name="categoria" id="selCat"></select>
<input name="codigo_barras" placeholder="Código de Barras" required><select name="loja"><option>Matola</option><option>Maputo</option><option>Porto</option></select>
<input name="imagem" type="file" accept="image/*" required><button type="submit">SALVAR PRODUTO</button>
</form></div>
<div class="card"><h3>🔍 Pesquisar & Vender</h3><input id="busca" placeholder="Nome, categoria ou código de barras..." onkeyup="pesquisar()"><div id="listaProdutos"></div></div>
<script>
async function carregar(){let r=await fetch('/api/produtos');let p=await r.json();document.getElementById('listaProdutos').innerHTML=p.map(x=>`<div class="prod card"><img src="/${x[6]}" onerror="this.src='https://via.placeholder.com/60'"><div><b>${x[1]}</b><br>${x[4]} | ${x[5]} | Stock:${x[3]}<br>MZN ${x[2]}</div><button onclick="vender(${x[0]})" style="width:auto">VENDER</button></div>`).join('');let r2=await fetch('/api/categorias');let c=await r2.json();document.getElementById('selCat').innerHTML=c.map(y=>`<option>${y[1]}</option>`).join('');relatorio();setInterval(()=>{document.getElementById('hora').innerText=new Date().toLocaleString()},1000);}
async function pesquisar(){let q=document.getElementById('busca').value;let r=await fetch('/api/search?q='+q);let p=await r.json();document.getElementById('listaProdutos').innerHTML=p.map(x=>`<div class="prod card"><img src="/${x[6]}"><div><b>${x[1]}</b><br>${x[4]} | ${x[5]}</div><button onclick="vender(${x[0]})" style="width:auto">VENDER</button></div>`).join('');}
async function relatorio(){let r=await fetch('/api/relatorio_hoje');let d=await r.json();document.getElementById('totalDia').innerText='MZN '+d.total.toFixed(2);document.getElementById('qtdDia').innerText=d.qtd+' vendas hoje';document.getElementById('relatorio').innerHTML=d.vendas.map(v=>`#${v[0]} ${v[2]} (${v[5]}x) MZN ${v[4]} - ${v[6]} - ${v[7]}`).join('<br>')||'Sem vendas';}
async function vender(id){let qtd=prompt("Qtd:","1");if(!qtd)return;await fetch('/api/vender',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,qtd})});alert("Venda feita!");carregar();}
document.getElementById('formProd').onsubmit=async(e)=>{e.preventDefault();let fd=new FormData(e.target);let r=await fetch('/api/produtos',{method:'POST',body:fd});let j=await r.json();alert(j.msg);e.target.reset();carregar();};carregar();
</script></body></html>
"""

OPERADOR_HTML = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;padding:10px;background:#fff}.card{background:#f9f9f9;padding:15px;border-radius:12px;margin-bottom:10px;border:1px solid #eee} input,button{width:100%;padding:14px;margin:5px 0;border-radius:8px;border:1px solid #ccc} button{background:#0a5c0a;color:white;font-weight:bold}.prod{display:flex;gap:10px;align-items:center}.prod img{width:60px;height:60px;object-fit:cover;border-radius:8px}</style>
</head><body>
<div style="display:flex;justify-content:space-between"><b>💵 CAIXA: {{user}} - {{loja}}</b><a href='/logout'>Sair</a></div>
<h2>Ponto de Venda</h2>
<div class="card"><h3>📷 Ler Código de Barras</h3><input id="busca" placeholder="Bipe o código aqui ou digite nome..." onkeyup="pesquisar()" style="font-size:18px"><div id="listaProdutos"></div></div>
<div class="card"><h4>🧾 Minhas Vendas Hoje</h4><div id="minhasVendas"></div><button onclick="minhas()">Atualizar</button></div>
<p style="font-size:11px;color:red;text-align:center">Você NÃO tem acesso ao relatório total, cadastro e stock geral.</p>
<script>
async function pesquisar(){let q=document.getElementById('busca').value;if(q.length<1){document.getElementById('listaProdutos').innerHTML='';return;}let r=await fetch('/api/search?q='+q);let p=await r.json();document.getElementById('listaProdutos').innerHTML=p.map(x=>`<div class="prod card"><img src="/${x[6]}" onerror="this.src='https://via.placeholder.com/60'"><div><b>${x[1]}</b><br>MZN ${x[2]} | Stock:${x[3]}</div><button onclick="vender(${x[0]})" style="width:auto;padding:15px 20px">VENDER</button></div>`).join('');}
async function vender(id){let qtd=prompt("Quantidade:","1");if(!qtd)return;await fetch('/api/vender',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,qtd})});alert("Venda registrada!");pesquisar();minhas();}
async function minhas(){let r=await fetch('/api/minhas_vendas');let d=await r.json();document.getElementById('minhasVendas').innerHTML=d.map(v=>`${v[3]}x ${v[2]} = MZN ${v[4]} - ${v[5]}`).join('<br>')||'Nenhuma';} minhas();
</script></body></html>
"""

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['user']; s = request.form['senha']
        if u in USUARIOS and USUARIOS[u]['senha'] == s:
            session['user'] = u; session['papel'] = USUARIOS[u]['papel']; session['loja'] = USUARIOS[u]['loja']
            return redirect('/')
        return "Senha errada! <a href='/login'>Voltar</a>"
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

@app.route('/')
def index():
    if 'user' not in session: return redirect('/login')
    if session['papel'] == 'gerente':
        return render_template_string(GERENTE_HTML, user=session['user'])
    else:
        return render_template_string(OPERADOR_HTML, user=session['user'], loja=session['loja'])

@app.route('/api/categorias')
def cats():
    conn=sqlite3.connect('mzn_pos.db'); c=conn.cursor(); c.execute("SELECT * FROM categorias"); r=c.fetchall(); conn.close(); return jsonify(r)

@app.route('/api/produtos')
def get_prods():
    conn=sqlite3.connect('mzn_pos.db'); c=conn.cursor(); c.execute("SELECT * FROM produtos ORDER BY id DESC"); r=c.fetchall(); conn.close(); return jsonify(r)

@app.route('/api/search')
def search():
    q=request.args.get('q',''); conn=sqlite3.connect('mzn_pos.db'); c=conn.cursor()
    c.execute("SELECT * FROM produtos WHERE nome LIKE? OR categoria LIKE? OR codigo_barras LIKE?", (f'%{q}%',f'%{q}%',f'%{q}%')); r=c.fetchall(); conn.close(); return jsonify(r)

@app.route('/api/produtos', methods=['POST'])
def add_prod():
    if session.get('papel')!= 'gerente': return jsonify({"msg":"Sem permissão! Só gerente"}),403
    from werkzeug.utils import secure_filename
    nome=request.form['nome']; preco=float(request.form['preco']); stock=int(request.form['stock'])
    categoria=request.form['categoria']; codigo=request.form['codigo_barras']; loja=request.form['loja']
    file=request.files['imagem']; filename=secure_filename(str(uuid.uuid4())+"_"+file.filename)
    path=os.path.join(app.config['UPLOAD_FOLDER'], filename); file.save(path)
    conn=sqlite3.connect('mzn_pos.db'); c=conn.cursor()
    try:
        c.execute("INSERT INTO produtos (nome, preco, stock, categoria, codigo_barras, imagem, loja) VALUES (?,?,?,?,?,?,?)",(nome,preco,stock,categoria,codigo,path,loja))
        conn.commit(); msg="✅ Produto cadastrado!"
    except Exception as e: msg=f"Erro: {e}"
    conn.close(); return jsonify({"msg":msg})

@app.route('/api/vender', methods=['POST'])
def vender():
    if 'user' not in session: return jsonify({"msg":"login"}),401
    data=request.json; pid=data['id']; qtd=int(data['qtd'])
    conn=sqlite3.connect('mzn_pos.db'); c=conn.cursor(); c.execute("SELECT nome, preco, stock FROM produtos WHERE id=?",(pid,)); row=c.fetchone()
    if not row: return jsonify({"msg":"Produto não encontrado"}),404
    nome,preco,stock=row
    if stock<qtd: return jsonify({"msg":"Sem stock"}),400
    total=preco*qtd; hoje=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE produtos SET stock=stock-? WHERE id=?",(qtd,pid))
    c.execute("INSERT INTO vendas (produto_id, produto_nome, qtd, total, data, loja, vendedor) VALUES (?,?,?,?,?,?,?)",(pid,nome,qtd,total,hoje,session['loja'],session['user']))
    conn.commit(); conn.close(); return jsonify({"msg":"ok"})

@app.route('/api/relatorio_hoje')
def relatorio_hoje():
    if session.get('papel')!= 'gerente': return jsonify({"total":0,"qtd":0,"vendas":[]})
    hoje=datetime.now().strftime("%Y-%m-%d")
    conn=sqlite3.connect('mzn_pos.db'); c=conn.cursor()
    c.execute("SELECT * FROM vendas WHERE data LIKE?", (f'{hoje}%',)); vendas=c.fetchall()
    c.execute("SELECT SUM(total), COUNT(*) FROM vendas WHERE data LIKE?", (f'{hoje}%',)); total,qtd=c.fetchone()
    conn.close(); return jsonify({"vendas":vendas, "total":total or 0, "qtd":qtd or 0})

@app.route('/api/minhas_vendas')
def minhas_vendas():
    if 'user' not in session: return jsonify([])
    hoje=datetime.now().strftime("%Y-%m-%d")
    conn=sqlite3.connect('mzn_pos.db'); c=conn.cursor()
    c.execute("SELECT * FROM vendas WHERE vendedor=? AND data LIKE?", (session['user'], f'{hoje}%')); r=c.fetchall(); conn.close(); return jsonify(r)

if __name__ == "__main__":
    inicializar_banco_dados()
    gerar_buildozer_spec()
    em_android = 'ANDROID_ARGUMENT' in os.environ or hasattr(sys, 'getandroidsdk')
    if em_android:
        print("📱 MZN POS V3 Gerente/Operador no Android...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    elif len(sys.argv) > 1 and sys.argv[1] == '--server':
        print("\n🚀 [NUVEM] SaaS Moçambique porta 5000...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("\n💻 [DESKTOP TESTE] MZN POS V3")
        app.run(host='0.0.0.0', port=5000, debug=True)
