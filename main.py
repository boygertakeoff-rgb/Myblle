import sqlite3
from flask import Flask, request, session, redirect, render_template_string, jsonify

app = Flask(__name__)
app.secret_key = "myblle-v6-lojas"

def get_db(): return sqlite3.connect('myblle.db')

def init_db():
    conn=get_db(); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS lojas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, categoria_loja TEXT, dono TEXT, telefone TEXT, endereco TEXT, cidade TEXT, data TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, senha TEXT, nome TEXT, papel TEXT, loja_id INTEGER, telefone TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS produtos (id TEXT, loja_id INTEGER, nome TEXT, categoria TEXT, preco REAL, stock INTEGER, barras TEXT, PRIMARY KEY(id, loja_id))")
    c.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, loja_id INTEGER, total REAL, recebido REAL, troco REAL, data TEXT, vendedor TEXT, papel TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS venda_itens (id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER, produto_id TEXT, qtd INTEGER, preco REAL)")
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0]==0:
        # Admin master
        c.execute("INSERT INTO lojas (nome,categoria_loja,dono,telefone,endereco,cidade,data) VALUES ('Loja Demo Matola','Mercearia','Admin','820000000','Matola','Matola',datetime('now'))")
        loja_id=c.lastrowid
        c.execute("INSERT INTO usuarios VALUES ('admin','myblle123','Admin Master','gerente',?, '820000000')", (loja_id,))
        c.execute("INSERT INTO usuarios VALUES ('1001','1001','Gerente Matola','gerente',?, '820000001')", (loja_id,))
        c.execute("INSERT INTO usuarios VALUES ('1002','1002','Caixa Matola','operador',?, '820000002')", (loja_id,))
        c.execute("INSERT INTO produtos VALUES ('ARROZ-10',?,'Arroz 10kg','Alimentacao',1500,50,'ARROZ-10')", (loja_id,))
        c.execute("INSERT INTO produtos VALUES ('FRANGO',?,'Frango','Alimentacao',450,30,'FRANGO')", (loja_id,))
    conn.commit(); conn.close()
init_db()

CATEGORIAS_LOJA = ["Mercearia / Minimercado","Boutique / Roupas","Farmácia","Restaurante / Bar / Takeaway","Material de Construção / Ferragem","Electrónica / Celulares","Cosméticos / Salão","Padaria / Pastelaria","Talhao / Agronegócio","Lojinha Geral","Outra"]

LOGIN_HTML = """
<body style="font-family:Arial;background:#0a3d8f;margin:0;padding:20px;display:flex;justify-content:center;align-items:center;min-height:100vh">
<div style="background:white;padding:25px;border-radius:16px;width:100%;max-width:400px">
<h2 style="color:#0a3d8f;text-align:center">MyBlle - LOGIN</h2>
<form method="POST" action="/login">
<input name="user" placeholder="Usuário (ex: 1001)" required style="width:100%;padding:14px;border:1px solid #ddd;border-radius:8px">
<input name="senha" type="password" placeholder="Senha" required style="width:100%;padding:14px;margin-top:10px;border:1px solid #ddd;border-radius:8px">
<button style="width:100%;padding:14px;background:#0a3d8f;color:white;margin-top:12px;border:none;border-radius:8px;font-weight:bold">ENTRAR</button>
</form>
<div style="margin-top:15px;text-align:center">
<a href="/cadastro-loja" style="display:block;padding:12px;background:#16a34a;color:white;border-radius:8px;text-decoration:none;font-weight:bold">+ CADASTRAR MINHA LOJA</a>
<p style="font-size:11px;color:#666;margin-top:10px">Demo: admin/myblle123<br>1001/1001 Gerente | 1002/1002 Caixa</p>
</div>
</div></body>
"""

