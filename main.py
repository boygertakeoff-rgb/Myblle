import os, sys, sqlite3, base64, uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/produtos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def inicializar_banco_dados():
    conn = sqlite3.connect('mzn_pos.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY, nome TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produtos
        (id INTEGER PRIMARY KEY, nome TEXT, preco REAL, stock INTEGER,
         categoria TEXT, codigo_barras TEXT UNIQUE, imagem TEXT, loja TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS vendas
        (id INTEGER PRIMARY KEY, produto_id INTEGER, qtd INTEGER, total REAL, data TEXT, loja TEXT)''')

    # Categorias padrão
    for cat in ["Polos", "Camisas", "T-Shirts", "Calças", "Acessórios"]:
        try: c.execute("INSERT INTO categorias (nome) VALUES (?)", (cat,))
        except: pass
    conn.commit()
    conn.close()

def gerar_buildozer_spec():
    return True # já está no projeto

# === API E TELAS ===
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MZN POS - myblle</title>
<style>
body{font-family:Arial;padding:10px;background:#f4f4f4}
.card{background:white;padding:15px;border-radius:12px;margin-bottom:10px;box-shadow:0 2px 5px #0001}
input,select,button{width:100%;padding:12px;margin:5px 0;border-radius:8px;border:1px solid #ccc}
button{background:#1a8a1a;color:white;font-weight:bold;border:none}
.prod{display:flex;gap:10px;align-items:center}
.prod img{width:60px;height:60px;object-fit:cover;border-radius:8px}
.top{display:flex;justify-content:space-between}
.badge{background:#eee;padding:3px 8px;border-radius:10px;font-size:12px}
</style>
</head>
<body>
<h2>📱 MZN POS - Matola</h2>

<div class="card" style="background:#0a5c0a;color:white">
  <div class="top"><span>Vendas HOJE</span><span id="hora"></span></div>
  <h1 id="totalDia">MZN 0.00</h1>
  <div id="qtdDia">0 vendas hoje</div>
</div>

<div class="card">
  <h3>🔍 Pesquisar Produto</h3>
  <input id="busca" placeholder="Nome, categoria ou código de barras..." onkeyup="pesquisar()">
  <div id="listaProdutos"></div>
</div>

<div class="card">
  <h3>➕ Cadastrar Produto</h3>
  <form id="formProd" enctype="multipart/form-data">
    <input name="nome" placeholder="Nome do produto" required>
    <input name="preco" type="number" step="0.01" placeholder="Preço MZN" required>
    <input name="stock" type="number" placeholder="Stock" required>
    <select name="categoria" id="selCat"></select>
    <input name="codigo_barras" placeholder="Código de barras (ex: 123456789)" required>
    <select name="loja"><option>Matola</option><option>Maputo</option><option>Porto</option></select>
    <label>Imagem do Produto:</label>
    <input name="imagem" type="file" accept="image/*" required>
    <button type="submit">SALVAR PRODUTO</button>
  </form>
</div>

<div class="card">
  <h3>📊 Relatório em Tempo Real</h3>
  <button onclick="relatorio()">Atualizar Relatório de Hoje</button>
  <div id="relatorio"></div>
</div>

<script>
async function carregar(){
  let res = await fetch('/api/produtos'); let prods = await res.json();
  document.getElementById('listaProdutos').innerHTML = prods.map(p=>`
    <div class="prod card"><img src="/${p[6] || 'static/produtos/no.png'}"><div><b>${p[1]}</b><br>${p[4]} | ${p[5]}<br>MZN ${p[2]} - Stock: ${p[3]}</div>
    <button onclick="vender(${p[0]})" style="width:auto">VENDER</button></div>`).join('');

  let res2 = await fetch('/api/categorias'); let cats = await res2.json();
  document.getElementById('selCat').innerHTML = cats.map(c=>`<option>${c[1]}</option>`).join('');

  relatorio();
  setInterval(()=>{ document.getElementById('hora').innerText = new Date().toLocaleTimeString(); },1000);
}
async function pesquisar(){
  let q = document.getElementById('busca').value;
  let res = await fetch('/api/search?q='+q); let prods = await res.json();
  document.getElementById('listaProdutos').innerHTML = prods.map(p=>`
    <div class="prod card"><img src="/${p[6]}"><div><b>${p[1]}</b><br>${p[4]} | ${p[5]}<br>MZN ${p[2]}</div></div>`).join('');
}
async function relatorio(){
  let res = await fetch('/api/relatorio_hoje'); let d = await res.json();
  document.getElementById('totalDia').innerText = 'MZN ' + d.total.toFixed(2);
  document.getElementById('qtdDia').innerText = d.qtd + ' vendas hoje';
  document.getElementById('relatorio').innerHTML = d.vendas.map(v=>`#${v[0]} - ${v[2]}x - MZN ${v[3]} - ${v[4]}`).join('<br>');
}
async function vender(id){
  let qtd = prompt("Quantidade:","1"); if(!qtd) return;
  await fetch('/api/vender',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id, qtd})});
  alert("Venda feita!"); relatorio(); carregar();
}
document.getElementById('formProd').onsubmit = async (e)=>{
  e.preventDefault(); let fd = new FormData(e.target);
  let res = await fetch('/api/produtos',{method:'POST',body:fd}); let j = await res.json();
  alert(j.msg); e.target.reset(); carregar();
}
carregar();
</script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/api/categorias')
def cats():
    conn = sqlite3.connect('mzn_pos.db'); c = conn.cursor()
    c.execute("SELECT * FROM categorias"); r=c.fetchall(); conn.close(); return jsonify(r)

@app.route('/api/produtos')
def get_prods():
    conn = sqlite3.connect('mzn_pos.db'); c = conn.cursor()
    c.execute("SELECT * FROM produtos ORDER BY id DESC"); r=c.fetchall(); conn.close(); return jsonify(r)

@app.route('/api/search')
def search():
    q = request.args.get('q','')
    conn = sqlite3.connect('mzn_pos.db'); c = conn.cursor()
    c.execute("SELECT * FROM produtos WHERE nome LIKE? OR categoria LIKE? OR codigo_barras LIKE?", (f'%{q}%',f'%{q}%',f'%{q}%'))
    r=c.fetchall(); conn.close(); return jsonify(r)

@app.route('/api/produtos', methods=['POST'])
def add_prod():
    nome = request.form['nome']; preco=float(request.form['preco']); stock=int(request.form['stock'])
    categoria=request.form['categoria']; codigo=request.form['codigo_barras']; loja=request.form['loja']
    file = request.files['imagem']
    filename = secure_filename(str(uuid.uuid4())+"_"+file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    conn = sqlite3.connect('mzn_pos.db'); c = conn.cursor()
    try:
        c.execute("INSERT INTO produtos (nome, preco, stock, categoria, codigo_barras, imagem, loja) VALUES (?,?,?,?,?,?,?)",
                  (nome, preco, stock, categoria, codigo, path, loja))
        conn.commit(); msg="Produto cadastrado!"
    except Exception as e: msg=f"Erro: {e} - Código de barras já existe?"
    conn.close(); return jsonify({"msg":msg})

@app.route('/api/vender', methods=['POST'])
def vender():
    data=request.json; pid=data['id']; qtd=int(data['qtd'])
    conn = sqlite3.connect('mzn_pos.db'); c = conn.cursor()
    c.execute("SELECT preco, stock FROM produtos WHERE id=?", (pid,)); preco, stock = c.fetchone()
    if stock < qtd: return jsonify({"msg":"Sem stock"}),400
    total=preco*qtd; hoje=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE produtos SET stock=stock-? WHERE id=?", (qtd, pid))
    c.execute("INSERT INTO vendas (produto_id, qtd, total, data, loja) VALUES (?,?,?,?,?)",(pid,qtd,total,hoje,"Matola"))
    conn.commit(); conn.close(); return jsonify({"msg":"ok"})

@app.route('/api/relatorio_hoje')
def relatorio_hoje():
    hoje = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('mzn_pos.db'); c = conn.cursor()
    c.execute("SELECT * FROM vendas WHERE data LIKE?", (f'{hoje}%',)); vendas=c.fetchall()
    c.execute("SELECT SUM(total), COUNT(*) FROM vendas WHERE data LIKE?", (f'{hoje}%',)); total,qtd=c.fetchone()
    conn.close(); return jsonify({"vendas":vendas, "total":total or 0, "qtd":qtd or 0})

# === INICIO ===
if __name__ == "__main__":
    inicializar_banco_dados()
    gerar_buildozer_spec()

    em_android = 'ANDROID_ARGUMENT' in os.environ or hasattr(sys, 'getandroidsdk')

    if em_android:
        print("📱 A iniciar o MZN POS dentro do ambiente Nativo Android...")
        # No Android usa Flask dentro de WebView
        app.run(host='0.0.0.0', port=5000, debug=False)
    elif len(sys.argv) > 1 and sys.argv[1] == '--server':
        print("\n🚀 [NUVEM] Servidor SaaS Moçambique porta 5000...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("\n💻 [DESKTOP TESTE] Interface Web no PC...")
        app.run(host='0.0.0.0', port=5000, debug=True)
