import sqlite3, os, base64, re
from flask import Flask, request, session, redirect, render_template_string, jsonify

app = Flask(__name__)
app.secret_key = "myblle-v8-final-fix"

def get_db(): return sqlite3.connect('myblle.db')

def init_db():
    conn=get_db(); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS lojas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, categoria_loja TEXT, dono TEXT, telefone TEXT, endereco TEXT, cidade TEXT, data TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, senha TEXT, nome TEXT, papel TEXT, loja_id INTEGER, telefone TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS produtos (id TEXT, loja_id INTEGER, nome TEXT, categoria TEXT, preco REAL, stock INTEGER, barras TEXT, codigo_barras TEXT, imagem TEXT, PRIMARY KEY(id, loja_id))")
    c.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, loja_id INTEGER, total REAL, recebido REAL, troco REAL, data TEXT, vendedor TEXT, papel TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS venda_itens (id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER, produto_id TEXT, qtd INTEGER, preco REAL)")
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0]==0:
        c.execute("INSERT INTO lojas (nome,categoria_loja,dono,telefone,endereco,cidade,data) VALUES ('Loja Demo Matola','Mercearia','Admin','820000000','Matola','Matola',datetime('now'))")
        loja_id=c.lastrowid
        c.execute("INSERT INTO usuarios VALUES ('admin','myblle123','Admin','gerente',?, '820000000')", (loja_id,))
        c.execute("INSERT INTO usuarios VALUES ('1001','1001','Gerente','gerente',?, '')", (loja_id,))
        c.execute("INSERT INTO usuarios VALUES ('1002','1002','Caixa','operador',?, '')", (loja_id,))
        c.execute("INSERT INTO produtos (id,loja_id,nome,categoria,preco,stock,barras,codigo_barras,imagem) VALUES ('ARROZ-10',?,'Arroz 10kg','Alimentação',1500,50,'ARROZ-10','10000001','')", (loja_id,))
    conn.commit(); conn.close()

init_db()

LOGIN_HTML = """<body style="font-family:Arial;background:#0a3d8f;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:15px"><div style="background:white;padding:25px;border-radius:16px;width:100%;max-width:380px"><h2 style="color:#0a3d8f;text-align:center">MyBlle</h2><form method="POST" action="/login"><input name="user" value="1001" required style="width:100%;padding:14px;border:1px solid #ddd;border-radius:8px"><input name="senha" type="password" value="1001" required style="width:100%;padding:14px;margin-top:10px;border:1px solid #ddd;border-radius:8px"><button style="width:100%;padding:14px;background:#0a3d8f;color:white;margin-top:12px;border:none;border-radius:8px;font-weight:bold">ENTRAR</button></form><a href="/cadastro-loja" style="display:block;text-align:center;margin-top:12px;background:#16a34a;color:white;padding:12px;border-radius:8px;text-decoration:none">+ CADASTRAR LOJA</a><p style="font-size:11px;text-align:center;color:#666;margin-top:10px">1001/1001 Gerente | 1002/1002 Caixa</p></div></body>"""