CADASTRO_LOJA_HTML = """
<body style="font-family:Arial;background:#f1f5f9;margin:0;padding:15px">
<div style="background:white;padding:20px;border-radius:16px;max-width:500px;margin:0 auto">
<h2 style="color:#0a3d8f">🏪 Cadastrar Minha Loja</h2>
<form method="POST" action="/cadastro-loja">
<label>Nome da Loja *</label><input name="nome_loja" required placeholder="Ex: MyBlle Matola" style="width:100%;padding:12px;margin:5px 0 10px;border:1px solid #ddd;border-radius:8px">
<label>Categoria da Loja *</label>
<select name="categoria_loja" required style="width:100%;padding:12px;margin:5px 0 10px;border:1px solid #ddd;border-radius:8px">
<option value="">Escolha a categoria</option>
{% for cat in cats %}<option value="{{cat}}">{{cat}}</option>{% endfor %}
</select>
<label>Nome do Dono / Gerente *</label><input name="dono" required placeholder="Seu nome" style="width:100%;padding:12px;margin:5px 0 10px;border:1px solid #ddd;border-radius:8px">
<label>Telefone / WhatsApp *</label><input name="telefone" required placeholder="82..." style="width:100%;padding:12px;margin:5px 0 10px;border:1px solid #ddd;border-radius:8px">
<label>Cidade / Bairro *</label><input name="cidade" required placeholder="Ex: Nampula - Muahivire" style="width:100%;padding:12px;margin:5px 0 10px;border:1px solid #ddd;border-radius:8px">
<label>Endereço</label><input name="endereco" placeholder="Rua, número" style="width:100%;padding:12px;margin:5px 0 10px;border:1px solid #ddd;border-radius:8px">
<hr style="margin:15px 0">
<h3 style="color:#0a3d8f">🔐 Criar seu usuário Gerente</h3>
<label>Usuário para login *</label><input name="user" required placeholder="Ex: gerente_nampula" style="width:100%;padding:12px;margin:5px 0 10px;border:1px solid #ddd;border-radius:8px">
<label>Senha *</label><input name="senha" type="password" required placeholder="Crie uma senha" style="width:100%;padding:12px;margin:5px 0 10px;border:1px solid #ddd;border-radius:8px">
<button style="width:100%;padding:14px;background:#0a3d8f;color:white;border:none;border-radius:10px;font-weight:bold;margin-top:10px">CADASTRAR LOJA E ENTRAR</button>
</form>
<a href="/login" style="display:block;text-align:center;margin-top:15px;color:#0a3d8f">Já tenho conta - Fazer Login</a>
</div></body>
"""

