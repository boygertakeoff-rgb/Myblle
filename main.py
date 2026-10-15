import sqlite3
from flask import Flask, request, session, redirect, render_template_string, jsonify

app = Flask(__name__)
app.secret_key = "myblle-pospal-v4-final"

# USUARIOS COM PAPEL - Igual sua mensagem antiga + video
USUARIOS = {
    "1001": {"senha": "1001", "nome": "Gerente", "papel": "gerente", "loja": "Todas"},
    "1002": {"senha": "1002", "nome": "Caixa", "papel": "operador", "loja": "Matola"},
    "admin": {"senha": "myblle123", "nome": "Admin", "papel": "gerente", "loja": "Todas"},
    "gerente": {"senha": "gerente123", "papel": "gerente", "loja": "Matola"},
    "caixa": {"senha": "caixa123", "papel": "operador", "loja": "Matola"},
    "operador": {"senha": "op123", "papel": "operador", "loja": "Maputo"}
}

def get_db(): return sqlite3.connect('myblle.db')

def init_db():
    conn=get_db(); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS produtos (id TEXT PRIMARY KEY, nome TEXT, categoria TEXT, preco REAL, stock INTEGER, barras TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, total REAL, recebido REAL, troco REAL, data TEXT, vendedor TEXT, papel TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS venda_itens (id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER, produto_id TEXT, qtd INTEGER, preco REAL)")
    c.execute("SELECT COUNT(*) FROM produtos")
    if c.fetchone()[0]==0:
        for p in [("IP-33Copo","Copo com Cabo","Ferramentas",20,150),("IP-28Pano","Pano Fundo","Casa",15,80),("IP-13Balde","Balde","Casa",240,30),("ARROZ-10","Arroz 10kg","Alimentacao",1500,50),("FRANGO","Frango","Alimentacao",450,30),("MATAPA","Matapa","Alimentacao",300,40)]:
            c.execute("INSERT INTO produtos VALUES (?,?,?,?,?,?)", (p[0],p[1],p[2],p[3],p[4],p[0]))
    conn.commit(); conn.close()
init_db()

LOGIN = """
<body style="font-family:Arial;padding:30px;background:#0a3d8f;color:white;display:flex;justify-content:center;align-items:center;height:100vh;margin:0">
<div style="background:white;color:#111;padding:30px;border-radius:16px;width:100%;max-width:380px">
<h2 style="color:#0a3d8f">MyBlle - LOGIN</h2>
<form method="POST" action="/login">
<input name="user" placeholder="Usuário" value="1001" required style="width:100%;padding:14px;border:1px solid #ddd;border-radius:8px">
<input name="senha" type="password" placeholder="Senha" value="1001" required style="width:100%;padding:14px;margin-top:10px;border:1px solid #ddd;border-radius:8px">
<button style="width:100%;padding:14px;background:#0a3d8f;color:white;margin-top:10px;border:none;border-radius:8px;font-weight:bold">ENTRAR</button>
</form>
<p style="font-size:12px;margin-top:20px;color:#666;text-align:center">admin/myblle123 = Gerente vê tudo<br>caixa/caixa123 = Operador só vende<br>1001/1001 e 1002/1002 = igual máquina</p>
</div></body>
"""

POS = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
.header{background:#0a3d8f;color:white;height:50px;display:flex;align-items:center;padding:0 10px;gap:10px}
.left{width:300px;background:white;border-right:1px solid #ddd;display:flex;flex-direction:column}
.main{flex:1;display:flex;height:calc(100vh - 80px)}
.produtos{flex:1;background:#f8fafc;display:flex;flex-direction:column}
.cats{background:#0a3d8f;display:flex;overflow-x:auto}
.cats button{background:transparent;color:white;border:none;padding:10px 15px;font-weight:bold}
.cats button.active{background:white;color:#0a3d8f;border-radius:6px 6px 0 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;padding:10px;overflow-y:auto}
.card{border:1px solid #e2e8f0;padding:8px;border-radius:12px;text-align:center;font-size:12px;cursor:pointer;background:white}
.preco{color:#0a3d8f;font-weight:bold}
.cart-item{display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #eee;font-size:13px}
.footer{background:#0a3d8f;color:white;padding:10px}
.btn{background:#0a3d8f;color:white;border:none;width:100%;padding:14px;font-size:18px;font-weight:bold;border-radius:10px}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);display:none;justify-content:center;align-items:center;z-index:100}
.modal-content{background:white;padding:20px;border-radius:16px;width:90%;max-width:360px}
.num{width:100%;padding:12px;font-size:20px;text-align:center;border:2px solid #0a3d8f;border-radius:10px;margin:10px 0}
.teclado{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.teclado button{padding:15px;font-size:18px;border:1px solid #ddd;background:white;border-radius:10px}
.menu{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.3);display:none;z-index:200}
.menu-box{background:white;width:85%;max-width:600px;height:100%;overflow-y:auto;padding:15px}
.badge-gerente{background:#16a34a;color:white;padding:4px 8px;border-radius:20px;font-size:11px}
.badge-caixa{background:#38bdf8;color:#0a3d8f;padding:4px 8px;border-radius:20px;font-size:11px;font-weight:bold}
</style></head><body>
<div class="header">
<button onclick="document.getElementById('menu').style.display='flex'" style="background:transparent;border:none;color:white;font-size:20px">☰</button>
<span style="font-weight:bold">MyBlle</span>
<div style="margin-left:auto;display:flex;align-items:center;gap:8px">
{% if papel=='gerente' %}<span class="badge-gerente">GERENTE: {{user}}</span>{% else %}<span class="badge-caixa">CAIXA: {{user}} - {{loja}}</span>{% endif %}
<a href="/logout" style="color:white">Sair</a>
</div>
</div>

<div style="padding:8px;background:{% if papel=='gerente' %}#dcfce7;color:#166534{% else %}#dbeafe;color:#0a3d8f{% endif %};font-size:12px;font-weight:bold">
{% if papel=='gerente' %}✅ Você é GERENTE - pode: vender, cadastrar produto, ver relatório total, ver stock
{% else %}🔵 Você é OPERADOR - só pode vender e ver suas vendas. NÃO pode cadastrar nem ver relatório total
{% endif %}
</div>

<div class="main">
<div class="left"><div style="padding:10px;font-weight:bold">Carrinho - {{loja}}</div><div id="lista" style="flex:1;overflow-y:auto"></div>
<div class="footer"><div style="display:flex;justify-content:space-between"><span>Pagar</span><span id="total">MT 0.00</span></div><button class="btn" onclick="abrirPag()">PAGAR</button></div></div>
<div class="produtos"><div style="padding:8px"><input id="busca" placeholder="Codigo de Barras / Nome" style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:10px" oninput="render()"></div>
<div class="cats" id="cats"></div><div class="grid" id="grid"></div></div></div>

<div class="modal" id="modalQtd"><div class="modal-content">
<h3 id="mNome"></h3><p id="mPreco" style="color:#0a3d8f;font-weight:bold"></p>
<label>Quantidade</label><input class="num" id="inputQtd" type="number" value="1">
<div class="teclado"><button onclick="add('1')">1</button><button onclick="add('2')">2</button><button onclick="add('3')">3</button><button onclick="add('4')">4</button><button onclick="add('5')">5</button><button onclick="add('6')">6</button><button onclick="add('7')">7</button><button onclick="add('8')">8</button><button onclick="add('9')">9</button><button onclick="add('00')">00</button><button onclick="add('0')">0</button><button onclick="document.getElementById('inputQtd').value=''">X</button></div>
<div style="display:flex;gap:10px;margin-top:10px"><button onclick="document.getElementById('modalQtd').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="conf()" style="flex:1;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Confirmar</button></div></div></div>

<div class="modal" id="modalPag"><div class="modal-content">
<h3 style="color:#0a3d8f">Pagamento MyBlle</h3>
<div style="background:#f8fafc;padding:12px;border-radius:12px"><div>Valor total: <b id="pagTotal">MT 0</b></div><div>Receber: <input id="pagRec" class="num" value="0" oninput="troco()"></div><div>Troco: <b id="pagTroco">MT 0</b></div></div>
<div class="teclado" style="margin-top:10px"><button onclick="addPag('50')">50</button><button onclick="addPag('100')">100</button><button onclick="addPag('200')">200</button><button onclick="addPag('500')">500</button><button onclick="addPag('1000')">1000</button><button onclick="addPag('10')">10</button></div>
<div style="display:flex;gap:10px;margin-top:10px"><button onclick="document.getElementById('modalPag').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="finalizar()" style="flex:1;padding:12px;background:#16a34a;color:white;border:none;border-radius:10px">Confirmar</button></div></div></div>

<div class="menu" id="menu" onclick="if(event.target==this) this.style.display='none'"><div class="menu-box">
<h3 style="color:#0a3d8f">Menu MyBlle - {{user}} ({{papel}})</h3>
<h4 style="margin:15px 0 8px">Pagar</h4><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px">
<div style="border:1px solid #e2e8f0;padding:12px;border-radius:12px" onclick="alert('Recibo')">📄 Recibo</div>
<div style="border:1px solid #0a3d8f;background:#dbeafe;padding:12px;border-radius:12px" onclick="window.location='/api/relatorio'">📊 Relatório</div>
</div>
<h4 style="margin:15px 0 8px">Produto</h4><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px">
{% if papel=='gerente' %}
<div style="border:2px solid #16a34a;background:#dcfce7;padding:12px;border-radius:12px;font-weight:bold" onclick="novo()">➕ Cadastrar Produto (Só Gerente)</div>
{% else %}
<div style="border:1px solid #cbd5e1;background:#f1f5f9;color:#94a3b8;padding:12px;border-radius:12px">🔒 Cadastrar (Bloqueado)</div>
{% endif %}
<div style="border:1px solid #e2e8f0;padding:12px;border-radius:12px">📋 Lista</div>
</div>
<button onclick="document.getElementById('menu').style.display='none'" style="margin-top:15px;width:100%;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Fechar</button>
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
function novo(){ let id=prompt('Codigo:'); if(!id) return; let nome=prompt('Nome:'); let preco=prompt('Preço MT:'); let stock=prompt('Stock:'); let cat=prompt('Categoria:')||'Geral'; fetch('/api/produtos',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,nome,preco,stock,categoria:cat})}).then(r=>{if(!r.ok) alert('⛔ Só Gerente pode cadastrar!'); else load();}); }
load();
</script></body></html>
"""

@app.route("/")
def index():
    if "user" not in session: return redirect("/login")
    u=USUARIOS.get(session["user"],{})
    return render_template_string(POS, user=session["user"], papel=u.get("papel",""), loja=u.get("loja",""))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="GET": return render_template_string(LOGIN)
    u=request.form.get("user"); s=request.form.get("senha")
    usr=USUARIOS.get(u)
    if usr and usr["senha"]==s:
        session["user"]=u; session["papel"]=usr["papel"]; session["loja"]=usr.get("loja","")
        return redirect("/")
    return "Login inválido! <a href='/login'>Voltar</a>"

@app.route("/logout")
def logout(): session.clear(); return redirect("/login")

@app.route("/api/produtos", methods=["GET","POST"])
def prod():
    conn=get_db(); c=conn.cursor()
    if request.method=="POST":
        if session.get("papel")!="gerente": return jsonify({"erro":"Só gerente"}),403
        d=request.json
        c.execute("INSERT OR REPLACE INTO produtos VALUES (?,?,?,?,?,?)", (d["id"],d["nome"],d.get("categoria","Geral"),float(d["preco"]),int(d["stock"]),d["id"]))
        conn.commit(); conn.close(); return jsonify({"ok":True})
    c.execute("SELECT id,nome,categoria,preco,stock,barras FROM produtos")
    rows=c.fetchall(); conn.close()
    return jsonify([{"id":r[0],"nome":r[1],"categoria":r[2],"preco":r[3],"stock":r[4]} for r in rows])

@app.route("/api/vender", methods=["POST"])
def vender():
    d=request.json; conn=get_db(); c=conn.cursor()
    c.execute("INSERT INTO vendas (total,recebido,troco,data,vendedor,papel) VALUES (?,?,?,?,datetime('now','localtime'),?)", (d["total"],d.get("recebido",0),d.get("troco",0),session.get("user",""),session.get("papel","")))
    vid=c.lastrowid
    for it in d.get("itens",[]):
        c.execute("INSERT INTO venda_itens (venda_id,produto_id,qtd,preco) VALUES (?,?,?,?)", (vid,it["id"],it["qtd"],it["preco"]))
        c.execute("UPDATE produtos SET stock=stock-? WHERE id=?", (it["qtd"],it["id"]))
    conn.commit(); conn.close(); return jsonify({"ok":True})

@app.route("/api/relatorio")
def rel():
    if session.get("papel")!="gerente": return "⛔ ACESSO NEGADO - Só Gerente pode ver relatório total.<br><a href='/'>Voltar</a>", 403
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT id,total,data,vendedor,papel FROM vendas ORDER BY id DESC LIMIT 100")
    v=c.fetchall(); c.execute("SELECT SUM(total),COUNT(*) FROM vendas WHERE date(data)=date('now','localtime')"); hoje=c.fetchone(); conn.close()
    h=f"<body style='font-family:Arial;padding:15px'><h2 style='color:#0a3d8f'>📊 MyBlle - Relatório Gerente</h2><p>Hoje: {hoje[1] or 0} vendas, Total MT {(hoje[0] or 0):.2f}</p><table border=1 cellpadding=8 style='border-collapse:collapse;width:100%'><tr style='background:#0a3d8f;color:white'><th>ID</th><th>Total</th><th>Vendedor</th><th>Papel</th><th>Data</th></tr>"
    for x in v: h+=f"<tr><td>{x[0]}</td><td>MT {x[1]}</td><td>{x[3]}</td><td>{x[4]}</td><td>{x[2]}</td></tr>"
    h+="</table><br><a href='/' style='background:#0a3d8f;color:white;padding:10px 20px;border-radius:8px;text-decoration:none'>Voltar ao POS</a></body>"; return h

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