POS_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>MyBlle</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
.header{background:#0a3d8f;color:white;height:54px;display:flex;align-items:center;padding:0 12px;gap:8px}
.left{width:300px;background:white;border-right:1px solid #ddd;display:flex;flex-direction:column}
.main{flex:1;display:flex;height:calc(100vh - 85px)}
.produtos{flex:1;background:#f8fafc;display:flex;flex-direction:column}
.cats{background:#0a3d8f;display:flex;overflow-x:auto}
.cats button{background:transparent;color:white;border:none;padding:10px 14px;font-weight:bold;white-space:nowrap}
.cats button.active{background:white;color:#0a3d8f;border-radius:6px 6px 0 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;padding:12px;overflow-y:auto}
.card{border:1px solid #e2e8f0;padding:8px;border-radius:12px;text-align:center;font-size:11px;cursor:pointer;background:white;position:relative}
.card img{width:100%;height:80px;object-fit:cover;border-radius:8px;background:#f1f5f9}
.preco{color:#0a3d8f;font-weight:bold;font-size:13px}
.cart-item{display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #f1f5f9;font-size:13px}
.footer{background:#0a3d8f;color:white;padding:12px}
.btn{background:#0a3d8f;color:white;border:none;width:100%;padding:14px;font-size:18px;font-weight:bold;border-radius:10px}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);display:none;justify-content:center;align-items:center;z-index:100;padding:10px}
.modal-content{background:white;padding:20px;border-radius:16px;width:100%;max-width:460px;max-height:95vh;overflow-y:auto}
.num{width:100%;padding:14px;font-size:20px;text-align:center;border:2px solid #0a3d8f;border-radius:10px;margin:10px 0}
.teclado{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.teclado button{padding:14px;font-size:18px;border:1px solid #e2e8f0;background:white;border-radius:10px}
.menu{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.3);display:none;z-index:200}
.menu-box{background:white;width:90%;max-width:650px;height:100%;overflow-y:auto;padding:18px}
.input{width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;margin:6px 0}
.preview{width:100%;height:160px;border:2px dashed #0a3d8f;border-radius:12px;display:flex;align-items:center;justify-content:center;overflow:hidden;background:#f8fafc;cursor:pointer}
.preview img{width:100%;height:100%;object-fit:cover}
</style></head><body>
<div class="header">
<button onclick="document.getElementById('menu').style.display='flex'" style="background:transparent;border:none;color:white;font-size:22px">☰</button>
<div><b>{{loja_nome}}</b><div style="font-size:10px;opacity:.8">{{loja_cat}}</div></div>
<div style="margin-left:auto;font-size:11px;text-align:right">{{user}}<br>GERENTE</div>
<a href="/logout" style="color:white;margin-left:8px">Sair</a>
</div>

<div class="main">
<div class="left"><div style="padding:10px;font-weight:bold">Carrinho</div><div id="lista" style="flex:1;overflow-y:auto"></div><div class="footer"><div style="display:flex;justify-content:space-between;margin-bottom:6px"><span>Pagar</span><span id="total">MT 0.00</span></div><button class="btn" onclick="abrirPag()">PAGAR</button></div></div>
<div class="produtos"><div style="padding:10px;display:flex;gap:8px"><input id="busca" placeholder="📷 Código de barras / Nome" style="flex:1;padding:12px;border:1px solid #cbd5e1;border-radius:10px" oninput="render()"><button onclick="startScanner()" style="padding:10px 14px;background:#0a3d8f;color:white;border:none;border-radius:10px">📷</button></div><div class="cats" id="cats"></div><div class="grid" id="grid"></div></div></div>

<!-- NOVO PRODUTO COM IMAGEM + BARRA - CORRIGIDO -->
<div class="modal" id="modalProd"><div class="modal-content">
<h3 style="color:#0a3d8f">📦 Novo Produto com Foto</h3>
<form id="formProd" enctype="multipart/form-data">
<div class="preview" id="preview" onclick="document.getElementById('fileImg').click()"><span id="previewTxt">📷 Clique para tirar foto do produto<br><small>Ex: Copo de Sorvete</small></span><img id="previewImg" style="display:none"></div>
<input type="file" id="fileImg" name="imagem" accept="image/*" capture="environment" style="display:none" onchange="previewFile()">
<input name="id" required placeholder="Código curto (ex: COPO-SORV)" class="input" style="margin-top:10px">
<input name="nome" required placeholder="Nome (ex: Copo de Sorvete)" class="input">
<div style="display:flex;gap:8px"><input name="preco" type="number" step="0.01" required placeholder="Preço MT - só número ex: 150" class="input"><input name="stock" type="number" required placeholder="Stock ex: 100" class="input"></div>
<select name="categoria" class="input"><option>Mercearia</option><option>Casa</option><option>Cozinha</option><option>Alimentação</option><option>Outro</option></select>
<input name="codigo_barras" placeholder="Código de barras (ex: 123456789) - opcional" class="input">
<div style="display:flex;gap:10px;margin-top:12px"><button type="button" onclick="document.getElementById('modalProd').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button type="submit" style="flex:1;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px;font-weight:bold">Salvar</button></div>
</form>
</div></div>

<div class="modal" id="modalQtd"><div class="modal-content"><div id="qtdImg" style="text-align:center"></div><h3 id="mNome"></h3><p id="mPreco" style="color:#0a3d8f;font-weight:bold"></p><input class="num" id="inputQtd" type="number" value="1"><div class="teclado"><button onclick="add('1')">1</button><button onclick="add('2')">2</button><button onclick="add('3')">3</button><button onclick="add('4')">4</button><button onclick="add('5')">5</button><button onclick="add('6')">6</button><button onclick="add('7')">7</button><button onclick="add('8')">8</button><button onclick="add('9')">9</button><button onclick="add('00')">00</button><button onclick="add('0')">0</button><button onclick="document.getElementById('inputQtd').value=''">X</button></div><div style="display:flex;gap:10px;margin-top:10px"><button onclick="document.getElementById('modalQtd').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="conf()" style="flex:1;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Adicionar</button></div></div></div>

<div class="modal" id="modalPag"><div class="modal-content"><h3>Pagamento</h3><div style="background:#f8fafc;padding:12px;border-radius:10px;margin:10px 0"><div>Valor total: <b id="pagTotal">MT 0</b></div><div>Receber: <input id="pagRec" class="num" value="0" oninput="troco()"></div><div>Troco: <b id="pagTroco">MT 0</b></div></div><div class="teclado"><button onclick="addPag('50')">50</button><button onclick="addPag('100')">100</button><button onclick="addPag('200')">200</button><button onclick="addPag('500')">500</button><button onclick="addPag('1000')">1000</button><button onclick="addPag('10')">10</button></div><div style="display:flex;gap:10px;margin-top:10px"><button onclick="document.getElementById('modalPag').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="finalizar()" style="flex:1;padding:12px;background:#16a34a;color:white;border:none;border-radius:10px">Confirmar</button></div></div></div>

<div class="menu" id="menu" onclick="if(event.target==this) this.style.display='none'"><div class="menu-box">
<h3 style="color:#0a3d8f">Menu - {{loja_nome}}</h3>
<div style="border:2px solid #0a3d8f;background:#dbeafe;padding:14px;border-radius:12px;font-weight:bold;margin:15px 0" onclick="document.getElementById('modalProd').style.display='flex';document.getElementById('menu').style.display='none'">➕ Cadastrar Produto com Imagem e Código de Barras</div>
<div style="border:1px solid #e2e8f0;padding:12px;border-radius:12px" onclick="window.location='/api/relatorio'">📊 Relatório</div>
<button onclick="document.getElementById('menu').style.display='none'" style="margin-top:20px;width:100%;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Fechar</button>
</div></div>

<script>
let prods=[]; let car=[]; let sel=null; let cat='Todos';
async function load(){ prods=await (await fetch('/api/produtos')).json(); renderCats(); render(); }
function renderCats(){ let cats=['Todos',...new Set(prods.map(p=>p.categoria))]; document.getElementById('cats').innerHTML=cats.map(c=>`<button class="${c==cat?'active':''}" onclick="cat='${c}';render()">${c}</button>`).join(''); }
function render(){ let b=document.getElementById('busca').value.toLowerCase(); let f=prods.filter(p=>(cat=='Todos'||p.categoria==cat)&&(!b||p.nome.toLowerCase().includes(b)||p.id.toLowerCase().includes(b)||(p.codigo_barras&&p.codigo_barras.toLowerCase().includes(b)))); document.getElementById('grid').innerHTML=f.map(p=>`<div class="card" onclick="openQtd('${p.id}')">${p.imagem?`<img src="${p.imagem}">`:`<div style="height:80px;display:flex;align-items:center;justify-content:center;font-size:30px">📦</div>`}<b>${p.id}<br>${p.nome}</b><div class="preco">MT ${p.preco}</div><div style="font-size:9px;color:#64748b">${p.codigo_barras||''} | Stock:${p.stock}</div></div>`).join(''); }
function openQtd(id){ sel=prods.find(p=>p.id==id); document.getElementById('mNome').innerText=sel.nome; document.getElementById('mPreco').innerText='MT '+sel.preco; document.getElementById('qtdImg').innerHTML=sel.imagem?`<img src="${sel.imagem}" style="width:100px;height:100px;object-fit:cover;border-radius:12px">`:''; document.getElementById('inputQtd').value=1; document.getElementById('modalQtd').style.display='flex'; }
function add(n){ document.getElementById('inputQtd').value+=n; }
function conf(){ let q=parseInt(document.getElementById('inputQtd').value)||1; car.push({id:sel.id,nome:sel.nome,preco:sel.preco,qtd:q,imagem:sel.imagem}); draw(); document.getElementById('modalQtd').style.display='none'; }
function draw(){ let t=0; document.getElementById('lista').innerHTML=car.map(c=>{t+=c.preco*c.qtd; return `<div class="cart-item"><span>${c.id} x${c.qtd}</span><span>MT ${(c.preco*c.qtd).toFixed(2)}</span></div>`}).join(''); document.getElementById('total').innerText='MT '+t.toFixed(2); document.getElementById('pagTotal').innerText='MT '+t.toFixed(2); }
function abrirPag(){ if(car.length==0){alert('Carrinho vazio');return} document.getElementById('modalPag').style.display='flex'; document.getElementById('pagRec').value=document.getElementById('total').innerText.replace('MT',''); troco(); }
function troco(){ let tot=parseFloat(document.getElementById('pagTotal').innerText.replace('MT',''))||0; let rec=parseFloat(document.getElementById('pagRec').value)||0; document.getElementById('pagTroco').innerText='MT '+(rec-tot).toFixed(2); }
function addPag(v){ let a=parseFloat(document.getElementById('pagRec').value)||0; document.getElementById('pagRec').value=a+parseFloat(v); troco(); }
async function finalizar(){ let tot=parseFloat(document.getElementById('pagTotal').innerText.replace('MT','')); let rec=parseFloat(document.getElementById('pagRec').value)||0; await fetch('/api/vender',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({total:tot,recebido:rec,troco:rec-tot,itens:car})}); alert('Venda MT '+tot+' OK!'); car=[]; draw(); document.getElementById('modalPag').style.display='none'; }
function previewFile(){ let file=document.getElementById('fileImg').files[0]; if(file){ let r=new FileReader(); r.onload=function(e){ document.getElementById('previewImg').src=e.target.result; document.getElementById('previewImg').style.display='block'; document.getElementById('previewTxt').style.display='none'; }; r.readAsDataURL(file); } }
function startScanner(){ let c=prompt('Digite ou escaneie o código de barras:'); if(c){ document.getElementById('busca').value=c; render(); let f=prods.find(p=>p.codigo_barras==c||p.id==c); if(f) openQtd(f.id); } }
document.getElementById('formProd').addEventListener('submit', async function(e){
  e.preventDefault();
  let fd=new FormData(this);
  // Corrige preço se usuário digitar 150MNZ -> vira 150
  let precoStr=fd.get('preco');
  let precoLimpo=precoStr.replace(/[^0-9.]/g,'');
  fd.set('preco', precoLimpo);
  let res=await fetch('/api/produtos',{method:'POST',body:fd});
  if(res.ok){ alert('✅ Produto salvo com imagem!'); document.getElementById('modalProd').style.display='none'; this.reset(); document.getElementById('previewImg').style.display='none'; document.getElementById('previewTxt').style.display='block'; load(); }
  else { let err=await res.json(); alert(err.erro||'Erro'); }
});
load();
</script></body></html>
"""

@app.route("/")
def index():
    if "user" not in session: return redirect("/login")
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT loja_id FROM usuarios WHERE user=?", (session["user"],))
    r=c.fetchone()
    if not r: session.clear(); return redirect("/login")
    loja_id=r[0]
    c.execute("SELECT * FROM lojas WHERE id=?", (loja_id,))
    loja=c.fetchone()
    conn.close()
    return render_template_string(POS_HTML, loja_nome=loja[1], loja_cat=loja[2])

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="GET": return render_template_string(LOGIN_HTML)
    user=request.form.get("user"); senha=request.form.get("senha")
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT user,papel,loja_id FROM usuarios WHERE user=? AND senha=?", (user,senha))
    u=c.fetchone(); conn.close()
    if u: session["user"]=u[0]; session["papel"]=u[1]; session["loja_id"]=u[2]; return redirect("/")
    return "Login inválido <a href='/login'>Voltar</a>"

@app.route("/logout")
def logout(): session.clear(); return redirect("/login")

@app.route("/api/produtos", methods=["GET","POST"])
def produtos():
    if "loja_id" not in session: return jsonify([]),401
    loja_id=session["loja_id"]
    conn=get_db(); c=conn.cursor()
    if request.method=="POST":
        if session.get("papel")!="gerente": return jsonify({"erro":"Só Gerente! Faça login com 1001/1001"}),403
        pid=request.form.get("id") or request.form.get("codigo")
        nome=request.form.get("nome")
        categoria=request.form.get("categoria","Geral")
        preco=request.form.get("preco","0")
        stock=request.form.get("stock","0")
        codigo_barras=request.form.get("codigo_barras","")
        # Limpa preço: tira letras MT, MNZ, pcs
        preco=re.sub(r'[^0-9.]', '', preco) or '0'
        stock=re.sub(r'[^0-9]', '', stock) or '0'
        imagem_file=request.files.get("imagem")
        imagem_data=""
        if imagem_file and imagem_file.filename!="":
            data=imagem_file.read()
            b64=base64.b64encode(data).decode('utf-8')
            imagem_data=f"data:image/jpeg;base64,{b64}"
        else:
            # Mantém imagem antiga se existir
            c.execute("SELECT imagem FROM produtos WHERE id=? AND loja_id=?", (pid, loja_id))
            old=c.fetchone()
            if old: imagem_data=old[0] or ""
        c.execute("INSERT OR REPLACE INTO produtos (id,loja_id,nome,categoria,preco,stock,barras,codigo_barras,imagem) VALUES (?,?,?,?,?,?,?,?,?)",
                  (pid,loja_id,nome,categoria,float(preco),int(stock),codigo_barras,codigo_barras,imagem_data))
        conn.commit(); conn.close()
        return jsonify({"ok":True})
    c.execute("SELECT id,nome,categoria,preco,stock,barras,codigo_barras,imagem FROM produtos WHERE loja_id=?", (loja_id,))
    rows=c.fetchall(); conn.close()
    return jsonify([{"id":r[0],"nome":r[1],"categoria":r[2],"preco":r[3],"stock":r[4],"barras":r[5],"codigo_barras":r[6],"imagem":r[7]} for r in rows])

@app.route("/api/vender", methods=["POST"])
def vender():
    if "loja_id" not in session: return jsonify({"erro":"sem loja"}),401
    d=request.json; conn=get_db(); c=conn.cursor()
    c.execute("INSERT INTO vendas (loja_id,total,recebido,troco,data,vendedor,papel) VALUES (?,?,?,?,datetime('now','localtime'),?,?)", (session["loja_id"],d["total"],d.get("recebido",0),d.get("troco",0),session.get("user",""),session.get("papel","")))
    vid=c.lastrowid
    for it in d.get("itens",[]):
        c.execute("INSERT INTO venda_itens (venda_id,produto_id,qtd,preco) VALUES (?,?,?,?)", (vid,it["id"],it["qtd"],it["preco"]))
        c.execute("UPDATE produtos SET stock=stock-? WHERE id=? AND loja_id=?", (it["qtd"],it["id"],session["loja_id"]))
    conn.commit(); conn.close()
    return jsonify({"ok":True})

@app.route("/api/relatorio")
def relatorio():
    if "loja_id" not in session: return redirect("/login