POS_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>MyBlle</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
.header{background:#0a3d8f;color:white;height:54px;display:flex;align-items:center;padding:0 12px;gap:10px}
.left{width:300px;background:white;border-right:1px solid #ddd;display:flex;flex-direction:column}
.main{flex:1;display:flex;height:calc(100vh - 85px)}
.produtos{flex:1;background:#f8fafc;display:flex;flex-direction:column}
.cats{background:#0a3d8f;display:flex;overflow-x:auto}
.cats button{background:transparent;color:white;border:none;padding:10px 14px;font-weight:bold;white-space:nowrap}
.cats button.active{background:white;color:#0a3d8f;border-radius:6px 6px 0 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;padding:12px;overflow-y:auto}
.card{border:1px solid #e2e8f0;padding:10px;border-radius:12px;text-align:center;font-size:12px;cursor:pointer;background:white}
.preco{color:#0a3d8f;font-weight:bold}
.cart-item{display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #f1f5f9;font-size:13px}
.footer{background:#0a3d8f;color:white;padding:12px}
.btn{background:#0a3d8f;color:white;border:none;width:100%;padding:14px;font-size:18px;font-weight:bold;border-radius:10px}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);display:none;justify-content:center;align-items:center;z-index:100}
.modal-content{background:white;padding:20px;border-radius:16px;width:90%;max-width:420px;max-height:90vh;overflow-y:auto}
.num{width:100%;padding:14px;font-size:20px;text-align:center;border:2px solid #0a3d8f;border-radius:10px;margin:10px 0}
.teclado{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.teclado button{padding:16px;font-size:18px;border:1px solid #e2e8f0;background:white;border-radius:10px}
.menu{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.3);display:none;z-index:200}
.menu-box{background:white;width:90%;max-width:650px;height:100%;overflow-y:auto;padding:18px}
.input{width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;margin:6px 0}
</style></head><body>
<div class="header">
<button onclick="document.getElementById('menu').style.display='flex'" style="background:transparent;border:none;color:white;font-size:22px">☰</button>
<div><b style="font-size:16px">{{loja_nome}}</b><div style="font-size:10px;opacity:.8">{{loja_cat}} - {{loja_cidade}}</div></div>
<div style="margin-left:auto;text-align:right"><div style="font-size:12px">{% if papel=='gerente' %}GERENTE{% else %}CAIXA{% endif %}: {{user}}</div><div style="font-size:10px">Loja ID: {{loja_id}}</div></div>
<a href="/logout" style="color:white;margin-left:10px">Sair</a>
</div>
<div style="padding:8px;font-size:11px;font-weight:bold;background:{% if papel=='gerente' %}#dcfce7;color:#166534{% else %}#dbeafe;color:#0a3d8f{% endif %}">
{% if papel=='gerente' %}✅ GERENTE - Pode cadastrar caixas, produtos e ver relatório{% else %}🔵 CAIXA da loja {{loja_nome}} - Só vende{% endif %}
</div>
<div class="main">
<div class="left"><div style="padding:10px;font-weight:bold">Carrinho</div><div id="lista" style="flex:1;overflow-y:auto"></div>
<div class="footer"><div style="display:flex;justify-content:space-between;margin-bottom:6px"><span>Pagar</span><span id="total">MT 0.00</span></div><button class="btn" onclick="abrirPag()">PAGAR</button></div></div>
<div class="produtos"><div style="padding:10px"><input id="busca" placeholder="Código de Barras / Nome" style="width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:10px" oninput="render()"></div>
<div class="cats" id="cats"></div><div class="grid" id="grid"></div></div></div>

<!-- Modal Qtd -->
<div class="modal" id="modalQtd"><div class="modal-content"><h3 id="mNome"></h3><p id="mPreco" style="color:#0a3d8f;font-weight:bold"></p><input class="num" id="inputQtd" type="number" value="1"><div class="teclado"><button onclick="add('1')">1</button><button onclick="add('2')">2</button><button onclick="add('3')">3</button><button onclick="add('4')">4</button><button onclick="add('5')">5</button><button onclick="add('6')">6</button><button onclick="add('7')">7</button><button onclick="add('8')">8</button><button onclick="add('9')">9</button><button onclick="add('00')">00</button><button onclick="add('0')">0</button><button onclick="document.getElementById('inputQtd').value=''">X</button></div><div style="display:flex;gap:10px;margin-top:10px"><button onclick="document.getElementById('modalQtd').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="conf()" style="flex:1;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Confirmar</button></div></div></div>

<!-- Modal Pag -->
<div class="modal" id="modalPag"><div class="modal-content"><h3 style="color:#0a3d8f">Pagamento</h3><div style="background:#f8fafc;padding:12px;border-radius:10px;margin:10px 0"><div>Valor total: <b id="pagTotal">MT 0</b></div><div>Receber: <input id="pagRec" class="num" value="0" oninput="troco()"></div><div>Troco: <b id="pagTroco">MT 0</b></div></div><div class="teclado"><button onclick="addPag('50')">50</button><button onclick="addPag('100')">100</button><button onclick="addPag('200')">200</button><button onclick="addPag('500')">500</button><button onclick="addPag('1000')">1000</button><button onclick="addPag('10')">10</button></div><div style="display:flex;gap:10px;margin-top:10px"><button onclick="document.getElementById('modalPag').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="finalizar()" style="flex:1;padding:12px;background:#16a34a;color:white;border:none;border-radius:10px">Confirmar</button></div></div></div>

<!-- Modal Cadastro Caixa -->
<div class="modal" id="modalCaixa"><div class="modal-content">
<h3 style="color:#0a3d8f">👤 Cadastrar Caixa da Loja {{loja_nome}}</h3>
<input id="c_user" class="input" placeholder="Usuário do caixa (ex: caixa1)">
<input id="c_nome" class="input" placeholder="Nome completo do caixa">
<input id="c_senha" class="input" type="password" placeholder="Senha">
<input id="c_tel" class="input" placeholder="Telefone">
<div style="display:flex;gap:10px;margin-top:10px"><button onclick="document.getElementById('modalCaixa').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="salvarCaixa()" style="flex:1;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Salvar Caixa</button></div>
<div id="listaCaixas" style="margin-top:15px"></div>
</div></div>

<!-- MENU -->
<div class="menu" id="menu" onclick="if(event.target==this) this.style.display='none'"><div class="menu-box">
<h3 style="color:#0a3d8f">Menu - {{loja_nome}}</h3><p style="font-size:11px;color:#666">{{loja_cat}} - {{loja_cidade}} | {{user}} ({{papel}})</p>

<h4 style="margin:15px 0 8px;color:#0a3d8f">🏪 Minha Loja</h4>
<div style="background:#f8fafc;padding:12px;border-radius:12px;font-size:13px">
<b>{{loja_nome}}</b><br>Categoria: {{loja_cat}}<br>Dono: {{loja_dono}}<br>Tel: {{loja_tel}}<br>Cidade: {{loja_cidade}}
</div>

<h4 style="margin:15px 0 8px;color:#0a3d8f">Pagar</h4>
<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px">
<div style="border:1px solid #e2e8f0;padding:12px;border-radius:12px" onclick="alert('Recibo em breve')">📄 Recibo</div>
<div style="border:2px solid #0a3d8f;background:#dbeafe;padding:12px;border-radius:12px" onclick="window.location='/api/relatorio'">📊 Relatório {% if papel!='gerente' %}(Bloq){% endif %}</div>
</div>

<h4 style="margin:15px 0 8px;color:#0a3d8f">👥 Equipe</h4>
<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px">
{% if papel=='gerente' %}
<div style="border:2px solid #16a34a;background:#dcfce7;padding:12px;border-radius:12px;font-weight:bold" onclick="abrirCadastroCaixa()">➕ Cadastrar Caixa (Gerente)</div>
<div style="border:1px solid #e2e8f0;padding:12px;border-radius:12px" onclick="abrirCadastroCaixa()">👀 Ver Caixas</div>
{% else %}
<div style="border:1px solid #cbd5e1;background:#f1f5f9;color:#94a3b8;padding:12px;border-radius:12px">🔒 Cadastrar Caixa (Só Gerente)</div>
{% endif %}
</div>

<h4 style="margin:15px 0 8px;color:#0a3d8f">📦 Produtos</h4>
<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px">
{% if papel=='gerente' %}
<div style="border:2px solid #16a34a;background:#dcfce7;padding:12px;border-radius:12px;font-weight:bold" onclick="novo()">➕ Cadastrar Produto</div>
{% else %}
<div style="border:1px solid #cbd5e1;background:#f1f5f9;color:#94a3b8;padding:12px;border-radius:12px">🔒 Cadastrar Produto</div>
{% endif %}
<div style="border:1px solid #e2e8f0;padding:12px;border-radius:12px" onclick="window.open('/api/produtos','_blank')">📋 Lista</div>
</div>
<button onclick="document.getElementById('menu').style.display='none'" style="margin-top:20px;width:100%;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Fechar</button>
</div></div>

<script>
let prods=[]; let car=[]; let sel=null; let cat='Todos';
async function load(){ prods=await (await fetch('/api/produtos')).json(); renderCats(); render(); }
function renderCats(){ let cats=['Todos',...new Set(prods.map(p=>p.categoria))]; document.getElementById('cats').innerHTML=cats.map(c=>`<button class="${c==cat?'active':''}" onclick="cat='${c}';render()">${c}</button>`).join(''); }
function render(){ let b=document.getElementById('busca').value.toLowerCase(); let f=prods.filter(p=>(cat=='Todos'||p.categoria==cat)&&(!b||p.nome.toLowerCase().includes(b)||p.id.toLowerCase().includes(b))); document.getElementById('grid').innerHTML=f.map(p=>`<div class="card" onclick="openQtd('${p.id}')"><div style="font-size:24px">📦</div><b>${p.id}<br>${p.nome}</b><div class="preco">MT ${p.preco}</div><div style="font-size:10px;color:#64748b">Stock:${p.stock}</div></div>`).join(''); }
function openQtd(id){ sel=prods.find(p=>p.id==id); document.getElementById('mNome').innerText=sel.id+' '+sel.nome; document.getElementById('mPreco').innerText='MT '+sel.preco; document.getElementById('inputQtd').value=1; document.getElementById('modalQtd').style.display='flex'; }
function add(n){ document.getElementById('inputQtd').value+=n; }
function conf(){ let q=parseInt(document.getElementById('inputQtd').value)||1; car.push({id:sel.id,nome:sel.nome,preco:sel.preco,qtd:q}); draw(); document.getElementById('modalQtd').style.display='none'; }
function draw(){ let t=0; document.getElementById('lista').innerHTML=car.map(c=>{t+=c.preco*c.qtd; return `<div class="cart-item"><span>${c.id} x${c.qtd}</span><span>MT ${(c.preco*c.qtd).toFixed(2)}</span></div>`}).join(''); document.getElementById('total').innerText='MT '+t.toFixed(2); document.getElementById('pagTotal').innerText='MT '+t.toFixed(2); }
function abrirPag(){ if(car.length==0){alert('Carrinho vazio');return} document.getElementById('modalPag').style.display='flex'; document.getElementById('pagRec').value=document.getElementById('total').innerText.replace('MT',''); troco(); }
function troco(){ let tot=parseFloat(document.getElementById('pagTotal').innerText.replace('MT',''))||0; let rec=parseFloat(document.getElementById('pagRec').value)||0; document.getElementById('pagTroco').innerText='MT '+(rec-tot).toFixed(2); }
function addPag(v){ let a=parseFloat(document.getElementById('pagRec').value)||0; document.getElementById('pagRec').value=a+parseFloat(v); troco(); }
async function finalizar(){ let tot=parseFloat(document.getElementById('pagTotal').innerText.replace('MT','')); let rec=parseFloat(document.getElementById('pagRec').value)||0; await fetch('/api/vender',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({total:tot,recebido:rec,troco:rec-tot,itens:car})}); alert('Venda MT '+tot+' OK!'); car=[]; draw(); document.getElementById('modalPag').style.display='none'; }
function novo(){ let id=prompt('Codigo:'); if(!id) return; let nome=prompt('Nome:'); let preco=prompt('Preço MT:'); let stock=prompt('Stock:'); let cat=prompt('Categoria:')||'Geral'; fetch('/api/produtos',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,nome,preco,stock,categoria:cat})}).then(r=>{if(!r.ok) alert('⛔ Só Gerente!'); else load();}); }
async function abrirCadastroCaixa(){ document.getElementById('modalCaixa').style.display='flex'; let caixas=await (await fetch('/api/caixas')).json(); document.getElementById('listaCaixas').innerHTML='<h4>Caixas da loja:</h4>'+caixas.map(c=>`<div style="padding:8px;border-bottom:1px solid #eee;display:flex;justify-content:space-between"><span>${c.user} - ${c.nome} (${c.papel})</span><span>${c.telefone||''}</span></div>`).join(''); }
async function salvarCaixa(){ let user=document.getElementById('c_user').value; let nome=document.getElementById('c_nome').value; let senha=document.getElementById('c_senha').value; let tel=document.getElementById('c_tel').value; if(!user||!senha) return alert('Preencha usuário e senha'); let r=await fetch('/api/caixas',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user,senha,nome,telefone:tel,papel:'operador'})}); if(r.ok){ alert('Caixa cadastrado!'); abrirCadastroCaixa(); } else { let e=await r.json(); alert(e.erro||'Erro'); } }
load();
</script></body></html>
"""

@app.route("/")
def index():
    if "user" not in session: return redirect("/login")
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT loja_id FROM usuarios WHERE user=?", (session["user"],))
    row=c.fetchone()
    if not row:
        session.clear()
        return redirect("/login")
    loja_id=row[0]
    c.execute("SELECT * FROM lojas WHERE id=?", (loja_id,))
    loja=c.fetchone()
    conn.close()
    if not loja: return "Loja não encontrada"
    return render_template_string(POS_HTML, user=session["user"], papel=session["papel"], loja_id=loja[0], loja_nome=loja[1], loja_cat=loja[2], loja_dono=loja[3], loja_tel=loja[4], loja_cidade=loja[6])

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="GET": return render_template_string(LOGIN_HTML)
    user=request.form.get("user"); senha=request.form.get("senha")
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT user,papel,loja_id FROM usuarios WHERE user=? AND senha=?", (user,senha))
    u=c.fetchone()
    conn.close()
    if u:
        session["user"]=u[0]; session["papel"]=u[1]; session["loja_id"]=u[2]
        return redirect("/")
    return "Login inválido! <a href='/login'>Voltar</a>"

@app.route("/cadastro-loja", methods=["GET","POST"])
def cadastro_loja():
    if request.method=="GET":
        return render_template_string(CADASTRO_LOJA_HTML, cats=CATEGORIAS_LOJA)
    nome=request.form.get("nome_loja"); cat=request.form.get("categoria_loja"); dono=request.form.get("dono"); tel=request.form.get("telefone"); cidade=request.form.get("cidade"); endereco=request.form.get("endereco"); user=request.form.get("user"); senha=request.form.get("senha")
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT user FROM usuarios WHERE user=?", (user,))
    if c.fetchone():
        conn.close()
        return f"Usuário {user} já existe! <a href='/cadastro-loja'>Voltar</a>"
    c.execute("INSERT INTO lojas (nome,categoria_loja,dono,telefone,endereco,cidade,data) VALUES (?,?,?,?,?,?,datetime('now'))", (nome,cat,dono,tel,endereco,cidade))
    loja_id=c.lastrowid
    c.execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?)", (user,senha,dono,"gerente",loja_id,tel))
    # produtos iniciais por categoria
    if "Construção" in cat or "Ferragem" in cat:
        c.execute("INSERT INTO produtos VALUES ('CIMENTO',?,'Cimento 50kg','Construção',1500,20,'CIMENTO')", (loja_id,))
    else:
        c.execute("INSERT INTO produtos VALUES ('ARROZ-10',?,'Arroz 10kg','Alimentação',1500,20,'ARROZ-10')", (loja_id,))
        c.execute("INSERT INTO produtos VALUES ('OLEO',?,'Óleo 1L','Alimentação',250,30,'OLEO')", (loja_id,))
    conn.commit(); conn.close()
    session["user"]=user; session["papel"]="gerente"; session["loja_id"]=loja_id
    return redirect("/")

@app.route("/logout")
def logout(): session.clear(); return redirect("/login")

@app.route("/api/produtos", methods=["GET","POST"])
def produtos():
    if "loja_id" not in session: return jsonify([]),401
    loja_id=session["loja_id"]
    conn=get_db(); c=conn.cursor()
    if request.method=="POST":
        if session.get("papel")!="gerente": return jsonify({"erro":"Só gerente"}),403
        d=request.json
        c.execute("INSERT OR REPLACE INTO produtos VALUES (?,?,?,?,?,?)", (d["id"],loja_id,d["nome"],d.get("categoria","Geral"),float(d["preco"]),int(d["stock"]),d["id"]))
        conn.commit(); conn.close(); return jsonify({"ok":True})
    c.execute("SELECT id,nome,categoria,preco,stock,barras FROM produtos WHERE loja_id=?", (loja_id,))
    rows=c.fetchall(); conn.close()
    return jsonify([{"id":r[0],"nome":r[1],"categoria":r[2],"preco":r[3],"stock":r[4],"barras":r[5]} for r in rows])

@app.route("/api/caixas", methods=["GET","POST"])
def caixas():
    if "loja_id" not in session: return jsonify([]),401
    loja_id=session["loja_id"]
    if session.get("papel")!="gerente": return jsonify({"erro":"Só gerente pode gerir caixas"}),403
    conn=get_db(); c=conn.cursor()
    if request.method=="POST":
        d=request.json
        c.execute("SELECT user FROM usuarios WHERE user=?", (d["user"],))
        if c.fetchone():
            conn.close()
            return jsonify({"erro":"Usuário já existe"}),400
        c.execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?)", (d["user"],d["senha"],d.get("nome",d["user"]),d.get("papel","operador"),loja_id,d.get("telefone","")))
        conn.commit(); conn.close()
        return jsonify({"ok":True})
    c.execute("SELECT user,nome,papel,telefone FROM usuarios WHERE loja_id=?", (loja_id,))
    rows=c.fetchall(); conn.close()
    return jsonify([{"user":r[0],"nome":r[1],"papel":r[2],"telefone":r[3]} for r in rows])

@app.route("/api/vender", methods=["POST"])
def vender():
    if "loja_id" not in session: return jsonify({"erro":"sem loja"}),401
    d=request.json; conn=get_db(); c=conn.cursor()
    c.execute("INSERT INTO vendas (loja_id,total,recebido,troco,data,vendedor,papel) VALUES (?,?,?,?,datetime('now','localtime'),?,?)", (session["loja_id"],d["total"],d.get("recebido",0),d.get("troco",0),session.get("user",""),session.get("papel","")))
    vid=c.lastrowid
    for it in d.get("itens",[]):
        c.execute("INSERT INTO venda_itens (venda_id,produto_id,qtd,preco) VALUES (?,?,?,?)", (vid,it["id"],it["qtd"],it["preco"]))
        c.execute("UPDATE produtos SET stock=stock-? WHERE id=? AND loja_id=?", (it["qtd"],it["id"],session["loja_id"]))
    conn.commit(); conn.close(); return jsonify({"ok":True})

@app.route("/api/relatorio")
def relatorio():
    if "loja_id" not in session: return redirect("/login")
    if session.get("papel")!="gerente": return "⛔ ACESSO NEGADO - Só Gerente vê relatório total da loja.<br><a href='/'>Voltar</a>", 403
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT id,total,data,vendedor,papel FROM vendas WHERE loja_id=? ORDER BY id DESC LIMIT 100", (session["loja_id"],))
    v=c.fetchall()
    c.execute("SELECT SUM(total),COUNT(*) FROM vendas WHERE loja_id=? AND date(data)=date('now','localtime')", (session["loja_id"],))
    hoje=c.fetchone()
    c.execute("SELECT nome,categoria_loja FROM lojas WHERE id=?", (session["loja_id"],))
    loja=c.fetchone()
    conn.close()
    h=f"<body style='font-family:Arial;padding:15px'><h2 style='color:#0a3d8f'>📊 {loja[0]} - Relatório ({loja[1]})</h2><p>Hoje: {hoje[1] or 0} vendas, Total MT {(hoje[0] or 0):.2f}</p><table border=1 cellpadding=8 style='border-collapse:collapse;width:100%'><tr style='background:#0a3d8f;color:white'><th>ID</th><th>Total</th><th>Vendedor</th><th>Papel</th><th>Data</th></tr>"
    for x in v: h+=f"<tr><td>{x[0]}</td><td>MT {x[1]}</td><td>{x[3]}</td><td>{x[4]}</td><td>{x[2]}</td></tr>"
    h+="</table><br><a href='/' style='background:#0a3d8f;color:white;padding:10px 20px;border-radius:8px;text-decoration:none'>Voltar</a></body>"; return h

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
