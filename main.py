import sqlite3
from flask import Flask, request, session, redirect, render_template_string, jsonify

app = Flask(__name__)
app.secret_key = "myblle-pospal-2026"

USUARIOS = {
    "1001": {"senha": "1001", "nome": "Gerente", "papel": "gerente"},
    "1002": {"senha": "1002", "nome": "Caixa", "papel": "operador"},
    "admin": {"senha": "myblle123", "nome": "Admin", "papel": "gerente"},
    "caixa": {"senha": "caixa123", "nome": "Caixa", "papel": "operador"},
}

def get_db():
    return sqlite3.connect('myblle.db')

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS produtos (id TEXT PRIMARY KEY, nome TEXT, categoria TEXT, preco REAL, stock INTEGER, barras TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, total REAL, recebido REAL, troco REAL, data TEXT, vendedor TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS venda_itens (id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER, produto_id TEXT, qtd INTEGER, preco REAL)")
    c.execute("SELECT COUNT(*) FROM produtos")
    if c.fetchone()[0]==0:
        lista = [
            ("IP-33Copo","Copo com Cabo","Ferramentas",20,150),
            ("IP-28Pano","Pano de Fundo","Casa",15,80),
            ("IP-19Peq","Pequeno","Casa",15,60),
            ("IP-37Tigela","Tigela 6.7-14.7","Cozinha",20,100),
            ("IP-16Bacia","Bacia de Agua","Casa",85,40),
            ("IP-13Balde","Balde Pequeno","Casa",240,30),
            ("IP-27Chaleira","Chaleira Plastica","Cozinha",45,25),
            ("IP-32Copo","Copo de Agua KF","Cozinha",15,200),
            ("IP-01Armario","Armario 3 portas","Moveis",2100,5),
            ("ARROZ-10","Arroz 10kg","Alimentacao",1500,50),
            ("FRANGO","Frango","Alimentacao",450,30),
            ("MATAPA","Matapa kg","Alimentacao",300,40),
        ]
        for p in lista:
            c.execute("INSERT INTO produtos VALUES (?,?,?,?,?,?)", (p[0],p[1],p[2],p[3],p[4],p[0]))
    conn.commit()
    conn.close()
init_db()

LOGIN = '''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{margin:0;background:#f0f2f5;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial}
.box{background:white;width:380px;padding:30px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,.1)}
.logo{color:#ff5722;font-weight:bold;font-size:22px;text-align:center;margin-bottom:20px}
input{width:100%;padding:14px;margin:10px 0;border:1px solid #ddd;border-radius:6px;box-sizing:border-box}
button{width:100%;padding:14px;background:#ff5722;color:white;border:none;border-radius:6px;font-weight:bold}</style></head><body>
<div class="box"><div class="logo">POSPAL - MyBlle</div>
<form method="POST" action="/login">
<label>No de trabalho</label><input name="user" value="1001" required>
<label>Senha</label><input name="senha" type="password" value="1001" required>
<button>LOGIN</button></form>
<p style="font-size:12px;color:#666;text-align:center">1001/1001 Gerente | 1002/1002 Caixa</p></div></body></html>'''

POS = '''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
.header{background:#ff5722;color:white;height:45px;display:flex;align-items:center;padding:0 10px;gap:10px}
.left{width:280px;background:white;border-right:1px solid #ddd;display:flex;flex-direction:column}
.main{flex:1;display:flex;height:calc(100vh - 45px)}
.produtos{flex:1;background:white;display:flex;flex-direction:column}
.cats{background:#ff5722;display:flex;overflow-x:auto}
.cats button{background:transparent;color:white;border:none;padding:10px 15px;white-space:nowrap}
.cats button.active{background:white;color:#ff5722}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;padding:10px;overflow-y:auto}
.card{border:1px solid #eee;padding:8px;border-radius:4px;text-align:center;font-size:12px;cursor:pointer}
.preco{color:#ff5722;font-weight:bold}
.cart-item{display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #eee;font-size:13px}
.footer{background:#ff5722;color:white;padding:10px}
.btn{background:#ff5722;color:white;border:none;width:100%;padding:14px;font-size:18px;font-weight:bold;border-radius:4px}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);display:none;justify-content:center;align-items:center;z-index:100}
.modal-content{background:white;padding:20px;border-radius:8px;width:90%;max-width:360px}
.num{width:100%;padding:12px;font-size:20px;text-align:center;border:2px solid #ff5722;border-radius:6px;margin:10px 0}
.teclado{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.teclado button{padding:15px;font-size:18px;border:1px solid #ddd;background:white;border-radius:6px}
.menu{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.3);display:none;z-index:200}
.menu-box{background:white;width:85%;max-width:600px;height:100%;overflow-y:auto;padding:15px}
.menu-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.menu-item{text-align:center;padding:10px;border:1px solid #eee;border-radius:8px;font-size:11px}
@media(max-width:700px){.main{flex-direction:column}.left{width:100%;height:220px}.grid{grid-template-columns:repeat(3,1fr)}}
</style></head><body>
<div class="header">
<button onclick="document.getElementById('menu').style.display='flex'" style="background:transparent;border:none;color:white;font-size:20px">☰</button>
<span>Selecionar VIP</span><span style="margin-left:auto">{{user}} - {{papel}}</span>
<a href="/logout" style="color:white;text-decoration:none;margin-left:10px">Sair</a>
</div>
<div class="main">
<div class="left"><div style="padding:10px;font-weight:bold">Carrinho</div><div id="lista" style="flex:1;overflow-y:auto"></div>
<div class="footer"><div style="display:flex;justify-content:space-between"><span>Pagar</span><span id="total">R$ 0.00</span></div><button class="btn" onclick="abrirPag()">PAGAR</button></div></div>
<div class="produtos"><div style="padding:8px"><input id="busca" placeholder="Codigo/Nome do Produto" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px" oninput="render()"></div>
<div class="cats" id="cats"></div><div class="grid" id="grid"></div></div></div>

<div class="modal" id="modalQtd"><div class="modal-content">
<h3 id="mNome"></h3><p id="mPreco" style="color:#ff5722;font-weight:bold"></p>
<label>Quantidade</label><input class="num" id="inputQtd" type="number" value="1">
<div class="teclado">
<button onclick="add('1')">1</button><button onclick="add('2')">2</button><button onclick="add('3')">3</button>
<button onclick="add('4')">4</button><button onclick="add('5')">5</button><button onclick="add('6')">6</button>
<button onclick="add('7')">7</button><button onclick="add('8')">8</button><button onclick="add('9')">9</button>
<button onclick="add('00')">00</button><button onclick="add('0')">0</button><button onclick="document.getElementById('inputQtd').value=''">X</button>
</div>
<div style="display:flex;gap:10px;margin-top:10px">
<button onclick="document.getElementById('modalQtd').style.display='none'" style="flex:1;padding:12px;background:#ccc;border:none;border-radius:6px">Cancelar</button>
<button onclick="conf()" style="flex:1;padding:12px;background:#ff5722;color:white;border:none;border-radius:6px">Confirmar</button>
</div></div></div>

<div class="modal" id="modalPag"><div class="modal-content">
<h3>Pagamento</h3>
<div style="background:#f9f9f9;padding:10px;border-radius:6px">
<div>Valor total: <b id="pagTotal">R$0</b></div>
<div>Receber: <input id="pagRec" class="num" value="0" oninput="troco()"></div>
<div>Troco: <b id="pagTroco">R$0</b></div>
</div>
<div class="teclado" style="margin-top:10px">
<button onclick="addPag('50')">50</button><button onclick="addPag('100')">100</button><button onclick="addPag('200')">200</button>
<button onclick="addPag('10')">10</button><button onclick="addPag('20')">20</button><button onclick="addPag('5')">5</button>
</div>
<div style="display:flex;gap:10px;margin-top:10px">
<button onclick="document.getElementById('modalPag').style.display='none'" style="flex:1;padding:12px;background:#ccc;border:none;border-radius:6px">Cancelar</button>
<button onclick="finalizar()" style="flex:1;padding:12px;background:#4caf50;color:white;border:none;border-radius:6px">Confirmar</button>
</div></div></div>

<div class="menu" id="menu" onclick="if(event.target==this) this.style.display='none'"><div class="menu-box">
<h3>Menu <button onclick="document.getElementById('menu').style.display='none'" style="float:right">X</button></h3>
<h4 style="margin:15px 0 8px">Produto</h4>
<div class="menu-grid">
<div class="menu-item" onclick="novo()">+ Produto</div>
<div class="menu-item" onclick="window.location='/api/relatorio'">Relatorio</div>
<div class="menu-item">Ver Stock</div>
<div class="menu-item" onclick="window.print()">Imprimir</div>
</div></div></div>

<script>
let prods=[]; let car=[]; let sel=null; let cat='Todos';
async function load(){ prods=await (await fetch('/api/produtos')).json(); renderCats(); render(); }
function renderCats(){ let cats=['Todos',...new Set(prods.map(p=>p.categoria))]; document.getElementById('cats').innerHTML=cats.map(c=>`<button class="${c==cat?'active':''}" onclick="cat='${c}';render()">${c}</button>`).join(''); }
function render(){ let b=document.getElementById('busca').value.toLowerCase(); let f=prods.filter(p=>(cat=='Todos'||p.categoria==cat)&&(!b||p.nome.toLowerCase().includes(b)||p.id.toLowerCase().includes(b))); document.getElementById('grid').innerHTML=f.map(p=>`<div class="card" onclick="openQtd('${p.id}')"><div>📦</div><b>${p.id}<br>${p.nome}</b><div class="preco">R$${p.preco}</div><div style="font-size:10px">Stock:${p.stock}</div></div>`).join(''); }
function openQtd(id){ sel=prods.find(p=>p.id==id); document.getElementById('mNome').innerText=sel.id+' '+sel.nome; document.getElementById('mPreco').innerText='R$'+sel.preco; document.getElementById('inputQtd').value=1; document.getElementById('modalQtd').style.display='flex'; }
function add(n){ document.getElementById('inputQtd').value+=n; }
function conf(){ let q=parseInt(document.getElementById('inputQtd').value)||1; car.push({id:sel.id,nome:sel.nome,preco:sel.preco,qtd:q}); draw(); document.getElementById('modalQtd').style.display='none'; }
function draw(){ let t=0; document.getElementById('lista').innerHTML=car.map(c=>{t+=c.preco*c.qtd; return `<div class="cart-item"><span>${c.id} x${c.qtd}</span><span>R$${(c.preco*c.qtd).toFixed(2)}</span></div>`}).join(''); document.getElementById('total').innerText='R$'+t.toFixed(2); document.getElementById('pagTotal').innerText='R$'+t.toFixed(2); }
function abrirPag(){ if(car.length==0){alert('Carrinho vazio');return} document.getElementById('modalPag').style.display='flex'; document.getElementById('pagRec').value=document.getElementById('total').innerText.replace('R$',''); troco(); }
function troco(){ let tot=parseFloat(document.getElementById('pagTotal').innerText.replace('R$',''))||0; let rec=parseFloat(document.getElementById('pagRec').value)||0; document.getElementById('pagTroco').innerText='R$'+(rec-tot).toFixed(2); }
function addPag(v){ let a=parseFloat(document.getElementById('pagRec').value)||0; document.getElementById('pagRec').value=a+parseFloat(v); troco(); }
async function finalizar(){ let tot=parseFloat(document.getElementById('pagTotal').innerText.replace('R$','')); let rec=parseFloat(document.getElementById('pagRec').value)||0; await fetch('/api/vender',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({total:tot,recebido:rec,troco:rec-tot,itens:car})}); alert('Venda R$'+tot+' OK!'); car=[]; draw(); document.getElementById('modalPag').style.display='none'; }
function novo(){ let id=prompt('Codigo:'); if(!id) return; let nome=prompt('Nome:'); let preco=prompt('Preco:'); let stock=prompt('Stock:'); let cat=prompt('Categoria:')||'Geral'; fetch('/api/produtos',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,nome,preco,stock,categoria:cat})}).then(()=>load()); }
load();
</script></body></html>'''

@app.route("/")
def index():
    if "user" not in session:
        return render_template_string(LOGIN)
    u = USUARIOS.get(session["user"],{})
    return render_template_string(POS, user=session["user"], papel=u.get("papel",""))

@app.route("/login", methods=["POST"])
def login():
    u=request.form.get("user"); s=request.form.get("senha")
    usr=USUARIOS.get(u)
    if usr and usr["senha"]==s:
        session["user"]=u; session["papel"]=usr["papel"]; return redirect("/")
    return "Senha errada <a href='/'>voltar</a>"

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

@app.route("/api/produtos", methods=["GET","POST"])
def prod():
    conn=get_db(); c=conn.cursor()
    if request.method=="POST":
        if session.get("papel")!="gerente": return jsonify({"erro":"so gerente"}),403
        d=request.json
        c.execute("INSERT OR REPLACE INTO produtos VALUES (?,?,?,?,?,?)", (d["id"],d["nome"],d.get("categoria","Geral"),float(d["preco"]),int(d["stock"]),d["id"]))
        conn.commit(); conn.close(); return jsonify({"ok":True})
    c.execute("SELECT id,nome,categoria,preco,stock,barras FROM produtos")
    rows=c.fetchall(); conn.close()
    return jsonify([{"id":r[0],"nome":r[1],"categoria":r[2],"preco":r[3],"stock":r[4],"barras":r[5]} for r in rows])

@app.route("/api/vender", methods=["POST"])
def vender():
    d=request.json; conn=get_db(); c=conn.cursor()
    c.execute("INSERT INTO vendas (total,recebido,troco,data,vendedor) VALUES (?,?,?,?,datetime('now','localtime'))", (d["total"],d.get("recebido",0),d.get("troco",0),session.get("user","")))
    vid=c.lastrowid
    for it in d.get("itens",[]):
        c.execute("INSERT INTO venda_itens (venda_id,produto_id,qtd,preco) VALUES (?,?,?,?)", (vid,it["id"],it["qtd"],it["preco"]))
        c.execute("UPDATE produtos SET stock=stock-? WHERE id=?", (it["qtd"],it["id"]))
    conn.commit(); conn.close(); return jsonify({"ok":True})

@app.route("/api/relatorio")
def rel():
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT id,total,data,vendedor FROM vendas ORDER BY id DESC LIMIT 50")
    v=c.fetchall(); conn.close()
    h="<h2>Relatorio</h2><table border=1 cellpadding=5><tr><th>ID</th><th>Total</th><th>Data</th><th>Vendedor</th></tr>"
    for x in v: h+=f"<tr><td>{x[0]}</td><td>{x[1]}</td><td>{x[2]}</td><td>{x[3]}</td></tr>"
    h+="</table><a href='/'>Voltar</a>"; return h

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
